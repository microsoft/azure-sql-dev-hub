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

All six criteria passed with `gpt-5.4` across isolated live runs:

| Scenario | Result | Evidence run |
|---|---|---|
| JavaScript app | PASS: app built, started, and returned seeded database rows over HTTP. | `20260917T235249Z` |
| Python API | PASS: GET returned JSON rows; POST created a row; completion also succeeded. | `20260917T235932Z` |
| RAG | PASS: native VECTOR column found; independent VECTOR_DISTANCE query returned three ranked rows. | `20260918T010359Z-06399e18` |
| Serverless API | PASS: Function ran locally and SQL input/output bindings returned the inserted row. | `20260917T235932Z` |
| Event-driven app | PASS: Change Tracking found on the table and one insert produced exactly one trigger event. | `20260918T010359Z-1f97a392` |
| Multi-tenant app | PASS: enabled RLS policy found and the isolation tests passed. | `20260918T010337Z` |

`claude-sonnet-5` also completed a live Python API scenario successfully in
`20260918T011701Z-64d73097`, proving that the same Copilot CLI adapter, Azure
lifecycle, and independent validator work with a Claude model.

## Iterations and prompt improvements

The live evaluation found and corrected the following harness issues:

1. The authenticated identity cannot create resource groups at subscription
   scope. Existing-server mode now creates only uniquely named test resources and
   deletes them individually.
2. Project discovery initially selected a dependency's `package.json`. Generated
   and dependency directories are now excluded and covered by a regression test.
3. macOS returned `EPERM` during a process-group exit race after a successful
   server validation. Teardown now tolerates already-gone or inaccessible groups
   and has regression coverage.
4. Parallel runs initially collided on one-second run IDs. IDs now include a
   random suffix and have regression coverage.
5. The independent SQL probe used two unsupported `mssql-python` connection
   string keywords. It now uses the driver's `timeout` argument and was exercised
   by the successful RAG, trigger, and RLS checks.

The RAG prompt itself was insufficient for unattended execution in this
subscription because the authenticated identity cannot create Azure OpenAI Service
resources and no existing deployment is visible. The prompt now permits a
clearly labeled deterministic fixture-vector fallback when no hosted provider is
available. The fallback proves Azure SQL storage and ranking mechanics without
claiming production semantic quality. The improved prompt passed the complete RAG
criterion.

## Cleanup evidence

Every live attempt used a uniquely named database and firewall rule. After each
pass, failure, and harness exception, Azure CLI checks returned empty lists for:

- databases named `hub_prompt_eval_*`
- firewall rules named `evaluation-client-*`
- Azure OpenAI Service accounts named `aoai-*`

The initial resource-group attempt failed authorization before creating a group,
and `az group list` confirmed no `rg-sqlhub-eval-*` group existed.
