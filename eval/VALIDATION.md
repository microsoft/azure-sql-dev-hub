# Evaluation status

The harness implementation and live-run findings are recorded here.

## Criteria source

The attached `Hub-Prompt-Validation.docx` is Microsoft Office DRM-protected and
could not be opened by the available headless Word session. The criteria were
subsequently supplied as a table and have been implemented directly, with
additional compatible assertions from each prompt's validation section.

## Model smoke tests

GitHub Copilot CLI 1.0.85 successfully completed noninteractive smoke tests with:

- `gpt-5.4`
- `claude-sonnet-5`

## Live scenario results

### Latest scenario results

Run `20260924T003818Z-a580dbff` completed all six scenarios with `gpt-5.4`
and `claude-sonnet-5`. The evidence is under
`eval/runs/20260924T003818Z-a580dbff/`.
Run `20260924T015743Z-7129af63` successfully reran the Claude Python API
scenario and supersedes its transient invalid-JSONL failure from the full matrix.

| Scenario | Model | Result | Run ID |
|---|---|---|---|
| JavaScript app | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260924T003818Z-a580dbff` |
| JavaScript app | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260924T003818Z-a580dbff` |
| Python API | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260924T003818Z-a580dbff` |
| Python API | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260924T015743Z-7129af63` |
| RAG | `gpt-5.4` | ✅ PASS: provisioned Azure OpenAI and independent end-state validation passed. | `20260924T003818Z-a580dbff` |
| RAG | `claude-sonnet-5` | ✅ PASS: provisioned Azure OpenAI and independent end-state validation passed. | `20260924T003818Z-a580dbff` |
| Serverless API | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260924T003818Z-a580dbff` |
| Serverless API | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260924T003818Z-a580dbff` |
| Event-driven app | `gpt-5.4` | ❌ FAIL: the SQL trigger did not log the inserted task within five minutes. | `20260924T003818Z-a580dbff` |
| Event-driven app | `claude-sonnet-5` | ❌ FAIL: the SQL trigger did not log the inserted task within five minutes. | `20260924T003818Z-a580dbff` |
| Multi-tenant app | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260924T003818Z-a580dbff` |
| Multi-tenant app | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260924T003818Z-a580dbff` |

The latest totals are five passes and one failure for each model. Azure cleanup
completed without errors for the full matrix and targeted rerun.
