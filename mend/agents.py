"""Real agent work-order generation. Agent prompts do not equal uncontrolled agent execution."""
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Agent:
    name: str
    role: str
    objective: str
    evidence_required: str
    completion_gate: str


AGENTS = [
    Agent("scout", "Site Intake", "Check requested scope, canonical URLs and crawl boundaries.",
          "Customer-authorised URL and task", "Scope recorded"),
    Agent("diagnostician", "Root Cause Engineer", "Trace symptoms to reproducible technical causes.",
          "Console logs, viewport measurements and errors", "Reproduction steps present"),
    Agent("creative_director", "Art Direction", "Develop a distinct, editorial design concept, not a template.",
          "Customer brief, visual reference permission and current screenshots", "Rationale ties to brief"),
    Agent("ux_architect", "Experience Design", "Design readable hierarchy, accessible navigation and meaningful CTAs.",
          "Audience, content hierarchy and device use cases", "User journeys and screen states specified"),
    Agent("visual_designer", "Visual Design", "Specify grids, spacing, type scales, color systems and polished components.",
          "Screenshot measurements and content structure", "Responsive design tokens and states defined"),
    Agent("motion_designer", "Interaction Design", "Specify GSAP/Three.js motion with graceful reduced-motion fallback.",
          "Interaction goals, device capabilities and performance budget", "Motion spec includes fallback"),
    Agent("responsive_engineer", "Responsive Design", "Adapt layout across small, medium and large screens.",
          "320px, 390px, 768px and 1440px layout requirements", "No accidental horizontal overflow"),
    Agent("repair_engineer", "Code Repair", "Prepare smallest safe code change with clear rollback.",
          "Authorized repository access, reproduction and existing tests", "Patch reviewed and tests pass"),
    Agent("accessibility_specialist", "Accessibility", "Review semantic structure, keyboard use and known WCAG risks.",
          "axe findings and manual audit notes", "Unverified accessibility claims prohibited"),
    Agent("inspector", "Independent QA", "Verify changes across browsers and preserve visual integrity.",
          "Before/after screenshots, functional tests and regression report", "No unexplained regressions"),
    Agent("archivist", "Repair Memory", "Store reusable patterns only after verified human approval.",
          "Patch, tests, acceptance and owner approval", "Verified record stored with provenance"),
    Agent("social_director", "Marketing", "Create case-study concepts from authorised customer results.",
          "Written permission, genuine before/after evidence", "Publishing requires explicit approval"),
]


def registry():
    return [asdict(a) for a in AGENTS]


def build_workorders(inspection, decision, brief="", examples=None, kind="audit"):
    category = decision["category"]
    diagnosis = ["diagnostician", "repair_engineer", "inspector"]
    design = ["creative_director", "ux_architect", "visual_designer",
              "motion_designer", "responsive_engineer", "accessibility_specialist", "inspector"]
    chosen = design if kind == "design_review" else diagnosis
    if category == "accessibility":
        chosen = ["accessibility_specialist", "repair_engineer", "inspector"]
    if category == "responsive":
        chosen = ["responsive_engineer", "visual_designer", "repair_engineer", "inspector"]
    agents = {a.name: a for a in AGENTS}
    context = {
        "customer_request": brief,
        "decision": decision,
        "site_title": inspection.get("title"),
        "target_url": inspection.get("url"),
        "observed_counts": inspection.get("counts", {}),
        "observed_flags": inspection.get("flags", []),
        "previous_verified_repairs": examples or [],
    }
    orders = []
    for name in chosen:
        agent = agents[name]
        orders.append({
            "agent": name, "role": agent.role, "task": agent.objective,
            "evidence_required": agent.evidence_required,
            "acceptance": agent.completion_gate, "context": context,
            "state": "awaiting_execution",
        })
    return orders


def design_spec(inspection, brief=""):
    """Deterministic starting brief for specialist agents; not falsely called finished AI design."""
    return {
        "customer_brief": brief,
        "creative_direction": "Editorial clarity, distinctive geometry, considered whitespace.",
        "discovery": ["Identify brand and audience", "Inventory existing pages and content",
                      "Request authorised visual references", "Measure existing layouts"],
        "deliverables": {
            "art_direction": ["moodboard", "three visual concepts", "typographic rationale"],
            "experience": ["information architecture", "primary user journeys", "keyboard flow"],
            "design_system": ["responsive grid", "colour tokens", "type scale", "component states"],
            "motion": ["GSAP timeline specification", "Three.js performance budget",
                       "prefers-reduced-motion fallback", "mobile GPU fallback"],
            "qa": ["320/390/768/1440px screenshots", "automated and manual accessibility review",
                   "interaction tests", "visual regression diff"],
        },
        "constraints": ["No copyright infringement: only use authorised source designs/assets.",
                        "No fabricated Lighthouse scores or customer claims.",
                        "No production changes before customer approval."],
        "current_site": {"title": inspection.get("title"), "url": inspection.get("url")},
        "state": "design_work_order_only"
    }
