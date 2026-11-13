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

Behaviour was not changed. Each copy was rebuilt on a fresh database with its own seed data. It was then used in the app, through its own pages, until it showed the feature the template is about. Each picture is cropped to that feature:

| Picture | What it shows | How it got there |
|---|---|---|
| `docs-chat` | An answer with the passage it cites | Asked two questions |
| `ask-your-data` | The generated SQL, marked read-only | Ran the "Monthly revenue" sample question |
| `catalog-search` | Filters with counts beside ranked results | Searched for "wireless" |
| `iot-telemetry` | A room's temperature crossing the 30°C alert line | Opened the mechanical room's chart |
| `job-queue` | A dead job after 3 of 3 attempts | Seeded the demo jobs and opened a dead one |
| `room-bookings` | The day's bookings on the room timeline | Opened the next weekday |
| `saas-starter` | Members, their roles, and the plan's seat limit | Signed in and opened Members |
| `wiki-history` | Two versions of a page compared line by line | Edited the onboarding checklist and compared it with the version before |

Most pictures were taken in a window 480 pixels wide, where the app lays out in one column. Catalog search was taken at 1280 pixels, because its filters fold away in a narrow window. All were taken at three times the pixel density, and saved as WebP at 1600 and 800 pixels wide.
