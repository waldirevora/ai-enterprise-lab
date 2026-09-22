# Security Policy

Security, privacy, access control and fail-closed behavior are core properties of AI Enterprise Lab.

## Supported code

Security reports should target the current `main` branch. Older commits, experimental branches and forks are not maintained as supported releases.

## Reporting a vulnerability

Do not publish credentials, exploit details, private enterprise data or sensitive logs in a public GitHub issue.

Contact the repository maintainer through a private contact channel associated with the project or maintainer profile before sharing sensitive technical details.

When reporting, include:

- affected component and version or commit;
- reproducible steps;
- expected and observed behavior;
- security impact;
- sanitized logs or evidence;
- suggested remediation, when available.

Never include API keys, passwords, `.env` contents, access tokens or real private datasets.

## Security model

The project uses server-side authentication and authorization, deny-by-default boundaries, document ACLs, classification controls, rate limiting, audit events, local-first AI providers and explicit policy gates for external providers.

Administrative onboarding is intentionally local-development oriented. `bootstrap_access` refuses to run when `APP_ENV=production`.

API credentials can be revoked with the supported revocation CLI.

## Disclosure

Allow reasonable time for investigation and remediation before public disclosure. No fixed response-time SLA is currently published.

## License

This security policy does not grant additional rights to use, modify or redistribute the repository. The project currently has no selected open-source license.
