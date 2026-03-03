#!/usr/bin/env bash
# =============================================================================
# GrantThrive Backend — Automated Setup Script
# =============================================================================
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
#
# What this script does:
#   1. Checks all system prerequisites (Python 3.11+)
#   2. Creates and activates a Python virtual environment
#   3. Installs all required Python packages
#   4. Creates the .env file with a securely generated SECRET_KEY
#   5. Creates all database tables
#   6. Confirms the server starts correctly and exits
#
# After running this script, start the server at any time with:
#   source venv/bin/activate && flask run
# =============================================================================

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Colour

# ── Helpers ───────────────────────────────────────────────────────────────────
ok()   { echo -e "${GREEN}  ✔  ${NC}$1"; }
info() { echo -e "${YELLOW}  →  ${NC}$1"; }
fail() { echo -e "${RED}  ✘  ERROR: ${NC}$1"; exit 1; }
hr()   { echo -e "\n${BOLD}──────────────────────────────────────────────────${NC}"; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  GrantThrive Backend — Setup${NC}"
echo -e "  $(date '+%Y-%m-%d %H:%M:%S')"
hr

# ── Step 1: Prerequisites ─────────────────────────────────────────────────────
info "Checking prerequisites..."

# Python version check (requires 3.11+)
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
        fail "Python 3.11+ is required. Found Python ${PYTHON_VERSION}. Please upgrade."
    fi
    ok "Python ${PYTHON_VERSION} found"
else
    fail "Python 3 is not installed. Please install Python 3.11+ and re-run this script."
fi

# pip check
if ! python3 -m pip --version &>/dev/null; then
    fail "pip is not available. Please install pip and re-run this script."
fi
ok "pip available"

hr

# ── Step 2: Virtual Environment ───────────────────────────────────────────────
info "Setting up Python virtual environment..."

if [ -d "venv" ]; then
    info "Existing virtual environment found — skipping creation."
else
    python3 -m venv venv
    ok "Virtual environment created at ./venv"
fi

# Activate
# shellcheck disable=SC1091
source venv/bin/activate
ok "Virtual environment activated"

hr

# ── Step 3: Install Dependencies ──────────────────────────────────────────────
info "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt --quiet
ok "All dependencies installed"

hr

# ── Step 4: Environment File ──────────────────────────────────────────────────
info "Configuring environment..."

if [ -f ".env" ]; then
    info ".env file already exists — skipping creation. Edit it manually if needed."
else
    if [ ! -f ".env.example" ]; then
        fail ".env.example not found. Cannot create .env. Please check the repository."
    fi

    cp .env.example .env

    # Generate a cryptographically secure SECRET_KEY
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    # Inject the generated key into .env
    # Works on both Linux (sed -i) and macOS (sed -i '')
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|SECRET_KEY=\"\"|SECRET_KEY=\"${SECRET_KEY}\"|" .env
        sed -i '' "s|SECRET_KEY=|SECRET_KEY=${SECRET_KEY}|" .env
    else
        sed -i "s|SECRET_KEY=\"\"|SECRET_KEY=\"${SECRET_KEY}\"|" .env
    fi

    ok ".env created with a generated SECRET_KEY"
    echo ""
    echo -e "  ${YELLOW}NOTE:${NC} Review .env and update MAIL_* settings before sending emails."
    echo -e "  ${YELLOW}NOTE:${NC} For production, set DATABASE_URL to your PostgreSQL connection string."
fi

# Export environment variables for the remainder of this script
set -a
# shellcheck disable=SC1091
source .env
set +a

# Ensure FLASK_ENV is set for this session
export FLASK_ENV="${FLASK_ENV:-development}"

hr

# ── Step 5: Database Setup ────────────────────────────────────────────────────
info "Creating database tables..."

python3 - <<'PYEOF'
import sys
try:
    from app import create_app, db
    from sqlalchemy import inspect

    app = create_app()
    with app.app_context():
        db.create_all()
        tables = inspect(db.engine).get_table_names()
        print(f"  Created {len(tables)} tables: {', '.join(sorted(tables))}")
except Exception as e:
    print(f"  ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

ok "Database tables created"

hr

# ── Step 6: Smoke Test ────────────────────────────────────────────────────────
info "Running a quick smoke test to verify the app starts..."

# Start the server in the background on port 5001 (avoids conflict with any running instance)
flask run --host=127.0.0.1 --port=5001 &>/tmp/grantthrive_setup_server.log &
SERVER_PID=$!

# Give it up to 5 seconds to start
STARTED=false
for i in {1..5}; do
    sleep 1
    if curl -s http://127.0.0.1:5001/api/health &>/dev/null; then
        STARTED=true
        break
    fi
done

# Stop the test server
kill "$SERVER_PID" 2>/dev/null || true
wait "$SERVER_PID" 2>/dev/null || true

if [ "$STARTED" = true ]; then
    ok "Server smoke test passed — /api/health responded successfully"
else
    echo ""
    echo -e "${YELLOW}  ⚠  Smoke test could not reach the server within 5 seconds.${NC}"
    echo -e "     This may be a timing issue. Check /tmp/grantthrive_setup_server.log for details."
    echo -e "     Setup will continue — try running the server manually."
fi

hr

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}  Setup complete!${NC}"
echo ""
echo -e "  To start the development server, run:"
echo -e ""
echo -e "    ${BOLD}source venv/bin/activate && flask run${NC}"
echo ""
echo -e "  The API will be available at:  ${BOLD}http://localhost:5000${NC}"
echo -e "  Health check endpoint:         ${BOLD}http://localhost:5000/api/health${NC}"
echo ""
