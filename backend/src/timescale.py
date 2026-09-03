"""
TimescaleDB Provisioning (best-effort, idempotent)
--------------------------------------------------
Upgrades the ``readings`` table to a TimescaleDB *hypertable* partitioned on
``recorded_at`` so the time-series ingestion path scales with chunking,
compression and continuous aggregates — without touching the ORM model.

The migration is deliberately **best-effort**: on a stock PostGIS container
(no TimescaleDB), every step fails closed with a warning and the application
keeps running on the plain relational table. This lets CI and local dev use the
standard PostGIS image while production uses the TimescaleDB+PostGIS image.

Run manually:   python -m src.timescale
Auto-applied:   on FastAPI startup (see src/main.py lifespan)
"""

import os

from sqlalchemy import text
from sqlalchemy.orm import Session

TSDB_RETENTION_DAYS = os.getenv("TSDB_RETENTION_DAYS", "180")


def _enable_extension(db: Session) -> bool:
    try:
        db.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"⚠️ TimescaleDB extension unavailable: {e}", flush=True)
        return False


def _create_hypertable(db: Session) -> bool:
    try:
        already_hypertable = db.execute(
            text(
                "SELECT (EXISTS (SELECT 1 FROM timescaledb_information.hypertables "
                "WHERE hypertable_name = 'readings'))"
            )
        ).scalar()
        if not already_hypertable:
            db.execute(
                text(
                    "SELECT create_hypertable('readings', 'recorded_at', "
                    "if_not_exists => TRUE, migrate_data => TRUE)"
                )
            )
        db.commit()
        print("✅ readings is a TimescaleDB hypertable (chunked on recorded_at).", flush=True)
        return True
    except Exception as e:
        db.rollback()
        print(f"⚠️ Hypertable creation skipped: {e}", flush=True)
        return False


def _create_continuous_aggregate(db: Session) -> bool:
    try:
        db.execute(
            text(
                "CREATE MATERIALIZED VIEW IF NOT EXISTS readings_minute "
                "WITH (timescaledb.continuous) AS "
                "SELECT sensor_id, time_bucket('1 minute', recorded_at) AS bucket, "
                "count(*) AS n, max(value) AS peak "
                "FROM readings GROUP BY sensor_id, bucket WITH NO DATA"
            )
        )
        db.commit()
        try:
            db.execute(
                text(
                    "SELECT add_continuous_aggregate_policy('readings_minute', "
                    "start_offset => INTERVAL '3 hours', "
                    "end_offset => INTERVAL '10 seconds', "
                    "schedule_interval => INTERVAL '1 minute')"
                )
            )
            db.commit()
        except Exception:
            db.rollback()  # policy already present or not yet refreshable
        print("✅ Continuous aggregate readings_minute created.", flush=True)
        return True
    except Exception as e:
        db.rollback()
        print(f"⚠️ Continuous aggregate skipped: {e}", flush=True)
        return False


def _apply_compression(db: Session) -> None:
    try:
        # Newer TimescaleDB (2.13+/3.x) requires columnstore on the hypertable
        # before a columnstore compression policy can be added.
        db.execute(text("ALTER TABLE readings SET (timescaledb.columnstore = true)"))
        db.commit()
    except Exception as e:
        db.rollback()
        if "already" not in str(e).lower():
            print(f"⚠️ Columnstore enable skipped: {e}", flush=True)
    try:
        db.execute(text("SELECT add_compression_policy('readings', INTERVAL '1 day')"))
        db.commit()
    except Exception as e:
        db.rollback()
        if "already exists" not in str(e).lower():
            print(f"⚠️ Compression policy skipped: {e}", flush=True)


def _apply_retention(db: Session) -> bool:
    try:
        db.execute(
            text(
                "SELECT add_retention_policy('readings', "
                f"INTERVAL '{TSDB_RETENTION_DAYS} days')"
            )
        )
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        if "already exists" in str(e).lower():
            return True
        print(f"⚠️ Retention policy skipped: {e}", flush=True)
        return False


def _run_extension_step(db: Session, report: dict) -> bool:
    """Step 1: Enable TimescaleDB extension."""
    if not _enable_extension(db):
        return False
    report["timescaledb"] = True
    return True

def _add_telemetry_columns(db: Session) -> None:
    """Step 1.5: Add Grafana telemetry columns to the hypertable."""
    try:
        db.execute(text("ALTER TABLE readings ADD COLUMN IF NOT EXISTS latency_ms INTEGER"))
        db.execute(text("ALTER TABLE readings ADD COLUMN IF NOT EXISTS free_heap INTEGER"))
        db.execute(text("ALTER TABLE readings ADD COLUMN IF NOT EXISTS rssi INTEGER"))
        db.execute(text("ALTER TABLE readings ADD COLUMN IF NOT EXISTS gnss_satellites INTEGER"))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"⚠️ Failed to add telemetry columns: {e}", flush=True)


def _run_hypertable_step(db: Session, report: dict) -> None:
    """Step 2: Create hypertable."""
    report["hypertable"] = _create_hypertable(db)


def _run_aggregate_step(db: Session, report: dict) -> None:
    """Step 3: Create continuous aggregate."""
    report["aggregate"] = _create_continuous_aggregate(db)


def _run_compression_retention_steps(db: Session, report: dict) -> None:
    """Step 4: Apply compression and retention policies."""
    _apply_compression(db)
    report["retention"] = _apply_retention(db)
    if report["retention"]:
        print(f"✅ Retention policy set to {TSDB_RETENTION_DAYS} days.", flush=True)


def apply_timescale(db: Session) -> dict:
    """Apply TimescaleDB DDL where possible. Returns a per-step report dict.

    Steps are isolated: a failure in any step never blocks the others nor the
    application startup.
    """
    report = {
        "timescaledb": False,
        "hypertable": False,
        "aggregate": False,
        "retention": False,
    }

    if not _run_extension_step(db, report):
        return report

    _add_telemetry_columns(db)
    _run_hypertable_step(db, report)
    _run_aggregate_step(db, report)
    _run_compression_retention_steps(db, report)

    return report


def run_migration() -> dict:
    from src.database import SessionLocal
    with SessionLocal() as db:
        report = apply_timescale(db)
    print(f"📋 TimescaleDB migration report: {report}", flush=True)
    return report


if __name__ == "__main__":
    run_migration()
