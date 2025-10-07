# ETAguard

ETAguard monitors BLDR deliveries, tracks promised versus actual ETAs, and surfaces SLA breaches using PostgreSQL, n8n automations, and an optional FastAPI proxy. A lightweight text-triage model adds context by classifying delivery notes and highlighting likely delay causes.

## Table of contents

1. [System architecture](#system-architecture)
2. [Repository layout](#repository-layout)
3. [Configuration](#configuration)
4. [Quick start](#quick-start)
5. [Operational workflows](#operational-workflows)
6. [Delay note triage](#delay-note-triage)
7. [Database schema overview](#database-schema-overview)
8. [Developing locally without Docker](#developing-locally-without-docker)
9. [Testing](#testing)
10. [License](#license)

## System architecture

```
┌────────────┐     HTTP (10 min)     ┌───────────────┐
│ FastAPI    │ ─────────────────────▶│ n8n Poll &    │
│ proxy      │◀──────────────────────│ Alert          │
└─────▲──────┘    Slack alerts       └─────┬─────────┘
      │                                   │
      │ deliveries JSON                   │ daily cron
      │                                   ▼
┌─────┴───────────────┐           ┌───────────────┐
│ Upstream systems or │           │ n8n Daily SLA │
│ scraping client     │           │ Summary       │
└─────┬───────────────┘           └─────┬─────────┘
      │                                   │
      │                                   ▼
      │                       ┌────────────────────┐
      │                       │ PostgreSQL         │
      │                       │ deliveries / alerts│
      │                       │ delay_causes / SLA │
      │                       └────────────────────┘
      │                                   ▲
      │                                   │
      └───────── Delivery notes ──────────┘
```

The proxy normalizes delivery payloads, n8n orchestrates polling, alerting, and daily summaries, and Slack receives both real-time breach notifications and daily SLA reports. When delivery notes are present, an embedded text-triage model predicts likely delay causes that are persisted for analytics.
ETAguard monitors BLDR deliveries, tracks promised versus actual ETAs, and surfaces SLA breaches using n8n automations, PostgreSQL, and an optional FastAPI proxy.

## Repository layout

```
etaguard/
  infra/                 # Docker Compose stack (Postgres, proxy, n8n)
  service/               # FastAPI proxy + ML inference server
    app.py               # Delivery proxy endpoints
    ml_server.py         # /explain_delay API
    client.py            # Upstream fetch + normalization
    nlp_text_triage.py   # Model loader with on-demand training fallback
    schemas.py / _text   # Pydantic contracts for APIs
    requirements.txt     # FastAPI + ML dependencies
    Dockerfile
    tests/
      test_explain_delay.py
  ml/
    text/                # Training utilities for delay triage
      labels.py
      train_text_triage.py
      data/delivery_notes.sample.csv
  n8n/
    workflows/           # Exported JSON workflows
      etaguard_poll_and_alert.json
      etaguard_daily_summary.json
      etaguard_errors.json
    env.example          # Template for shared env vars
  db/
    migrations/
      001_init.sql       # deliveries / alerts / sla_history
      002_indexes.sql    # performance indexes
      004_delay_cause.sql# delay cause persistence
  README.md
```

## Configuration

Create a root `.env` by copying `n8n/env.example`:

```bash
cp n8n/env.example .env
```

Populate the following values before running the stack:

| Variable | Purpose |
| --- | --- |
| `POSTGRES_*` | Credentials for the shared database used by n8n and the proxy |
| `N8N_BASIC_AUTH_*` | Auth guard for the n8n editor UI |
| `SLACK_BOT_TOKEN`, `SLACK_SLA_CHANNEL` | Slack bot credentials for alerts and summaries |
| `SERVICE_URL` | Where n8n reaches the proxy (`http://service:8000` inside Docker) |
| `MYBLDR_AUTH_COOKIE` | Optional cookie/token for upstream delivery data |

## Quick start

1. **Launch the stack**
  infra/
    docker-compose.yaml
  service/
    app.py
    ml_server.py
    client.py
    nlp_text_triage.py
    schemas.py
    schemas_text.py
    requirements.txt
    Dockerfile
    model_store/
      text_triage.pkl
    tests/
      test_explain_delay.py
  ml/
    text/
      labels.py
      train_text_triage.py
      data/
        delivery_notes.sample.csv
    client.py
    schemas.py
    requirements.txt
    Dockerfile
  n8n/
    workflows/
      etaguard_poll_and_alert.json
      etaguard_daily_summary.json
      etaguard_errors.json
    env.example
  db/
    migrations/
      001_init.sql
      002_indexes.sql
      004_delay_cause.sql
  README.md
  .env
```

## Getting started

1. **Create environment file**

   ```bash
   cp n8n/env.example .env
   ```

   Update secrets like `SLACK_BOT_TOKEN`, `SLACK_SLA_CHANNEL`, and `MYBLDR_AUTH_COOKIE`.

2. **Launch the stack**

   ```bash
   cd infra
   docker compose up --build -d
   ```

   Exposed services:

   * n8n UI – <http://localhost:5678> (basic auth from `.env`)
   * FastAPI proxy – <http://localhost:8000/health>
   * ML endpoint – <http://localhost:8000/explain_delay>
   * PostgreSQL – `localhost:5432`

2. **Import workflows and wire credentials**

   * In n8n, import JSON exports from `n8n/workflows/`.
   * Edit Postgres, Slack, and HTTP Request nodes to reference credentials derived from `.env`.

3. **Run the smoke test**

   The stubbed proxy response includes a 40-minute late delivery with a gate-access note. After the poll workflow executes you should observe:

   * `deliveries` row for order `B12345` updated via UPSERT.
   * Slack alert summarizing the lateness, including `Cause (ML)` with confidence.
   * `alerts` entry recording the breach and `delay_causes` entry capturing the prediction.
   * Daily summary (07:30 America/Los_Angeles) reporting yard-level SLA metrics.

## Operational workflows

* **ETAguard — Poll & Alert** (cron every 10 minutes)
  * Fetches delivery data, computes lateness, and UPSERTs into `deliveries`.
  * When `note` text exists, calls `/explain_delay`, persists predictions, and enriches Slack alerts.
  * Posts alerts for delivered orders >30 minutes late and optional in-flight breaches.

* **ETAguard — Daily Summary** (07:30 local time)
  * Aggregates prior-day deliveries by yard.
  * Upserts SLA metrics into `sla_history` and publishes a Slack digest.

* **ETAguard — Errors**
  * Captures workflow exceptions, sends diagnostic Slack messages, and can dead-letter to Postgres.

## Delay note triage

The service exposes a minimal scikit-learn pipeline for classifying delivery notes into canonical delay causes:

* **Training:**
   Services:

   * n8n UI: [http://localhost:5678](http://localhost:5678) (basic auth from `.env`)
   * FastAPI proxy: [http://localhost:8000/health](http://localhost:8000/health)
   * PostgreSQL: `localhost:5432`

3. **Import n8n workflows**

   * In the n8n UI, import the JSON files in `n8n/workflows/`.
   * Update node credentials (Postgres, Slack, HTTP Request) to use your environment secrets.

4. **Smoke test**

   The default proxy stub returns a sample delivery with a 40 minute delay. After the poll workflow runs you should see:

   * A row in `deliveries` for order `B12345`.
   * A Slack alert in `SLACK_SLA_CHANNEL` for the late delivery.
   * A row in `alerts` for the breach.
   * When the delivery note is present, a Slack alert line with the ML-predicted cause and a `delay_causes` entry.
   * A daily summary posted at 07:30 America/Los_Angeles.

## Delay note triage (TF-IDF + Logistic Regression)

* The FastAPI service now exposes `POST /explain_delay` which returns a predicted delay label, confidence, model version, and top-3 probabilities for any delivery note.
* Train or update the lightweight scikit-learn model with:

  ```bash
  python -m ml.text.train_text_triage --csv ml/text/data/delivery_notes.sample.csv
  ```

  The script prints a classification report, then saves `service/model_store/text_triage.pkl` containing the TF-IDF + Logistic Regression pipeline.

* **Inference:**
  * `POST /explain_delay` accepts `{"order_id": "...", "note": "..."}`.
  * Responses include the top label, confidence, model version, and top-3 breakdown.
  * If the serialized model is missing (fresh clone), the loader trains from the bundled sample CSV on demand so the endpoint remains available.

* **Workflow integration:**
  * Predictions are recorded in `delay_causes` for analytics and surfaced in Slack alerts alongside lateness details.

## Database schema overview

| Table | Purpose |
| --- | --- |
| `deliveries` | Current view of each tracked order, including promised/actual ETA, status, and `last_seen` heartbeat |
| `alerts` | Historical alert events containing lateness thresholds and reasons |
| `sla_history` | Daily yard-level aggregates (total, on-time, >15 min, >30 min, p95 lateness) |
| `delay_causes` | Model predictions for notes with confidence, versioning, and excerpts |

Indexes (see `002_indexes.sql` and `004_delay_cause.sql`) keep polling and reporting queries performant.

## Developing locally without Docker

1. **Run the proxy + ML server**
  The script will emit a `service/model_store/text_triage.pkl` artifact used by the API.
* n8n workflow “ETAguard — Poll & Alert” calls the endpoint for deliveries that include a note, stores the result in the `delay_causes` table, and enriches Slack alerts with `Cause (ML): <label> (<confidence>%)`.

   * A daily summary posted at 07:30 America/Los_Angeles.

## Development notes

* The proxy service is optional if you have a direct API; point `SERVICE_URL` to the appropriate endpoint returning the same schema.
* `db/migrations` are mounted into PostgreSQL via Docker Compose and run automatically.
* The `sla_history` table is updated by the daily summary workflow using an UPSERT.
* An error workflow posts execution failures into Slack.

## Testing locally without Docker

1. Install dependencies for the proxy service:

   ```bash
   cd service
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app:app --reload
   ```

   `ml_server.py` is imported by `app.py`, so the `/explain_delay` endpoint is available automatically.

2. **Database setup** – Point a local Postgres instance at the migrations in `db/migrations/`.

3. **n8n desktop / self-hosted** – Configure it to connect to the same database and import the workflows.

## Testing

Run the FastAPI smoke tests (requires dependencies from `service/requirements.txt`):

```bash
pytest service/tests -q
```
2. Ensure you have PostgreSQL available and apply the SQL migrations.
3. Run the n8n workflows using the desktop app or a local n8n instance pointed at the same database.

## License

MIT
