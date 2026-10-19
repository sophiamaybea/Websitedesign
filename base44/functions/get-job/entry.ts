import { createClientFromRequest } from "npm:@base44/sdk";
import { secrets } from "base44:runtime";

export default async function (req: Request): Promise<Response> {
  try {
    const base44 = createClientFromRequest(req);
    const user = await base44.auth.me();
    if (!user || user.role !== "admin") {
      return Response.json({ error: "Admin-only pilot" }, { status: 403 });
    }
    const { job_id } = await req.json();
    if (typeof job_id !== "string" ||
        !/^[0-9a-fA-F-]{36}$/.test(job_id)) {
      return Response.json({ error: "Invalid job ID" }, { status: 422 });
    }
    const url = secrets.get("MEND_API_URL");
    const key = secrets.get("MEND_API_KEY");
    if (!url?.startsWith("https://") || !key) {
      return Response.json({ error: "MEND backend is not configured" }, { status: 503 });
    }
    const response = await fetch(url.replace(/\/$/, "") + "/v1/jobs/" + job_id, {
      headers: { "Authorization": "Bearer " + key },
      signal: AbortSignal.timeout(15000)
    });
    return Response.json(await response.json(), { status: response.status });
  } catch {
    return Response.json({ error: "Could not retrieve MEND job" }, { status: 502 });
  }
}
