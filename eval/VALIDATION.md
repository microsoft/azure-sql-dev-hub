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

## Scenario results

Run `20260925T205633Z-2a884c44` completed all six scenarios with `gpt-5.4`
and `claude-sonnet-5`. All 12 scenario/model combinations passed independent
end-state validation, both Azure preflights passed, and cleanup completed
without errors. The evidence is under
`eval/runs/20260925T205633Z-2a884c44/`.

| Scenario | Model | Result | Run ID |
|---|---|---|---|
| JavaScript app | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260925T205633Z-2a884c44` |
| JavaScript app | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260925T205633Z-2a884c44` |
| Python API | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260925T205633Z-2a884c44` |
| Python API | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260925T205633Z-2a884c44` |
| RAG | `gpt-5.4` | ✅ PASS: provisioned Azure OpenAI and independent end-state validation passed. | `20260925T205633Z-2a884c44` |
| RAG | `claude-sonnet-5` | ✅ PASS: provisioned Azure OpenAI and independent end-state validation passed. | `20260925T205633Z-2a884c44` |
| Serverless API | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260925T205633Z-2a884c44` |
| Serverless API | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260925T205633Z-2a884c44` |
| Event-driven app | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260925T205633Z-2a884c44` |
| Event-driven app | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260925T205633Z-2a884c44` |
| Multi-tenant app | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260925T205633Z-2a884c44` |
| Multi-tenant app | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260925T205633Z-2a884c44` |
