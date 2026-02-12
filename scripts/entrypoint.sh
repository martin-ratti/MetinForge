#!/bin/bash
# ─────────────────────────────────────────────
# MetinForge — Docker Entrypoint
# Waits for MySQL, initializes the DB schema,
# seeds data if empty, and starts the app.
# ─────────────────────────────────────────────

set -e

# ── Wait for MySQL to accept connections ─────
echo "[MetinForge] Waiting for MySQL..."
MAX_RETRIES=30
RETRY=0
until python -c "
from app.utils.config import Config
from sqlalchemy import create_engine, text
engine = create_engine(Config.get_db_url())
with engine.connect() as c:
    c.execute(text('SELECT 1'))
engine.dispose()
print('OK')
" 2>/dev/null; do
    RETRY=$((RETRY + 1))
    if [ $RETRY -ge $MAX_RETRIES ]; then
        echo "[MetinForge] ERROR: MySQL not available after ${MAX_RETRIES} retries."
        exit 1
    fi
    echo "[MetinForge] MySQL not ready (attempt $RETRY/$MAX_RETRIES), waiting 2s..."
    sleep 2
done
echo "[MetinForge] MySQL is ready."

# ── Create tables + seed in a SINGLE process ─
# This avoids connection pool leaks between steps.
echo "[MetinForge] Initializing database..."
python -c "
from app.utils.config import Config
from app.domain.models import Base
from sqlalchemy import create_engine, inspect, text

engine = create_engine(Config.get_db_url())
inspector = inspect(engine)
existing = inspector.get_table_names()

if not existing:
    print('[MetinForge] No tables found — creating schema + seeding...')
    Base.metadata.create_all(engine)
    print('[MetinForge] Schema created.')
    engine.dispose()
    # Run seeder in clean state
    from app.utils.seed_data import seed
    seed()
    print('[MetinForge] Seed completed.')
else:
    with engine.connect() as conn:
        count = conn.execute(text('SELECT COUNT(*) FROM servers')).scalar()
    if count == 0:
        print('[MetinForge] Tables exist but empty — seeding...')
        engine.dispose()
        from app.utils.seed_data import seed
        seed()
        print('[MetinForge] Seed completed.')
    else:
        print(f'[MetinForge] Found {len(existing)} tables, {count} servers — ready.')
    engine.dispose()

print('[MetinForge] Database initialization complete.')
"

# ── Start the application ────────────────────
echo "[MetinForge] Starting application..."
exec python main.py
