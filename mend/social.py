"""No publishing without permission. Produce truthful Instagram case-study drafts."""
def case_study_draft(job, customer_permission=False):
    if not customer_permission:
        raise PermissionError("Explicit permission is required for public case studies")
    if job["state"] != "approved":
        raise ValueError("Only approved results may be considered")
    inspected = (job["result"] or {}).get("inspection", {})
    counts = inspected.get("counts", {})
    issues = [name.replace("_", " ") for name, value in counts.items()
              if name not in {"requests"} and isinstance(value, int) and value > 0]
    return {
        "status": "draft_only",
        "series": "The Fix Files",
        "caption": "Website check: " + (", ".join(issues[:3]) or "technical inspection")
                   + ". Here is what we observed and what we proposed.",
        "storyboard": ["Authorised before screenshot", "Evidence-based issue highlight",
                       "Proposed solution overview", "Verified after screenshot, if available",
                       "MEND | Design. Repair. Evolve."],
        "disclosure": "Do not claim a completed fix unless a post-repair audit verifies it.",
        "publisher": "Postiz / Instagram professional account, requires separate credentials and approval",
        "approved_for_publish": False
    }
