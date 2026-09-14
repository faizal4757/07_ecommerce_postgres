CREATE SCHEMA IF NOT EXISTS ops;

CREATE TABLE IF NOT EXISTS ops.simulation_runs (
    run_id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    orders_created INTEGER NOT NULL DEFAULT 0,
    payments_created INTEGER NOT NULL DEFAULT 0,
    orders_updated INTEGER NOT NULL DEFAULT 0,
    reviews_created INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS ops.rejected_records (
    rejected_record_id BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES ops.simulation_runs(run_id) ON DELETE SET NULL,
    source_table VARCHAR(100) NOT NULL,
    record_key VARCHAR(255),
    reason TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_simulation_runs_started_at
    ON ops.simulation_runs(started_at DESC);

CREATE INDEX IF NOT EXISTS idx_rejected_records_run_id
    ON ops.rejected_records(run_id);

CREATE INDEX IF NOT EXISTS idx_rejected_records_created_at
    ON ops.rejected_records(created_at DESC);