# Olist PostgreSQL Operational Source System

This repository implements a minimal operational PostgreSQL source system for the Olist e-commerce dataset. It is intentionally separate from the sibling platform repo and includes only the core source-system pieces: PostgreSQL, a schema, one-time Olist seed load, and a simple daily simulator.

## Architecture

Olist CSV -> PostgreSQL -> later S3 / Databricks Bronze -> Silver -> Gold

The downstream extraction pipeline is intentionally not implemented yet.

## Docker

Create a local .env file from .env.example before starting PostgreSQL.

```bash
docker compose up -d
```

Connection details:
- Host: localhost
- Port: 5432
- Database: olist
- Username: from .env
- Password: from .env

DBeaver settings:
- Driver: PostgreSQL
- Host: localhost
- Port: 5432
- Database: olist
- Username: from .env
- Password: from .env
- SSL: Disable

## Schema

The init/001_schema.sql script creates the olist schema and the required tables:
- olist.customers
- olist.orders
- olist.products
- olist.sellers
- olist.order_items
- olist.order_payments
- olist.order_reviews
- olist.geolocation
- olist.category_translation
- olist.seed_state

These tables include created_at and updated_at so the project remains ready for future incremental extraction.

## Seed

The seed script reads the raw Olist CSVs from the sibling repo and inserts the canonical data into PostgreSQL.

```bash
python scripts/seed.py
```

It uses Python's built-in csv module and psycopg with idempotent insert/upsert logic so rerunning it does not blindly duplicate rows.

## Simulator

The simulator creates a simple batch of daily operational activity.

```bash
python scripts/simulate.py
```

It creates:
- new orders
- order items
- payments
- some updates to existing orders
- occasional reviews
- minor realistic imperfection such as duplicate payment inserts, late updates, and missing optional values

## Requirements

```bash
pip install -r requirements.txt
```

Required packages:
- psycopg[binary]
- python-dotenv

## Validation

```bash
docker compose up -d
python scripts/seed.py
python scripts/simulate.py
```

The database should stay persistent and remain usable for DBeaver or SQL queries afterward.

SELECT * FROM olist.orders ORDER BY updated_at DESC LIMIT 20;
SELECT * FROM ops.simulation_runs ORDER BY started_at DESC LIMIT 20;
SELECT * FROM ops.rejected_records ORDER BY created_at DESC LIMIT 20;
```

In DBeaver you can inspect schemas and tables in the database navigator.

## What is intentionally deferred

This repo does not implement:

- Kafka or Debezium
- Kubernetes or cloud Postgres
- full application or FastAPI layer
- Terraform for local PostgreSQL
- 30-day retention logic
- file-based or event-driven CDC frameworks
- any expansion beyond the local source-system scope

## Assumptions

- The Olist CSV files are available in the sibling platform repository under `data/raw`.
- Local PostgreSQL is sufficient for development and data-source simulations.
- The implementation aims for a working source-system foundation rather than a production-grade distributed platform.
