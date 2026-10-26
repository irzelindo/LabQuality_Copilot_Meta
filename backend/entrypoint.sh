#!/bin/sh
set -eu
if [ "${LQ_SEED_DEMO:-false}" = "true" ]; then
    python -m app.bootstrap --demo
else
    python -m app.bootstrap
fi
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
