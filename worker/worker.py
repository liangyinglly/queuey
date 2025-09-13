import os
import json
import time
import signal
import random
from datetime import datetime, timezone

import redis

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_redis():
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return redis.from_url(url, decode_responses=True)

r = get_redis()
running = True

def handle_shutdown(signum, frame):
    global running
    print(f"[worker] received signal {signum}, shutting down gracefully...")
    running = False

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def process(job: dict):
    t = job.get("type")
    payload = job.get("payload") or {}
    # Example tasks
    if t == "text.reverse":
        text = payload.get("text")
        if not isinstance(text, str):
            raise ValueError("payload.text must be a string")
        return text[::-1]
    elif t == "math.square":
        n = payload.get("n")
        if not isinstance(n, (int, float)):
            raise ValueError("payload.n must be a number")
        return n * n
    else:
        # Unknown task type -> fail
        raise ValueError(f"unknown job type: {t}")

def save_job(job: dict):
    r.set(f"job:{job['id']}", json.dumps(job))

def work_loop():
    print("[worker] starting...")
    while running:
        try:
            item = r.blpop("queue:default", timeout=2)
            if not item:
                continue

            _, raw = item
            job = json.loads(raw)

            # Transition to running
            job["status"] = "running"
            if not job.get("started_at"):
                job["started_at"] = now_iso()
            save_job(job)

            try:
                result = process(job)
                job["status"] = "succeeded"
                job["result"] = result
                job["finished_at"] = now_iso()
                save_job(job)
                print(f"[worker] job {job['id']} OK")
            except Exception as e:
                job["attempts"] = int(job.get("attempts", 0)) + 1
                job["last_error"] = repr(e)
                max_attempts = int(job.get("max_attempts", 5))

                if job["attempts"] < max_attempts:
                    # Exponential backoff with jitter (cap at 60s)
                    backoff = min(2 ** job["attempts"], 60) + random.random()
                    print(f"[worker] job {job['id']} failed: {e}; retry in {backoff:.1f}s")
                    save_job(job)
                    time.sleep(backoff)
                    # Requeue
                    job["status"] = "queued"
                    save_job(job)
                    r.rpush("queue:default", json.dumps(job))
                else:
                    job["status"] = "dead_letter"
                    job["finished_at"] = now_iso()
                    save_job(job)
                    r.rpush("queue:dlq", json.dumps(job))
                    print(f"[worker] job {job['id']} moved to DLQ after {job['attempts']} attempts")
        except Exception as loop_err:
            # Non-job-specific failure; brief pause to avoid tight loop
            print(f"[worker] loop error: {loop_err}")
            time.sleep(1.0)

    print("[worker] stopped.")

if __name__ == "__main__":
    work_loop()
