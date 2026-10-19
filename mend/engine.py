"""Orchestration: inspect -> classify -> retrieve verified memory -> prepare specialist work orders."""
import os
from . import audit, agents, router, store, creative


def process(job):
    inspection = audit.inspect(job["url"], job["id"])
    task = "design" if job["kind"] == "design_review" else "repair"
    decision = router.classify(inspection, brief=job["brief"], task=task)
    store.record_usage(job["id"], decision["source"], 1, "routing_decision", 0)
    examples = store.find_recipes(job["brief"] + " " + str(inspection.get("counts", {})))
    orders = agents.build_workorders(inspection, decision, job["brief"], examples, job["kind"])
    design = agents.design_spec(inspection, job["brief"]) if task == "design" else None
    direction = creative.generate_design_direction(inspection, design) if design else None
    if direction and direction.get("status") == "generated":
        usage = direction.get("usage", {})
        tokens = (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
        store.record_usage(job["id"], "design_llm", tokens, "tokens_cost_unknown", 0)
    output = {
        "inspection": inspection,
        "decision": decision,
        "verified_examples": examples,
        "work_orders": orders,
        "design_spec": design,
        "design_direction": direction,
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
