---
title: Privacy
description: Analytics and privacy information for the Azure SQL Developer Hub.
permalink: /privacy.html
---

This site uses Microsoft Clarity to understand how visitors use it, through
behavioral metrics, heatmaps, and session replay. We use this information to
improve site usability.

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
