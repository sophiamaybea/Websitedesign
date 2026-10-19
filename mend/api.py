"""Authenticated MEND API, designed for Base44 function calls and human approvals."""
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from typing import Literal
from . import agents, store
from .security import UnsafeTarget, validate_public_url

bearer = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.initialise()
    yield


app = FastAPI(title="MEND Backend", version="0.1.0", lifespan=lifespan,
              description="Website auditing, design work orders and verified repair memory.")


def authenticate(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    key = os.getenv("MEND_API_KEY", "")
    if len(key) < 24:
        raise HTTPException(503, "Server API key is not configured")
    if not credentials or not secrets.compare_digest(credentials.credentials, key):
        raise HTTPException(401, "Invalid API key", headers={"WWW-Authenticate": "Bearer"})
    return "operator"


class JobRequest(BaseModel):
    target_url: str = Field(min_length=10, max_length=2048)
    brief: str = Field(default="", max_length=3000)


class Approval(BaseModel):
    reviewer: str = Field(min_length=2, max_length=120)


class RecipeRequest(BaseModel):
    source_job: str = Field(min_length=32, max_length=40)
    symptom: str = Field(min_length=10, max_length=1000)
    environment: str = Field(min_length=3, max_length=1000)
    repair: str = Field(min_length=10, max_length=5000)
    verification: str = Field(min_length=10, max_length=3000)


@app.get("/health")
def health():
    return {"status": "ok", "service": "mend"}


@app.get("/v1/agents", dependencies=[Depends(authenticate)])
def get_agents():
    return {"agents": agents.registry()}


@app.post("/v1/audits", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(authenticate)])
def create_audit(request: JobRequest):
    try:
        validate_public_url(request.target_url)
    except UnsafeTarget as exc:
        raise HTTPException(422, str(exc))
    job_id = store.create_job("audit", request.target_url, request.brief)
    return {"job_id": job_id, "status": "queued", "action": "audit"}


@app.post("/v1/design-reviews", status_code=status.HTTP_202_ACCEPTED,
          dependencies=[Depends(authenticate)])
def create_design_review(request: JobRequest):
    try:
        validate_public_url(request.target_url)
    except UnsafeTarget as exc:
        raise HTTPException(422, str(exc))
    job_id = store.create_job("design_review", request.target_url, request.brief)
    return {"job_id": job_id, "status": "queued", "action": "design_review"}


@app.get("/v1/jobs/{job_id}", dependencies=[Depends(authenticate)])
def job_details(job_id: str):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@app.get("/v1/jobs/{job_id}/screenshots/{viewport}", dependencies=[Depends(authenticate)])
def screenshot(job_id: str, viewport: Literal["mobile", "desktop"]):
    if not store.get_job(job_id):
        raise HTTPException(404, "Job not found")
    root = Path(os.getenv("MEND_ARTIFACT_DIR", "artifacts"))
    file = root / (job_id + "-" + viewport + ".png")
    if not file.is_file():
        raise HTTPException(404, "No screenshot has been recorded")
    return FileResponse(file, media_type="image/png", headers={"Cache-Control": "no-store"})


@app.post("/v1/jobs/{job_id}/approve", dependencies=[Depends(authenticate)])
def approve(job_id: str, body: Approval):
    if not store.approve_job(job_id, body.reviewer):
        raise HTTPException(409, "Only existing proposals may be approved")
    return {"job_id": job_id, "status": "approved",
            "important": "Approval records a decision but does not run code or deploy."}


@app.post("/v1/recipes", dependencies=[Depends(authenticate)], status_code=201)
def record_verified_repair(body: RecipeRequest):
    job = store.get_job(body.source_job)
    if not job or job["state"] != "approved":
        raise HTTPException(409, "Source job must be approved by a human reviewer")
    recipe_id = store.add_recipe(body.symptom, body.environment, body.repair,
                                 body.verification, body.source_job, approved=True)
    return {"recipe_id": recipe_id, "verified": True}


@app.get("/v1/metrics", dependencies=[Depends(authenticate)])
def metrics():
    return store.stats()
