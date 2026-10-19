"""Deterministic tests: external sites, providers and browsers are mocked."""
import os
from fastapi.testclient import TestClient
from mend import store, security, agents, engine, router
from mend.api import app

TOKEN = "test-key-that-is-at-least-24-characters-long"
HEADERS = {"Authorization": "Bearer " + TOKEN}


def test_api_and_workflow(tmp_path, monkeypatch):
    monkeypatch.setenv("MEND_DB_PATH", str(tmp_path / "mend.db"))
    monkeypatch.setenv("MEND_API_KEY", TOKEN)
    monkeypatch.setattr("mend.api.validate_public_url", lambda u: u)
    inspection = {"url": "https://example.org", "title": "Demo", "flags": [],
                  "counts": {"horizontal_overflow": 1}, "load_ms": 700}
    monkeypatch.setattr("mend.audit.inspect", lambda url, jid: inspection)
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/v1/agents").status_code == 401
        created = client.post("/v1/audits", headers=HEADERS,
                              json={"target_url": "https://example.org",
                                    "brief": "Fix mobile menu"})
        assert created.status_code == 202
        job_id = created.json()["job_id"]
        assert store.claim_job()["id"] == job_id
        engine.process(store.get_job(job_id))
        completed = client.get("/v1/jobs/" + job_id, headers=HEADERS).json()
        assert completed["state"] == "proposal"
        assert completed["result"]["decision"]["category"] == "responsive"
        assert completed["result"]["work_orders"][0]["agent"] == "responsive_engineer"
        assert completed["result"]["execution"]["state"] == "proposal_only"
        bad = client.post("/v1/recipes", headers=HEADERS, json={
            "source_job": job_id, "symptom": "Mobile navigation layout breaks",
            "environment": "CSS grid", "repair": "Adjust breakpoint and CSS grid",
            "verification": "Screenshots and Playwright regression pass"})
        assert bad.status_code == 409
        approved = client.post("/v1/jobs/" + job_id + "/approve", headers=HEADERS,
                               json={"reviewer": "human-owner"})
        assert approved.status_code == 200
        result = client.post("/v1/recipes", headers=HEADERS, json={
            "source_job": job_id, "symptom": "Mobile navigation layout breaks",
            "environment": "CSS grid", "repair": "Adjust breakpoint and CSS grid",
            "verification": "Screenshots and Playwright regression pass"})
        assert result.status_code == 201
        assert len(store.find_recipes("mobile navigation CSS grid")) == 1
        assert client.get("/v1/metrics", headers=HEADERS).json()["verified_repairs"] == 1


def test_design_agents(tmp_path, monkeypatch):
    monkeypatch.setenv("MEND_DB_PATH", str(tmp_path / "design.db"))
    store.initialise()
    monkeypatch.setattr("mend.audit.inspect", lambda url, jid: {
        "url": url, "title": "Portfolio", "flags": [], "counts": {}, "load_ms": 800})
    job_id = store.create_job("design_review", "https://example.org", "Elegant GSAP and 3D site")
    job = store.claim_job()
    engine.process(job)
    payload = store.get_job(job_id)["result"]
    names = {a["agent"] for a in payload["work_orders"]}
    assert {"creative_director", "visual_designer", "motion_designer",
            "responsive_engineer", "inspector"}.issubset(names)
    assert payload["design_spec"]["state"] == "design_work_order_only"


def test_security_blocks_private_ips(monkeypatch):
    import socket
    def resolve(host, port, type):
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("127.0.0.1", port))]
    monkeypatch.setattr(security.socket, "getaddrinfo", resolve)
    for url in ("http://127.0.0.1/", "http://localhost/", "http://example.org:8080/",
                "file:///etc/passwd", "http://user:pass@example.org/"):
        try:
            security.validate_public_url(url)
        except security.UnsafeTarget:
            pass
        else:
            raise AssertionError("Unsafe URL accepted: " + url)
    assert router.classify({"counts": {"page_errors": 1}})["category"] == "javascript"
    assert len(agents.registry()) >= 10


def test_concurrent_claims_are_exclusive(tmp_path, monkeypatch):
    monkeypatch.setenv("MEND_DB_PATH", str(tmp_path / "queue.db"))
    store.initialise()
    store.create_job("audit", "https://example.org")
    assert store.claim_job() is not None
    assert store.claim_job() is None
