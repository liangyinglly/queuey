# Queuey — A Distributed Job Queue System (FastAPI + Redis + Docker)

[![CI](https://github.com/liangyinglly/queuey/actions/workflows/ci.yml/badge.svg)](../../actions)

Queuey is a **minimal but complete distributed job queue system**, inspired by tools like Celery or Sidekiq.  
It demonstrates **distributed systems principles** such as decoupling, fault tolerance, retries, and scalability, while being easy to run locally with Docker.

---

## Features
- **FastAPI REST API**: Submit and track background jobs
- **Worker service**: Executes jobs with retries, exponential backoff, and a Dead Letter Queue (DLQ)
- **Watchdog service**: Implements **visibility timeout** to prevent job loss if workers crash
- **Priority Queues**: High / Default / Low priority scheduling
- **Observability**: Can expose metrics for Prometheus + Grafana dashboards
- **Load testing**: k6 scripts to validate throughput and latency
- **Docker Compose**: Run the full system with a single command
- **CI/CD**: GitHub Actions workflow with automated smoke tests

---

## Architecture

```mermaid
flowchart LR
  C[Client]
  A[API]
  Q[(Redis)]
  W1[Worker1]
  W2[Worker2]
  WD[Watchdog]
  D[(DLQ)]

  C -->|submit job| A
  A -->|enqueue| Q
  Q -->|pull high then default then low| W1
  Q -->|pull high then default then low| W2
  W1 -->|update status| A
  W2 -->|update status| A
  W1 -->|max retries| D
  WD -->|requeue expired| Q
```
- The API, Workers, and Redis are loosely coupled (can scale independently).
- Workers can be horizontally scaled (run N workers to increase throughput).
- Reliability is achieved through retries, DLQ, and watchdog lease requeueing.

---
## Prerequisites: Docker / Docker Compose
<img width="1142" height="558" alt="image" src="https://github.com/user-attachments/assets/712aea95-c8d4-451a-950f-afa32efc9ed4" />

---
## Quickstart
1. Clone and start
```
git clone https://github.com/<your-username>/queuey.git
cd queuey
docker compose up --build
```
2. Submit a job
```
curl -X POST http://localhost:8000/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"type":"text.reverse","payload":{"text":"hello"}}'
```
  Response:
  ```
  {"job_id": "e9530532-3dcb-4c39-82c3-22ea2e2b1612"}
  ```
3. Check job status
```
curl http://localhost:8000/v1/jobs/<job_id>
```

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

## Reliability

- Retries with exponential backoff: failed jobs retried with 2^k + jitter seconds
- Dead Letter Queue (DLQ): jobs exceeding max attempts go to DLQ
- Visibility Timeout: watchdog requeues jobs if workers crash
- Idempotency: dedupe_key prevents duplicate side effects
- Graceful shutdown: workers finish current jobs before exit

---

## Priority Queues

Jobs can be submitted with priority.
Workers always consume high > default > low.
```
curl -X POST http://localhost:8000/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"type":"text.reverse","payload":{"text":"LOW priority"},"priority":"low"}'
```
```
curl -X POST http://localhost:8000/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"type":"text.reverse","payload":{"text":"HIGH priority"},"priority":"high"}'
```
<img width="2048" height="411" alt="image" src="https://github.com/user-attachments/assets/8bd12822-83cd-4bbe-aee0-d747595b4864" />

---

## Observability
Supports Prometheus + Grafana dashboards.

Metrics to expose:

- `queue_depth{queue="high|default|low|dlq"}`

- `jobs_processed_total{status="success|failure"}`

- `job_latency_seconds` histogram

Use `docker-compose.override.yml` to run Prometheus (9090) and Grafana (3000).

---

## Load Testing
k6 script included under `load/k6-submit.js.`
```
brew install k6   # macOS
k6 run load/k6-submit.js
```
Observe:
- Success rate (>99%)
- Latency (p95 ideally <2s with 5 workers @100RPS)
- Scaling behavior with more workers

---
## SLA/SLI Targets
- Job success rate ≥ 99.5%
- End-to-end latency (p95) < 2s under load
- API availability ≥ 99.9%
  
---
## Development & CI
- Local dev: `docker compose up --build`
- Logs: `docker compose logs -f worker`
- Tests: `pytest`
- CI: GitHub Actions (`.github/workflows/ci.yml`) runs smoke tests
- Agile tracking: GitHub Project Board with Issues linked to PRs

---
## Roadmap
- Full Prometheus metrics in API/Worker (/metrics)
- Pluggable job types (image resize, OCR, webhooks)
- Scheduled jobs (Cron support)
- Web UI for job browsing and DLQ replay
- Cloud deployment: AWS ECS + RDS + ElastiCache (Terraform)

---
## Why this project?
This project is a portfolio-grade demonstration of distributed systems engineering:
- Scalability: add workers to process more jobs
- Reliability: retries, DLQ, watchdog
- Prioritization: handle critical jobs first
- Observability: metrics and dashboards
- DevOps practices: CI/CD, Docker, Agile workflows

## License

MIT
