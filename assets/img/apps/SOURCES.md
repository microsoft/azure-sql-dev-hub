# App template screenshots

Each picture is a real app, built unattended from its prompt in `build/` by a coding agent during the hub's template evaluation (GitHub Copilot CLI, SQL Server 2025 container, November 2026). The build that showed the most of the template was picked:

| Picture | Prompt | Build |
|---|---|---|
| `docs-chat` | `build/docs-chat.md` | gpt-6.1-sol, baseline |
| `ask-your-data` | `build/ask-your-data.md` | gpt-6.1-sol, baseline |
| `catalog-search` | `build/catalog-search.md` | gpt-6.1-sol, baseline |
| `iot-telemetry` | `build/iot-telemetry.md` | gpt-6.1-sol, baseline |
| `job-queue` | `build/job-queue.md` | gpt-6.1-sol, baseline |
| `room-bookings` | `build/room-bookings.md` | gpt-6.1-sol, baseline |
| `saas-starter` | `build/saas-starter.md` | gpt-6-luna, with the Microsoft SQL skills |
| `wiki-history` | `build/wiki-history.md` | gpt-6.1-sol, baseline |

For the hub, a copy of each app was restyled, and the evaluation's own copies were left as they were. The changes:

- **Colours:** Fluent 2 colours, with Microsoft blue `#0f6cbd` as the accent, neutral greys, and Fluent's success, warning and danger colours.
- **Type and shape:** Segoe UI and Fluent corner radii.
- **Names:** the agents' made-up product names became Contoso names.

Behaviour was not changed. Each copy was rebuilt on a fresh database with its own seed data. It was then used the way a person first would, before the screenshot:

- **ask-your-data and docs-chat:** asked a sample question.
- **catalog-search:** searched.
- **job-queue:** seeded the demo jobs.
- **room-bookings:** moved to the next weekday.
- **saas-starter:** signed in.
- **wiki-history:** opened a page.

The screenshots were taken at 1280×800, at twice the pixel density, and saved as WebP at 1600 and 800 pixels wide.
