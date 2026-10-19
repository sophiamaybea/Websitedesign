# MEND integration status

## Implemented in this repository

- FastAPI HTTP endpoints for Base44 backend functions.
- Durable SQLite jobs and a polling worker with recovery leases.
- Playwright Chromium diagnostics on desktop/mobile; screenshots require authentication.
- axe-core browser evaluation when npm dependency is installed.
- Laya Python Router integration (optional, disabled by default), with deterministic routing first.
- Specialist design/repair work orders.
- Optional single OpenAI-compatible design model call (disabled by default).
- Optional OpenHands Cloud V1 dispatch, gated by prior approval + repository allowlist + feature flag.
- Human-approved repair patterns and low-cost lexical retrieval.
- Marketing drafts gated by explicit publication permission.

## Not yet implemented

- Base44 app linkage, authorisation and entity synchronisation (Base44 app ID not supplied).
- OpenHands running autonomously on customer projects (API key and approved repo needed).
- Actual code repair in the baseline worker; output is a proposal, not an executed patch.
- Postiz account connection, Instagram publication, analytics or video rendering.
- Lighthouse subprocess integration, site crawling, multi-user billing.
- Distributed workers / managed PostgreSQL. Current SQLite supports one shared-disk instance.

## Source projects (do not vendor or silently copy upstream source)

Playwright: https://github.com/microsoft/playwright
axe-core: https://github.com/dequelabs/axe-core
Laya: https://github.com/NandhaKishorM/laya
OpenHands SDK: https://github.com/OpenHands/software-agent-sdk
Chrome DevTools MCP: https://github.com/ChromeDevTools/chrome-devtools-mcp
Lighthouse: https://github.com/GoogleChrome/lighthouse
Argos: https://github.com/argos-ci/argos
Mem0: https://github.com/mem0ai/mem0
Postiz: https://github.com/gitroomhq/postiz-app
Remotion: https://github.com/remotion-dev/remotion

Each project retains its own licence. Use the upstream package or hosted API according
to its licence, rather than copying entire projects into this repository.

## Example Base44 function (illustration, not yet linked to a Base44 app)

A Base44 backend function can POST an authorised URL to the MEND API using its
secret environment value MEND_API_KEY. Client-side JavaScript should never hold
that key. Call POST /v1/audits with a JSON body containing target_url and brief.
Poll GET /v1/jobs/<job_id> and display the output as an unverified proposal.
