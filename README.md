# Queuey — A Distributed Job Queue System (FastAPI + Redis + Docker)

[![CI](https://github.com/liangyinglly/queuey/actions/workflows/ci.yml/badge.svg)](../../actions)

Queuey is a **minimal but complete distributed job queue system**, inspired by tools like Celery or Sidekiq.  
It demonstrates **distributed systems principles** such as decoupling, fault tolerance, retries, and scalability, while being easy to run locally with Docker.

---

## ✨ Features
- **FastAPI REST API**: Submit and track background jobs
- **Worker service**: Executes jobs with retries, exponential backoff, and a Dead Letter Queue (DLQ)
- **Watchdog service**: Implements **visibility timeout** to prevent job loss if workers crash
- **Priority Queues**: High / Default / Low priority scheduling
- **Observability**: Can expose metrics for Prometheus + Grafana dashboards
- **Load testing**: k6 scripts to validate throughput and latency
- **Docker Compose**: Run the full system with a single command
- **CI/CD**: GitHub Actions workflow with automated smoke tests

---

## 📐 Architecture

```mermaid
  flowchart LR
  C[Client] -->|"POST /v1/jobs"| A[API (FastAPI)]
  A -->|"enqueue"| Q[(Redis Queues)]

  subgraph Workers
    W1[Worker 1]
    W2[Worker 2]
    WD[Watchdog]
  end

  Q -->|"BLPOP high→default→low"| W1
  Q -->|"BLPOP high→default→low"| W2
  W1 -->|"update status/result"| A
  W2 -->|"update status/result"| A
  W1 -->|"max retries reached"| DLQ[(queue:dlq)]
  WD -->|"requeue expired leases"| Q


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
