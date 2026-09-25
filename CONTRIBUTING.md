# Contributing to the Azure SQL Developer Hub

Thank you for your interest in improving the Azure SQL Developer Hub.

## Before you contribute

- Search existing [issues](../../issues) and [pull requests](../../pulls) before starting work.
- Report security vulnerabilities privately as described in [SECURITY.md](SECURITY.md), not in a
  public issue.
- Follow the [Microsoft Open Source Code of Conduct](CODE_OF_CONDUCT.md).

## Contributor License Agreement

All contributions are subject to Microsoft's Contributor License Agreement (CLA). Most
contributions require you to agree to a CLA declaring that you have the right to, and actually
do, grant Microsoft the rights to use your contribution. For details, visit
[https://cla.opensource.microsoft.com](https://cla.opensource.microsoft.com).

When you submit a pull request, the CLA bot determines whether you need to provide a CLA and
adds the appropriate status check or comment. Follow the instructions provided by the bot. You
only need to complete this process once across repositories that use the Microsoft CLA.

## What to change

This repository is the source of a static Jekyll site published to GitHub Pages. Every page is a
markdown file published twice, once as HTML and once as its own source at `<page>.md`, so the
human page and the machine-readable twin cannot drift. Changes to page copy, the build prompts
under `build/`, layouts, styles, and the scripts in `scripts/` are all welcome.

Home page hero and card copy lives in the front matter of `index.md` rather than in the body,
because the layout consumes it as structured data. `scripts/build-agent-files.mjs` renders it
back into markdown for the twin, so edit the front matter and let the script regenerate.

## Pull requests

1. Create a focused branch and keep changes limited to one concern.
2. Do not include credentials, customer data, internal Microsoft information, or generated
   binaries.
3. Run the checks, in this order:

   ```
   npm test
   bundle exec jekyll build
   npm run build:agent-files
   npm run check:links
   ```

   `npm test` applies the house rules in `scripts/check-house-rules.mjs`. `check:links` reads the
   built site, so it needs the build and the agent-file generator to have run first. This is the
   order CI uses, so a green run locally and a green run in CI mean the same thing.
4. Append a dated line to `docs/DECISIONS.md` if the pull request makes an irreversible or
   debatable choice. Do not rewrite past entries: if a decision is reversed, add a new line
   saying so and why.
5. Describe the change, its user impact, and how you validated it.

By participating in this project, you agree to follow its
[Code of Conduct](CODE_OF_CONDUCT.md).
