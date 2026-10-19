import { createClientFromRequest } from "npm:@base44/sdk";
import { secrets } from "base44:runtime";

export default async function (req: Request): Promise<Response> {
  try {
    const base44 = createClientFromRequest(req);
    const user = await base44.auth.me();
    // Pilot restriction: no tenant isolation exists in MEND yet.
    if (!user || user.role !== "admin") {
      return Response.json({ error: "Admin-only pilot" }, { status: 403 });
    }
    const { target_url, brief = "", mode = "audit" } = await req.json();
    const url = secrets.get("MEND_API_URL");
    const key = secrets.get("MEND_API_KEY");
    if (!url?.startsWith("https://") || !key) {
      return Response.json({ error: "MEND backend is not configured" }, { status: 503 });
    }
    if (mode !== "audit" && mode !== "design_review") {
      return Response.json({ error: "Invalid mode" }, { status: 422 });
    }
    const endpoint = mode === "audit" ? "audits" : "design-reviews";
    const response = await fetch(url.replace(/\/$/, "") + "/v1/" + endpoint, {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ target_url, brief }),
      signal: AbortSignal.timeout(15000)
    });
    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch {
    return Response.json({ error: "Could not submit MEND audit" }, { status: 502 });
  }
}
