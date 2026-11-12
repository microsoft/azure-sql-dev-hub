# PR checks and previews

Every pull request runs [`.github/workflows/pr.yml`](../.github/workflows/pr.yml). It posts one comment on the PR and updates it on every push.

## What runs

| Check | Script or tool | Blocks the PR |
|---|---|---|
| House rules and telemetry rules | `npm test` | Yes |
| Build site and Markdown twins | Jekyll, `scripts/build-agent-files.mjs` | Yes |
| Internal links and anchors | `scripts/check-links.mjs` | Yes |
| Page checks and agent-readiness score | `scripts/check-pages.mjs` | On errors, or if the score drops below the base branch |
| Agent files: robots.txt, sitemap, llms.txt and others | [Lumar `agentic-readiness`](https://agentic-readiness.lumar.io/cli) (MIT), against the built site served in the job | On a published file that is broken |
| External links | `scripts/check-external-links.mjs` | No, report only |

Run them locally after a build:

```bash
bundle exec jekyll build && node scripts/build-agent-files.mjs
node scripts/check-links.mjs
node scripts/check-pages.mjs
node scripts/check-external-links.mjs
```

## The score

`check-pages.mjs` scores the built site out of 100, using the checklist of the public agent-readiness scanners for everything the site controls from its own files.

- **Site checks (30 points):** llms.txt, llms-full.txt, sitemap, robots.txt, and a helpful 404 page.
- **Page checks (70 points):** `lang`, title, description, canonical link, Open Graph tags, JSON-LD, one h1, headings in order, text without JavaScript, image alt text, and a Markdown twin. Each check earns its points times the share of pages that pass.

The public scanners (is-agentic.com, open-agent-readiness, isitagentready.com) grade a whole host. This site lives on a subpath of `microsoft.github.io`, so they grade the org's landing page instead. They become useful once the site has its own domain.

## Previews

Pull requests from branches in this repository get a preview at `<site>/pr/<number>/`:

1. `pr.yml` builds the site for that subfolder, with analytics off and `noindex` on every page, and commits it to the `pr-previews` branch.
2. It starts `pages.yml`, which publishes `main` plus the folders of open PRs.
3. When the PR closes, its folder is removed and the site redeploys.

Previews carry a banner linking to the live site. They are not in the live sitemap, llms.txt, or llms-full.txt. The repository is public, so the `pr-previews` branch and the preview links are too.

Pull requests from forks, and Dependabot's, get the checks and a job summary, but no preview and no comment: their workflow token cannot write.

No secret is involved. The only token is the workflow's own `GITHUB_TOKEN`.
