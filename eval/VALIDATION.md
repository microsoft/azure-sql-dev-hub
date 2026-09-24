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

| Scenario | Model | Result | Run ID |
|---|---|---|---|
| JavaScript app | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260924T190604Z-c3560ff0` |
| JavaScript app | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260924T190604Z-c3560ff0` |
| Python API | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260924T190604Z-c3560ff0` |
| Python API | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260924T190604Z-c3560ff0` |
| RAG | `gpt-5.4` | ✅ PASS: provisioned Azure OpenAI and independent end-state validation passed. | `20260924T190604Z-c3560ff0` |
| RAG | `claude-sonnet-5` | ✅ PASS: provisioned Azure OpenAI and independent end-state validation passed. | `20260924T190604Z-c3560ff0` |
| Serverless API | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260924T190604Z-c3560ff0` |
| Serverless API | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260924T190604Z-c3560ff0` |
| Event-driven app | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260924T190604Z-c3560ff0` |
| Event-driven app | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260924T190604Z-c3560ff0` |
| Multi-tenant app | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260924T190604Z-c3560ff0` |
| Multi-tenant app | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260924T190604Z-c3560ff0` |
