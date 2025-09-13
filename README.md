# Queuey — A Minimal Distributed Job Queue (FastAPI + Redis + Docker)

Queuey is a small, production-shaped background jobs system:
- **FastAPI** service exposes REST endpoints to submit and track jobs.
- **Worker** pulls from Redis to process jobs concurrently.
- **Retries with exponential backoff**, **dead-letter queue (DLQ)**, and **idempotency (optional)** included.
- **Watchdog**：implement **Visibility Timeout** to avoid job missing
- **Observability**：integrete Prometheus/Grafana（Metrics & Dashboard）
- **Dockerized** for local dev; ready to deploy to AWS ECS later.
- **Load Test**：k6 pressure test

> First milestone (MVP): runs with Docker Compose, no external DB required.

---

## Outline


---

## Structure View

```mermaid
flowchart LR
  C[Client] -->|POST /v1/jobs| A[API (FastAPI)]
  A -->|enqueue| Q[(Redis queues)]
  subgraph Workers
    W1[Worker 1]
    W2[Worker 2]
    WD[Watchdog]
  end
  Q -->|BLPOP high->default->low| W1
  Q -->|BLPOP high->default->low| W2
  W1 -->|update status/result| A
  W2 -->|update status/result| A
  W1 -->|on max retries| DLQ[(queue:dlq)]
  WD -->|requeue expired leases| Q
```

---

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
