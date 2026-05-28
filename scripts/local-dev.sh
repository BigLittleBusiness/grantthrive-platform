#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [[ ! -d venv ]]; then
  ./setup.sh
fi

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

export FLASK_ENV="${FLASK_ENV:-development}"
export FLASK_APP="${FLASK_APP:-wsgi.py}"

source venv/bin/activate

flask db upgrade
exec flask run --host 127.0.0.1 --port 5000