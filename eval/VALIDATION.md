# Evaluation status

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
