"""Low-credit routing: deterministic rules first, verified memory second, optional Laya last."""
import os
import threading

_MODEL = None
_LOCK = threading.Lock()
ISSUES = ("javascript", "responsive", "accessibility", "performance", "assets", "general")


def _laya_decision(description):
    global _MODEL
    if os.getenv("MEND_ENABLE_LAYA", "false").lower() != "true":
        return None
    with _LOCK:
        if _MODEL is None:
            from laya import Router
            _MODEL = Router()
    result = _MODEL.predict(description, {
        "issue": {
            "type": "choice",
            "instructions": "Identify the principal website repair issue. Choose general if evidence is inadequate.",
            "criteria": {
                "javascript": "runtime exception, failed JavaScript action, malfunctioning form",
                "responsive": "mobile viewport overflow, misaligned navigation, responsive CSS",
                "accessibility": "accessible names, keyboard navigation, contrast, semantics",
                "performance": "slow loading, large resources, web performance",
                "assets": "missing media, broken images, font loading or broken resources",
                "general": "unclear or mixed issue, requires further investigation",
            }
        }
    })
    guess = result.get("answers", {}).get("issue", {}).get("choice")
    return guess if guess in ISSUES else None


def classify(inspection, brief="", task="repair"):
    """Returns evidence-based route; low-confidence results use general, not risky guesses."""
    if task == "design":
        return {"category": "design", "source": "rules", "reason": "Design request"}
    flags = inspection.get("flags", [])
    counts = inspection.get("counts", {})
    if counts.get("page_errors", 0) > 0:
        return {"category": "javascript", "source": "rules", "reason": "Browser exception observed"}
    if counts.get("horizontal_overflow", 0) > 0:
        return {"category": "responsive", "source": "rules", "reason": "Viewport overflow observed"}
    if counts.get("broken_images", 0) > 0:
        return {"category": "assets", "source": "rules", "reason": "Broken images observed"}
    if counts.get("axe_violations", 0) > 0:
        return {"category": "accessibility", "source": "rules", "reason": "Automated accessibility findings"}
    if inspection.get("load_ms", 0) > 4500:
        return {"category": "performance", "source": "rules", "reason": "Slow browser navigation observed"}
    if flags and "HTTP_ERROR" in flags:
        return {"category": "general", "source": "rules", "reason": "HTTP error observed"}
    try:
        choice = _laya_decision(str(brief) + "\n" + str(inspection)[:3000])
        if choice:
            return {"category": choice, "source": "laya", "reason": "Model classification, requires verification"}
    except Exception:
        # No paid-model fallback: Laya errors must not accidentally incur AI credit costs.
        pass
    return {"category": "general", "source": "rules", "reason": "No deterministic root cause established"}
