#!/usr/bin/env bash
# =============================================================================
# GrantThrive — Rollback Script
# =============================================================================
# Rolls back either the frontend or backend (or both) to the previous release.
# Run this on the EC2 server when a deployment needs to be undone.
#
# Usage:
#   ./rollback.sh              # rolls back both frontend and backend
#   ./rollback.sh frontend     # rolls back frontend only
#   ./rollback.sh backend      # rolls back backend only
#   ./rollback.sh list         # lists available releases for both
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

FRONTEND_RELEASES="/var/www/grantthrive/releases"
FRONTEND_CURRENT="/var/www/grantthrive/current"
BACKEND_RELEASES="/srv/grantthrive/releases"
BACKEND_CURRENT="/srv/grantthrive/current"

list_releases() {
    local dir=$1
    local label=$2
    echo ""
    info "$label releases (newest first):"
    if ls -1dt "$dir"/*/ 2>/dev/null | head -10; then
        :
    else
        warn "  No releases found in $dir"
    fi
}

rollback_frontend() {
    info "Rolling back frontend..."
    local releases
    releases=$(ls -1dt "$FRONTEND_RELEASES"/*/ 2>/dev/null) || error "No frontend releases found."

    local current_release
    current_release=$(readlink -f "$FRONTEND_CURRENT" 2>/dev/null) || error "No current frontend symlink found."

    local previous_release
    previous_release=$(echo "$releases" | grep -v "^${current_release}$" | head -1) \
        || error "No previous frontend release to roll back to."

    warn "Current:  $current_release"
    info "Rolling back to: $previous_release"

    ln -sfn "$previous_release" "$FRONTEND_CURRENT"
    sudo systemctl reload nginx

    info "Frontend rollback complete. Active: $previous_release"
}

rollback_backend() {
    info "Rolling back backend..."
    local releases
    releases=$(ls -1dt "$BACKEND_RELEASES"/*/ 2>/dev/null) || error "No backend releases found."

    local current_release
    current_release=$(readlink -f "$BACKEND_CURRENT" 2>/dev/null) || error "No current backend symlink found."

    local previous_release
    previous_release=$(echo "$releases" | grep -v "^${current_release}$" | head -1) \
        || error "No previous backend release to roll back to."

    warn "Current:  $current_release"
    info "Rolling back to: $previous_release"

    ln -sfn "$previous_release" "$BACKEND_CURRENT"
    sudo systemctl restart grantthrive-backend
    sleep 3
    sudo systemctl is-active grantthrive-backend \
        && info "Backend rollback complete. Active: $previous_release" \
        || error "Backend failed to start after rollback. Check: journalctl -u grantthrive-backend -n 50"
}

TARGET="${1:-both}"

case "$TARGET" in
    list)
        list_releases "$FRONTEND_RELEASES" "Frontend"
        list_releases "$BACKEND_RELEASES"  "Backend"
        ;;
    frontend)
        rollback_frontend
        ;;
    backend)
        rollback_backend
        ;;
    both)
        rollback_frontend
        rollback_backend
        ;;
    *)
        error "Unknown target: $TARGET. Use: frontend | backend | both | list"
        ;;
esac
