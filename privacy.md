---
title: Privacy
description: Analytics and privacy information for the Azure SQL Developer Hub.
permalink: /privacy.html
---

This site uses Microsoft Clarity and Microsoft first-party 1DS telemetry to
understand how visitors use it. We use this information to improve site
usability, content, and agent-skill installation guidance.

## How Clarity is configured

These settings are recorded as a decision in `docs/DECISIONS.md`, and they are
the configuration this site runs with:

- **Strict masking.** Text and input values are masked in the browser before
  anything is sent, so page content in a session replay is obscured rather than
  recorded.
- **Clarity cookies disabled.** The site runs Clarity without its cookies, so no
  consent banner is required.
- **No custom user identifiers.** This site does not send user identifiers to
  Clarity. Only stable allowlisted dimensions become session level custom tags.

Actions the site already tracks, such as choosing a quickstart path or copying a
command, reach Clarity as custom events through a single `track()` helper. They
record that an action happened, not who took it.

## How 1DS telemetry is configured

- **Cookieless SDK configuration.** The 1DS client does not use telemetry
  cookies.
- **Short-lived pseudonymous session.** The site generates a random identifier
  for the current browser tab and stores it in `sessionStorage`. It is not based
  on an account, device, IP address, or browser fingerprint, and it does not
  persist after the tab session ends.
- **Coarse client context.** Events can include the page, browser family,
  operating-system family, device class, language group, referring-site
  category, local UTC offset, and country or region supplied by the telemetry
  service. Raw IP addresses and user-agent strings are not included in custom
  event properties.
- **No copied content.** Copy events identify the skill, prompt, command type,
  harness, and page location, but do not send the copied text, prompt, code,
  connection string, or clipboard contents.
- **No account identity.** The site does not send names, email addresses,
  GitHub usernames, Microsoft account identifiers, or VS Code machine IDs.

The site's normalized event names begin with `mssql-agent-skills/`. Local
previews and forks initialize telemetry in disabled mode and do not send
production events.

## Data collection notice

The software may collect information about you and your use of the software and
send it to Microsoft. Microsoft may use this information to provide services and
improve our products and services. There are also some features in the software
that may enable you and Microsoft to collect data from users of your
applications. If you use these features, you must comply with applicable law,
including providing appropriate notices to users of your applications together
with a copy of Microsoft's privacy statement.

For more information about how Microsoft processes data, see the
[Microsoft Privacy Statement](https://privacy.microsoft.com/privacystatement).
