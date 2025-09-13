import os
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Any, Dict

from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel, Field
import redis

APP_TITLE = "Queuey API"
API_KEY = os.getenv("API_KEY", "dev")

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def get_redis() -> redis.Redis:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return redis.from_url(url, decode_responses=True)

r = get_redis()
app = FastAPI(title=APP_TITLE, version="0.1.0")

class JobCreate(BaseModel):
    type: str = Field(examples=["text.reverse", "math.square"])
    payload: Dict[str, Any] | None = Field(default_factory=dict)
    dedupe_key: Optional[str] = None
    max_attempts: int = 5

class JobId(BaseModel):
    job_id: str

@app.get("/healthz")
def healthz():
    try:
        r.ping()
        return {"status": "ok", "redis": "up"}
    except Exception as e:
        return {"status": "degraded", "error": repr(e)}

@app.post("/v1/jobs", response_model=JobId)
def create_job(body: JobCreate):
    # Optional idempotency by dedupe_key
    if body.dedupe_key:
        existing = r.get(f"dedupe:{body.dedupe_key}")
        if existing:
            return JobId(job_id=existing)

    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "type": body.type,
        "payload": body.payload or {},
        "dedupe_key": body.dedupe_key,
        "status": "queued",
        "attempts": 0,
        "max_attempts": max(1, int(body.max_attempts)),
        "created_at": now_iso(),
        "started_at": None,
        "finished_at": None,
        "last_error": None,
        "result": None,
    }

    pipe = r.pipeline()
    pipe.set(f"job:{job_id}", json.dumps(job))
    pipe.rpush("queue:default", json.dumps(job))
    if body.dedupe_key:
        # store mapping; TTL optional (e.g., 1 day) to avoid unbounded growth
        pipe.set(f"dedupe:{body.dedupe_key}", job_id)
        pipe.expire(f"dedupe:{body.dedupe_key}", 24 * 3600)
    pipe.execute()

    return JobId(job_id=job_id)

@app.get("/v1/jobs/{job_id}")
def get_job(job_id: str):
    raw = r.get(f"job:{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="job not found")
    return json.loads(raw)

@app.get("/v1/queues/metrics")
def queue_metrics():
    return {
        "queue_default_length": r.llen("queue:default"),
        "queue_dlq_length": r.llen("queue:dlq"),
    }

@app.post("/v1/replay-dlq")
def replay_dlq(limit: int = 100, x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")

    moved = 0
    for _ in range(max(0, int(limit))):
        raw = r.lpop("queue:dlq")
        if not raw:
            break
        # Reset state to queued and push back
        try:
            job = json.loads(raw)
            job["status"] = "queued"
            job["last_error"] = None
            r.set(f"job:{job['id']}", json.dumps(job))
            r.rpush("queue:default", json.dumps(job))
            moved += 1
        except Exception:
            # if malformed, skip
            continue

    return {"requeued": moved}
