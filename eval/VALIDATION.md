# Evaluation status

## Task-app revision: container verified, cloud validation pending

On 2026-10-30, a disposable Next.js app was generated from
[the revised JavaScript task-app prompt](../build/javascript-app.md) and exercised
against the real Azure SQL Database container. Run: `20261030-container-72d42bc3`.
This validates the CRUD learning outcome locally, not the cloud identity path.

The test-owned engine used image digest
`sha256:de81a8941316d1ecde19c8126f9174281bf90c54a014c7c102493d6a9c7aeffd`.
Independent queries confirmed `EngineEdition = 5` and `Edition = SQL Azure`.
The app used a separate database and login with only table-level
SELECT/INSERT/UPDATE/DELETE permissions, not `sa`, `sysadmin`, `db_owner`, or
schema-creation privileges. The administrator pre-created the empty schema;
the generated initializer seeded it and a repeat initialization preserved rows.

The explicit local overrides were SQL authentication and trust of the
container's self-signed certificate, with encryption enabled. The cloud prompt
still uses Entra and certificate validation. All prompt package pins were
available without substitution: Next.js 16.3.4, mssql 12.7.2,
@azure/identity 4.13.3, @types/mssql 12.3.0, and tsx 4.23.13.

| Check | Result |
|---|---|
| Generated app unit/route tests | 29 passed, zero failed or skipped |
| Generated app production build | Passed |
| Generated app opt-in HTTP integration exercise | Passed |
| Published independent verifier | CRUD, fresh SQL reads, application restart, invalid requests, and preservation of existing rows passed |
| Additional black-box HTTP checks | 42 assertions passed, covering malformed bodies, id/title boundaries, origins, no-store responses, missing tasks, and SQL state |
| Real database failures | Denied SELECT and INSERT returned safe 500 errors; restoring permissions recovered reads and preserved rows |
| Browser task lifecycle | Keyboard create/edit, complete, reopen, cancel, confirmed delete, and persistence across reloads passed |
| Browser failure behavior | Real read/write failures showed errors; drafts survived failed writes; Retry recovered; concurrent deletion produced a 404 explanation and refreshed the list |
| Duplicate submission | Two rapid form submissions created exactly one row |
| Layout and status contrast | A 200-character title fit at 360 CSS pixels without horizontal overflow; wide layout passed; status contrast ratios were 9.44:1 and 7.51:1 |
| Other UI checks | HTML-looking titles rendered as text; simulated network loss guarded uncertain writes; a simulated empty API result showed the empty-state invitation |
| Cleanup | App servers stopped; owned container, database/login, and generated credential files removed; shared containers left unchanged |

The first real HTTP run found a defect that unit tests with synthetic request
URLs missed: Next.js normalized the internal request URL to `localhost` while
the browser and evaluator used `127.0.0.1`. Valid mutations were rejected with
403. The prompt and fixture now use a trusted, explicit `APP_ORIGIN` rather than
deriving it from the request URL or host/forwarded headers. The evaluator supplies
its own origin, and the fixture includes regression tests for normalized URLs
and missing/invalid configuration. The final unit/build/SQL/restart run passed
after that correction.

The generated fixture and raw local evidence are retained in the session
workspace, outside the site repository, without credential files. No cloud
resources were provisioned for this run.

The historical JavaScript passes below apply only to the earlier read-only
prompt. Keep `validated: false` until the revised prompt passes a fresh cloud
run using Entra authentication and the cloud certificate configuration. Do not
treat this container run as that cloud validation or as authorization to retire
the older Todo repository.

## Harness and model smoke tests

The evaluation completed successfully with:

- GitHub Copilot CLI using `gpt-5.4`
- GitHub Copilot CLI using `claude-sonnet-5`
- Claude Code using `claude-sonnet-5`

## Scenario results

Run `20260929T004000Z-f1d89da0` completed all six scenarios with three
harness/model targets. All 18 combinations passed independent end-state
validation, all three Azure preflights passed, and cleanup completed without
errors.

| Scenario | Harness | Model | Result | Run ID |
|---|---|---|---|---|
| JavaScript app | Copilot | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| Python API | Copilot | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| RAG | Copilot | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| Serverless API | Copilot | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| Event-driven app | Copilot | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| Multi-tenant app | Copilot | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| JavaScript app | Copilot | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| Python API | Copilot | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| RAG | Copilot | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| Serverless API | Copilot | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| Event-driven app | Copilot | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| Multi-tenant app | Copilot | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| JavaScript app | Claude Code | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| Python API | Claude Code | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| RAG | Claude Code | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| Serverless API | Claude Code | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| Event-driven app | Claude Code | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
| Multi-tenant app | Claude Code | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260929T004000Z-f1d89da0` |
