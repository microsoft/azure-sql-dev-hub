"""Regression tests for the task-app verifier and HTTP response contract."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch

from hub_eval.command import CommandError
from hub_eval.scenarios import _load_module
from hub_eval.validation import http_json


verification = _load_module("javascript-app")


class HttpJsonTests(unittest.TestCase):
    def test_existing_callers_can_receive_created_status(self) -> None:
        response = Mock(status=201)
        response.read.return_value = b'{"id": 4}'
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with patch("urllib.request.urlopen", return_value=response):
            self.assertEqual(http_json("http://localhost/tasks"), (201, {"id": 4}))

    def test_expected_client_error_is_decoded_and_origin_is_sent(self) -> None:
        error = urllib.error.HTTPError(
            "http://localhost/tasks", 400, "Bad Request", {},
            io.BytesIO(b'{"error": "Invalid title"}'),
        )
        with patch("urllib.request.urlopen", side_effect=error) as opened:
            result = http_json(
                "http://localhost/tasks", method="POST", payload={"title": ""},
                headers={"Origin": "http://localhost"}, expected_status=400,
            )
        self.assertEqual(result, (400, {"error": "Invalid title"}))
        self.assertEqual(opened.call_args.args[0].get_header("Origin"), "http://localhost")

    def test_unexpected_error_is_not_treated_as_an_expected_client_error(self) -> None:
        error = urllib.error.HTTPError(
            "http://localhost/tasks", 500, "Internal Server Error", {},
            io.BytesIO(b'{"error": "Unavailable"}'),
        )
        with patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(CommandError, "returned 500"):
                http_json("http://localhost/tasks", expected_status=400)

    def test_success_cannot_satisfy_an_expected_rejection(self) -> None:
        response = Mock(status=200)
        response.read.return_value = b'{"id": 4}'
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with patch("urllib.request.urlopen", return_value=response):
            with self.assertRaisesRegex(CommandError, "expected 400"):
                http_json("http://localhost/tasks", expected_status=400)

    def test_non_json_success_is_reported_explicitly(self) -> None:
        response = Mock(status=200)
        response.read.return_value = b"<html>not an API</html>"
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with patch("urllib.request.urlopen", return_value=response):
            with self.assertRaisesRegex(CommandError, "did not return JSON"):
                http_json("http://localhost/tasks")


class TaskContractTests(unittest.TestCase):
    def test_client_error_requires_a_helpful_message(self) -> None:
        for body in ({}, {"error": ""}, {"error": 1}, []):
            with self.subTest(body=body):
                with patch.object(verification, "http_json", return_value=(400, body)):
                    with self.assertRaisesRegex(CommandError, "error string"):
                        verification.request("POST", expected_status=400)

    def test_fresh_read_must_match_independent_sql(self) -> None:
        probe = Mock()
        probe.query.return_value = [(4, "task", False)]
        with patch.object(
            verification, "request", return_value=[{"id": 4, "title": "task", "done": True}]
        ):
            with self.assertRaisesRegex(CommandError, "saved task state"):
                verification.assert_saved_task(probe, 4, "task", True)

    def test_numeric_status_is_not_a_json_boolean(self) -> None:
        with patch.object(
            verification, "request", return_value=[{"id": 4, "title": "task", "done": 0}]
        ):
            with self.assertRaisesRegex(CommandError, "saved task state"):
                verification.assert_saved_task(Mock(), 4, "task", False)


class TaskLifecycleTests(unittest.TestCase):
    def run_verifier(self, *, break_reopen: bool = False, change_on_rejection: bool = False):
        seeds = (
            "Plan a weekend trip",
            "Book a dentist appointment",
            "Pick up groceries",
        )
        tasks = {
            index: {"id": index, "title": title, "done": False}
            for index, title in enumerate(seeds, start=1)
        }
        probe = Mock()

        def query(statement, parameters=(), **kwargs):
            if "created_at" in statement:
                return [(key, row["title"], row["done"], "unchanged")
                        for key, row in sorted(tasks.items())]
            row = tasks.get(parameters[0])
            if "SELECT id FROM" in statement:
                return [(row["id"],)] if row else []
            return [(row["id"], row["title"], row["done"])] if row else []

        def execute(statement, parameters=(), **kwargs):
            self.assertEqual(statement, "DELETE FROM dbo.tasks WHERE id = ?")
            tasks.pop(parameters[0], None)

        probe.query.side_effect = query
        probe.execute.side_effect = execute
        reopened = False

        def request(method, path="/api/tasks", payload=None, *,
                    expected_status=200, origin=verification.ORIGIN):
            nonlocal reopened
            if expected_status >= 400:
                if change_on_rejection and method == "PATCH" and path == "/api/tasks/4":
                    tasks[4]["title"] = "unexpected change"
                return {"error": "Rejected request"}
            if method == "GET":
                return [dict(row) for row in tasks.values()]
            if method == "POST":
                tasks[4] = {"id": 4, "title": payload["title"].strip(), "done": False}
                return dict(tasks[4])
            task_id = int(path.rsplit("/", 1)[1])
            if method == "PATCH":
                if payload.get("done") is False:
                    reopened = True
                    if break_reopen:
                        return dict(tasks[task_id])
                tasks[task_id].update(payload)
                tasks[task_id]["title"] = tasks[task_id]["title"].strip()
                return dict(tasks[task_id])
            tasks.pop(task_id)
            return {"id": task_id}

        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "package.json").write_text(
                json.dumps({"dependencies": {"next": "test", "mssql": "test"}}),
                encoding="utf-8",
            )
            with (
                patch.object(verification, "CommandRunner") as runner,
                patch.object(verification, "ManagedProcess") as process,
                patch.object(verification, "DatabaseProbe", return_value=probe),
                patch.object(verification, "database_environment", return_value={}),
                patch.object(verification, "request", side_effect=request),
            ):
                process.return_value.__enter__.return_value.wait_for_http.return_value = (
                    "<h1>My Tasks</h1>"
                )
                try:
                    verification.validate(project, Mock(), project, 60, Mock())
                finally:
                    self.assertEqual(set(tasks), {1, 2, 3})
                    if probe.execute.called:
                        self.assertEqual(probe.execute.call_args.args[1], (4,))
                self.assertEqual(process.call_count, 2)
                scripts = [call.args[0] for call in runner.return_value.run.call_args_list]
                self.assertIn(["npm", "run", "test"], scripts)
                self.assertIn(["npm", "run", "build"], scripts)
                self.assertIn(["npx", "tsx", "scripts/init.ts"], scripts)
                for call in runner.return_value.run.call_args_list:
                    self.assertEqual(call.kwargs["env"]["APP_ORIGIN"], verification.ORIGIN)
                self.assertTrue(reopened)

    def test_full_lifecycle_restarts_app_and_preserves_existing_rows(self) -> None:
        self.run_verifier()

    def test_ignoring_done_false_fails_and_still_cleans_up(self) -> None:
        with self.assertRaisesRegex(CommandError, "saved task"):
            self.run_verifier(break_reopen=True)

    def test_rejected_patch_must_not_change_sql(self) -> None:
        with self.assertRaisesRegex(CommandError, "saved task"):
            self.run_verifier(change_on_rejection=True)


class FollowOnScenarioTests(unittest.TestCase):
    def test_tenant_verifier_does_not_collect_node_runner_tests_with_vitest(self) -> None:
        tenant = _load_module("multi-tenant")
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "package.json").write_text("{}", encoding="utf-8")
            with (
                patch.object(tenant, "CommandRunner") as runner,
                patch.object(tenant, "DatabaseProbe") as probe,
                patch.object(tenant, "database_environment", return_value={}),
            ):
                probe.return_value.query.return_value = [(1, 2)]
                tenant.validate(project, Mock(), project, 60, Mock())
                self.assertEqual(
                    runner.return_value.run.call_args.args[0],
                    ["npx", "vitest", "run", "tests/rls.test.ts"],
                )


if __name__ == "__main__":
    unittest.main()
