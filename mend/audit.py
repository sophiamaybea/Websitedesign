"""Playwright browser inspector + locally installed axe-core. No AI used for evidence gathering."""
import os
import time
from pathlib import Path
from urllib.parse import urlsplit
from .security import validate_public_url, UnsafeTarget


def inspect(url, job_id):
    """Only public sites. Do not store cookies, page text, credentials or browser state."""
    if os.getenv("MEND_ENABLE_BROWSER", "true").lower() != "true":
        raise RuntimeError("Browser audits disabled; no inspection was performed")
    validate_public_url(url)
    from playwright.sync_api import sync_playwright, TimeoutError as BrowserTimeout
    artifacts = Path(os.getenv("MEND_ARTIFACT_DIR", "artifacts"))
    artifacts.mkdir(parents=True, exist_ok=True)
    axe_file = Path(__file__).resolve().parent.parent / "audit-tools" / "node_modules" / "axe-core" / "axe.min.js"
    max_requests = int(os.getenv("MEND_MAX_AUDIT_REQUESTS", "80"))
    started = time.monotonic()
    result = {"url": url, "title": "", "flags": [], "counts": {},
              "viewports": {}, "console_errors": [], "axe": {"status": "not_run"}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            for label, width, height in (("mobile", 390, 844), ("desktop", 1440, 900)):
                context = browser.new_context(viewport={"width": width, "height": height},
                    device_scale_factor=1, ignore_https_errors=False,
                    accept_downloads=False, service_workers="block")
                try:
                    page = context.new_page()
                    errors = []
                    counters = {"requests": 0, "broken_images": 0,
                                "horizontal_overflow": 0, "page_errors": 0, "http_errors": 0}
                    def guard(route):
                        counters["requests"] += 1
                        if counters["requests"] > max_requests:
                            route.abort()
                            return
                        try:
                            validate_public_url(route.request.url)
                            route.continue_()
                        except (UnsafeTarget, Exception):
                            route.abort()
                    page.route("**/*", guard)
                    page.on("pageerror", lambda error: errors.append(str(error)[:300]))
                    response = None
                    try:
                        response = page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        page.wait_for_timeout(900)
                    except BrowserTimeout:
                        result["flags"].append("TIMEOUT_" + label.upper())
                    status = response.status if response else None
                    if status is not None and status >= 400:
                        counters["http_errors"] += 1
                        result["flags"].append("HTTP_ERROR")
                    title = page.title()[:250] if response else ""
                    result["title"] = result["title"] or title
                    dimensions = page.evaluate("""() => ({
                        document: document.documentElement.scrollWidth,
                        viewport: window.innerWidth,
                        brokenImages: Array.from(document.images).filter(i => !i.complete || i.naturalWidth === 0).length,
                        h1Count: document.querySelectorAll('h1').length
                    })""")
                    counters["horizontal_overflow"] = int(dimensions["document"] > dimensions["viewport"] + 3)
                    counters["broken_images"] = dimensions["brokenImages"]
                    counters["page_errors"] = len(errors)
                    result["console_errors"].extend(errors[:5])
                    screenshot = artifacts / (job_id + "-" + label + ".png")
                    page.screenshot(path=str(screenshot), full_page=False, timeout=10000)
                    result["viewports"][label] = {
                        "width": width, "height": height, "http_status": status,
                        "h1_count": dimensions["h1Count"],
                        "overflow": bool(counters["horizontal_overflow"]),
                        "screenshot": screenshot.name
                    }
                    if label == "desktop" and axe_file.exists() and response:
                        try:
                            page.add_script_tag(path=str(axe_file))
                            axe = page.evaluate("""async () => {
                                const r = await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa']}});
                                return r.violations.map(v => ({id:v.id, impact:v.impact, nodes:v.nodes.length}));
                            }""")
                            result["axe"] = {"status": "complete", "violations": axe[:30]}
                            counters["axe_violations"] = len(axe)
                        except Exception as exc:
                            result["axe"] = {"status": "failed", "detail": type(exc).__name__}
                    for key, value in counters.items():
                        if key != "requests":
                            result["counts"][key] = result["counts"].get(key, 0) + value
                    result["counts"]["requests"] = result["counts"].get("requests", 0) + counters["requests"]
                finally:
                    context.close()
        finally:
            browser.close()
    result["load_ms"] = round((time.monotonic() - started) * 1000)
    result["flags"] = sorted(set(result["flags"]))
    return result
