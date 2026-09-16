# SQLCon mockup handoff

September 16, 2026. PM owns content and mockup approval. Engineering owns prompt validation and Clarity telemetry implementation, as agreed with Carlos. This PR is a review mockup, not a validated application release.

## Prompt validation

Start with the featured JavaScript app, Python API and Python RAG drafts. Confirm the final launch selection with PM. Execute the exact published prompts in documented environments, check the resulting application and database operations, record agent/model and runtime versions, and return one consolidated correction list. RAG requires available embedding and generation services.

Extend the existing evaluation lab where appropriate. Use explicit outcome checks and retained run evidence. Include independent review instead of relying only on the executing agent's self-assessment. Record preview access requirements and limitations. A page preview or successful copy is not proof that an application works.

Publish only the paths that pass validation and PM content approval. Additional framework variants and workflows remain post-SQLCon work. Existing scenario URLs are retained for compatibility and are not evidence of validated launch coverage.

## Clarity implementation

Engineering owns project setup, site configuration, applicable consent and masking configuration, instrumentation, and ingestion verification. PM owns measurement questions and reporting interpretation. The current mock retains console event hooks; Clarity is not installed or activated by this PR.

Measure page views and preserve existing action names: gallery_card_open, copy_prompt, copy_code, copy_command, install_cmd_copy, docs_outbound and azure_outbound where the relevant UI exists. Count copies only after clipboard success. Use stable scenario/source identifiers, never copied content or credentials. Document how event names and dimensions map to Clarity's API.

Verify a controlled visit, scenario open, successful copy and outbound click in Clarity. Test clipboard failure and blocked analytics, and ensure the site stays usable. Give PM reporting access. Use existing reporting features for launch; a custom dashboard is deferred. Do not add telemetry to installed skills or interpret browser actions as completed applications or direct agent fetches.

## Release checks

Run house rules, Jekyll build, Markdown generation and internal link checks. Review mobile and keyboard navigation, no-JavaScript reading, prompt parity between HTML/copy/Markdown, and the alternate Markdown links. Confirm the intended audience can access the deployed URL. Public launch requires a publicly accessible URL, not just access from an employee account.

## References

- Prompt quality reference: https://aka.ms/azuresqldb-container-build
- Clarity: https://learn.microsoft.com/en-us/clarity/setup-and-installation/clarity-setup
- Quickstart pattern: https://docs.docker.com/ai/sandboxes/
- Tabbed code pattern: https://docs.stripe.com/
