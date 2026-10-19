# MEND | autonomous web repair and design backend

MEND is the beginning of a self-learning web design and website maintenance studio. The Base44 app will be its customer-facing headquarters; this GitHub repository supplies the independent Python service and worker.

**Status:** working backend scaffold with authenticated job API, durable queue, Playwright website inspection, axe accessibility checks, evidence-based routing, specialist design work orders, optional model adapters, approval gates and a verified repair library. This is NOT a deployed Base44 integration or a fully autonomous website repairer.

## What is real now

- Submit a public HTTP(S) site for inspection or a visual design review.
- Browser worker visits mobile (390px) and desktop (1440px), captures private screenshots, finds viewport overflow, broken images, browser exceptions, HTTP failures, and when installed runs axe-core accessibility checks.
- Rules classify obvious issues for free. An optional Laya Router classifies the remainder; it is disabled by default because model inference needs resources.
- The specialists include creative director, UX architect, visual designer, motion designer, responsive engineer, repair engineer, accessibility specialist and QA inspector.
- A *single* optional OpenAI-compatible LLM call can generate a creative direction for the whole design team rather than paying for seven separate agents.
- The repair library only retrieves human-approved patterns.
- All repair outputs are PROPOSALS. Approval records are explicit. OpenHands dispatch requires a second feature flag, provider key and repository allowlist. There is no automatic merge or deployment.
- Instagram case-study drafts require customer permission; nothing auto-posts.

## Run locally or in a cloud container

Create your own .env from .env.example. Replace MEND_API_KEY with a long random value.

To run with browser auditing and the API together:

1. Install Docker with Compose on a cloud server (for an iPad-only workflow, use your cloud hosting dashboard).
2. Set MEND_API_KEY in the shell or a private deployment secret.
3. Run: docker compose up --build -d

Health: GET /health. Interactive API docs: /docs.

Submit a request using a server-side call (never embed your key in browser JavaScript):

    curl -X POST http://localhost:8000/v1/audits \
      -H "Authorization: Bearer YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"target_url":"https://example.org","brief":"Find mobile navigation issues"}'

Response is a job_id. Poll GET /v1/jobs/{job_id} with the same bearer token.

For a design consultation, POST /v1/design-reviews with the same JSON body.
Use GET /v1/agents to display the specialist roles and GET /v1/metrics for jobs and usage.

An approved job can be exported as a coding task with GET /v1/jobs/{job_id}/coding-preview.
OpenHands dispatch must be opted into by the owner, separately configured, and is never triggered by the baseline audit worker.

## Configure AI only when useful

Without any external AI account the audit, issue routing rules, work orders and repair memory operate.

- Set MEND_ENABLE_LAYA=true after separately installing laya and allowing checkpoint download. The first load may take time and use substantial memory.
- Set MEND_ENABLE_DESIGN_LLM=true and provide MEND_DESIGN_API_URL, MEND_DESIGN_API_KEY, MEND_DESIGN_MODEL to enable one bounded creative-direction call per design review.
- Set MEND_ALLOW_OPENHANDS_DISPATCH=true, MEND_OPENHANDS_API_KEY and MEND_ALLOWED_CODE_REPOS=owner/repo to allow separately approved coding jobs.

Neither cloud model nor OpenHands cloud execution is guaranteed to be free. Set quotas with providers and review their billing settings before enabling.

## Architecture

Base44 server-side function -> authenticated MEND API -> SQLite job queue -> browser worker -> rules / optional Laya -> memory lookup -> specialist work orders -> approved proposal -> optional OpenHands coding agent -> human-reviewed PR.

A later service will connect Postiz and Remotion to create and schedule Instagram posts, with approval and explicit rights to the original site materials.

## Security and limitations

- Public URLs only; private addresses, localhost, internal domains and non-standard ports are refused, and browser requests are screened.
- Browser-side DNS checks do not eliminate DNS rebinding and sandbox escape risk. Use an isolated browser container with network-level restrictions against private IP ranges for any production public scanning service.
- One worker and one local SQLite volume are supported. Move to a managed queue and PostgreSQL before multi-replica production.
- The worker does not execute arbitrary client JavaScript outside the browser sandbox or run submitted code.
- All client code changes, purchases, production deployments and public social posts require express approval.
- Screenshots may contain personal data; protect artifact storage, add retention/deletion controls and get permission before external use.
- Automated accessibility checks are partial and do not replace manual WCAG testing.
- MEND estimated cost metrics cannot calculate external bills until provider-specific costs are supplied; token usage is recorded separately.

## Test

    python -m pip install -r requirements-dev.txt
    pytest -q

CI runs Python compile checks and tests on pushes and pull requests.

Detailed integration inventory: docs/INTEGRATIONS.md.
