# Security policy

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub: on
[almena-id/agent](https://github.com/almena-id/agent),
open the **Security** tab and choose **Report a vulnerability**. Do not open a
public issue, pull request or discussion about it.

Include what you can of:

- the version or commit;
- what an attacker can do, and under which configuration;
- steps or a proof of concept to reproduce it.

We aim to acknowledge a report within 3 working days and to agree on a
disclosure date with you once the issue is understood. We credit reporters in
the release notes unless you prefer otherwise.

## Supported versions

The project is before its first release: only the `main` branch receives
security fixes.

## Scope

In scope, among others:

- reading or continuing another peer's tasks or conversations;
- prompt injection that makes the agent disclose its configuration or secrets;
- input validation flaws in the A2A endpoints;
- proxy-header misconfiguration in the shipped defaults;
- anything that exposes secrets such as the Anthropic API key.

Out of scope:

- the development setup (`compose.yml`, `.env.example`, `task dev`), e.g.
  `/docs` enabled in `development`;
- the model's answers being wrong, with no security impact;
- denial of service through sheer traffic volume;
- vulnerabilities in dependencies with no demonstrated impact on this
  project (report those upstream).
