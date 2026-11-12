# PR checks

Every pull request runs [`.github/workflows/pr.yml`](../.github/workflows/pr.yml). It posts one comment on the PR and updates it on every push. Nothing deploys, the live site is never touched, and no secret is involved.

## What runs

| Check | Tool | Blocks the PR |
|---|---|---|
| House rules and telemetry rules | `npm test` | Yes |
| Build site and Markdown twins | Jekyll, `scripts/build-agent-files.mjs` | Yes |
| Internal links and anchors | `scripts/check-links.mjs` | Yes |
| Page checks and score out of 100 | `scripts/check-pages.mjs` | On errors, or a lower score than the base branch |
| Agent files: robots.txt, sitemap, llms.txt and others | [Lumar `agentic-readiness`](https://agentic-readiness.lumar.io/cli) (MIT) | On a published file that is broken |
| Agent-readiness score out of 100, PR and base | [`open-agent-readiness`](https://gitlab.com/startuphub-ai/open-agent-readiness) (MIT), over a public tunnel | No, report only |
| Agent Readability Spec score out of 100, PR and base | [`@vercel/agent-readability`](https://www.npmjs.com/package/@vercel/agent-readability) audit (MIT), run in the job | No, report only |
| Links, internal and external | [linkinator](https://github.com/JustinBeckwith/linkinator) (MIT) | No, report only |
| Visual diff against the base branch | [BackstopJS](https://github.com/garris/BackstopJS) (MIT) | No, report only |

Pull requests from forks, and Dependabot's, run every check and get the results in the Checks job summary, but no comment: their workflow token cannot write.

## How it works

1. The job builds the PR and the base branch, and serves each with `scripts/serve-site.mjs`, which answers the way GitHub Pages does: `/page` finds `page.html`, a missing path gets `404.html` with a 404 status, and there is no content negotiation.
2. `open-agent-readiness` grades a whole public host and refuses local addresses. This site lives on a subpath of `microsoft.github.io`, so it cannot grade the live site either. Each build gets a [Cloudflare quick tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/) for the length of the scan: a temporary `https://<random>.trycloudflare.com` with the site at its root. Quick tunnels are free, need no account, and are meant for testing. They have no uptime guarantee, so a failed tunnel shows "unavailable" and does not fail the PR. `cloudflared` is pinned and its checksum verified.
3. BackstopJS captures only the pages whose built output changed (`scripts/visual/changed-pages.mjs`), plus the key pages when shared CSS, JS or images changed, at desktop and phone widths from each build, with reduced motion so animations rest. A PR that changes no page gets no screenshots. Changed screenshots go to the `pr-assets` branch under `pr/<number>/` so the comment can show them, and closing the PR removes them. The full report is in the run's `pr-report` artifact.

The key pages are listed in `scripts/visual/changed-pages.mjs`.

The open-agent-readiness score is the scanner's own. A few of its checks grade Cloudflare's edge in front of the tunnel (its robots.txt and its blocking of AI crawlers) rather than this site; the comment lists those apart. The PR and base go through the same edge, so the difference between them is fair.

## Run it locally

After a build:

```bash
node scripts/check-links.mjs
node scripts/check-pages.mjs
node scripts/serve-site.mjs _site 8080 &
npx agentic-readiness@0.3.7 localhost:8080 --allow-private
npx linkinator@8.1.0 http://localhost:8080/ --recurse
```

## The page score

`check-pages.mjs` scores the built site out of 100, offline, using the checklist of the public agent-readiness scanners for everything the site controls from its own files.

- **Site checks (30 points):** llms.txt, llms-full.txt, sitemap, robots.txt, and a helpful 404 page.
- **Page checks (70 points):** `lang`, title, description, canonical link, Open Graph tags, JSON-LD, one h1, headings in order, text without JavaScript, image alt text, and a Markdown twin. Each check earns its points times the share of pages that pass.

Two rules are required rather than scored, and fail the build: `llms.txt` keeps its "When to use this site" section (at least three jobs and numbered steps), and every page's JSON-LD keeps the publisher's Organization with its name, url, description, logo and three sameAs links.
