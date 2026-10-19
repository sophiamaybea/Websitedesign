# Wiring MEND into Base44 (code prepared, not deployed)

These two admin-only pilot backend functions use official Base44 SDK
createClientFromRequest and the base44:runtime secrets utility.

- base44/functions/submit-audit/entry.ts
- base44/functions/get-job/entry.ts

Deploy these into an authorised Base44 app using Base44's CLI or remote
sandbox workflow after connecting the app. The code in GitHub alone
does not create or deploy Base44 functions.

Set environment secrets in Base44 app settings:
- MEND_API_URL: public HTTPS endpoint of deployed MEND API
- MEND_API_KEY: a long shared secret also set on MEND server

Because backend currently uses a single operator key, pilot functions
require Base44 admin role. Multi-client access needs per-tenant DB
records and proper job-level access control before it can be enabled.

From an authenticated Base44 admin client, invoke submit-audit with:
{target_url: 'https://example.org', brief: 'Analyse responsiveness', mode: 'design_review'}
Then invoke get-job with the returned job_id.

Keep the secret server-side. Do not use Base44 Core.InvokeLLM for site checks:
the Playwright and rule-based worker can produce evidence without spending LLM credits.
