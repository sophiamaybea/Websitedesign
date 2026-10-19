"""Orchestration: inspect -> classify -> retrieve verified memory -> prepare specialist work orders."""
import os
from . import audit, agents, router, store


def process(job):
    inspection = audit.inspect(job["url"], job["id"])
    task = "design" if job["kind"] == "design_review" else "repair"
    decision = router.classify(inspection, brief=job["brief"], task=task)
    store.record_usage(job["id"], decision["source"], 1, "routing_decision", 0)
    examples = store.find_recipes(job["brief"] + " " + str(inspection.get("counts", {})))
    orders = agents.build_workorders(inspection, decision, job["brief"], examples, job["kind"])
    output = {
        "inspection": inspection,
        "decision": decision,
        "verified_examples": examples,
        "work_orders": orders,
        "design_spec": agents.design_spec(inspection, job["brief"]) if task == "design" else None,
        "execution": {
            "state": "proposal_only",
            "notes": [
                "No code modifications, production deployments or Instagram posts executed.",
                "OpenHands / Aider coding is a later, separately authorised worker.",
                "Human review required before any client code is changed."
            ]
        }
    }
    store.finish_job(job["id"], output)
    return output
