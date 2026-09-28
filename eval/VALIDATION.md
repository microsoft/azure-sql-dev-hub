# Evaluation status

## Model smoke tests

GitHub Copilot CLI 1.0.85 successfully completed noninteractive smoke tests with:

- `gpt-5.4`
- `claude-sonnet-5`

## Scenario results

Run `20260928T172540Z-ae419628` completed all six scenarios with `gpt-5.4`
and `claude-sonnet-5`. All 12 scenario/model combinations passed independent
end-state validation, both Azure preflights passed, and cleanup completed
without errors. The evidence is under
`eval/runs/20260928T172540Z-ae419628/`.

| Scenario | Model | Result | Run ID |
|---|---|---|---|
| JavaScript app | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260928T172540Z-ae419628` |
| JavaScript app | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260928T172540Z-ae419628` |
| Python API | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260928T172540Z-ae419628` |
| Python API | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260928T172540Z-ae419628` |
| RAG | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260928T172540Z-ae419628` |
| RAG | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260928T172540Z-ae419628` |
| Serverless API | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260928T172540Z-ae419628` |
| Serverless API | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260928T172540Z-ae419628` |
| Event-driven app | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260928T172540Z-ae419628` |
| Event-driven app | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260928T172540Z-ae419628` |
| Multi-tenant app | `gpt-5.4` | ✅ PASS: independent end-state validation passed. | `20260928T172540Z-ae419628` |
| Multi-tenant app | `claude-sonnet-5` | ✅ PASS: independent end-state validation passed. | `20260928T172540Z-ae419628` |
