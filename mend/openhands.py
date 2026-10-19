"""Approval-gated integration with OpenHands Cloud V1 API.

External execution is deliberately opt-in and never triggered by auditing.
Use only repositories the operator owns or has explicit authority to edit.
"""
import os
import httpx


def coding_task(job):
    if job["state"] != "approved" or not job["result"]:
        raise ValueError("Only an approved proposal can generate a coding task")
    result = job["result"]
    workorders = result.get("work_orders", [])
    task = "\n".join(
        a["role"] + ": " + a["task"] + ". Acceptance: " + a["acceptance"]
        for a in workorders
    )
    return (
        "MEND authorised coding proposal for " + job["url"] + "\n"
        "Client brief: " + job["brief"][:2500] + "\n"
        "Confirmed evidence: " + str(result["inspection"].get("counts", {})) + "\n"
        "Work orders:\n" + task + "\n"
        "First reproduce the failure in a sandbox. Implement the smallest safe patch. "
        "Run checks, attach before/after evidence, and open a draft PR only. "
        "Do not deploy to production, publish social posts, access private customer data "
        "outside this authorised repository, or merge a PR. "
        "If the repository is not accessible or the root cause is unproven, stop and report."
    )


def dispatch(job, repository):
    """Explicit call. This may consume external provider credits."""
    if os.getenv("MEND_ALLOW_OPENHANDS_DISPATCH", "false").lower() != "true":
        raise RuntimeError("OpenHands dispatch disabled")
    allowlist = {s.strip() for s in os.getenv("MEND_ALLOWED_CODE_REPOS", "").split(",") if s.strip()}
    if not repository or repository not in allowlist:
        raise ValueError("Target repository is not authorised")
    key = os.getenv("MEND_OPENHANDS_API_KEY", "")
    if not key:
        raise RuntimeError("Missing OpenHands API key")
    payload = {
        "initial_message": {
            "content": [{"type": "text", "text": coding_task(job)}]
        },
        "selected_repository": repository
    }
    with httpx.Client(timeout=20) as client:
        response = client.post(
            "https://app.all-hands.dev/api/v1/app-conversations",
            headers={"Authorization": "Bearer " + key},
            json=payload)
        response.raise_for_status()
    task = response.json()
    return {"provider": "openhands", "start_task_id": task.get("id"),
            "status": task.get("status", "submitted"),
            "note": "External coding started; review its draft PR before accepting."}
