# Queuey — A Minimal Distributed Job Queue (FastAPI + Redis + Docker)

Queuey is a small, production-shaped background jobs system:
- **FastAPI** service exposes REST endpoints to submit and track jobs.
- **Worker** pulls from Redis to process jobs concurrently.
- **Retries with exponential backoff**, **dead-letter queue (DLQ)**, and **idempotency (optional)** included.
- **Dockerized** for local dev; ready to deploy to AWS ECS later.

> First milestone (MVP): runs with Docker Compose, no external DB required.

---

## Quickstart

**Prereqs:** Docker Desktop (or Docker Engine), `curl`

```bash
# 1) Build and run
docker compose up --build

# 2) In another terminal: submit a job
curl -s -X POST http://localhost:8000/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"type":"text.reverse","payload":{"text":"hello world"}}' | jq

# 3) Check job status/result
curl -s http://localhost:8000/v1/jobs/<job_id> | jq



**Metrics (basic):**
```bash
curl -s http://localhost:8000/v1/queues/metrics | jq
# => queue_default_length, queue_dlq_length
```
<img width="571" height="279" alt="截圖 2025-09-13 16 37 51" src="https://github.com/user-attachments/assets/4ce188be-b3ca-44e0-8cd1-81334c926af7" /> 


**Admin (replay DLQ):**
```bash
curl -s -X POST "http://localhost:8000/v1/replay-dlq?limit=100" -H "x-api-key: dev" | jq
```

Stop containers with `Ctrl+C` and `docker compose down`.

---

## API Summary

- `POST /v1/jobs` → Create a job. Body:
  ```json
  {"type":"text.reverse","payload":{"text":"hello"},"dedupe_key":"file123:200x200"}
  ```
  Returns: `{"job_id":"..."}`

- `GET /v1/jobs/{id}` → Get job status/result

- `GET /v1/queues/metrics` → Queue lengths

- `POST /v1/replay-dlq?limit=N` → Requeue items from DLQ (header `x-api-key` required)

---

## Repo Layout

```
queuey/
  api/
    main.py          # FastAPI app
  worker/
    worker.py        # Worker loop
  Dockerfile         # Shared image for API and worker
  docker-compose.yml # Local dev stack
  requirements.txt   # Python deps
  README.md
```

---

## Next Steps

- Add Prometheus + Grafana for metrics.
- Add visibility timeout & lease renewal.
- Add Postgres for durable job metadata.
- Deploy to AWS ECS Fargate (API + workers), ElastiCache (Redis).
- Write unit/integration tests + GitHub Actions CI.

---

## License

MIT
