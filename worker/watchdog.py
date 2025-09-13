# worker/watchdog.py
import os, json, time, redis

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)

def run():
    print("[watchdog] start")
    while True:
        for key in r.scan_iter("lease:*"): #scan all leases
            if not r.exists(key):  # lease out of time
                job_id = key.split(":", 1)[1]
                raw = r.get(f"job:{job_id}") #check job status
                if not raw:
                    continue
                job = json.loads(raw)
                if job.get("status") == "running":
                    # return to queue
                    job["status"] = "queued"
                    r.set(f"job:{job_id}", json.dumps(job))
                    r.rpush("queue:default", json.dumps(job))
                    print(f"[watchdog] requeued {job_id} (lease expired)")
        time.sleep(5)

if __name__ == "__main__":
    run()