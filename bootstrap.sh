#!/usr/bin/env bash
# Entry point for whisperx-tui. Ensures a usable Python is present, creates a
# dedicated venv for the app (kept separate from any other Python project),
# and installs the TUI's own dependencies into it.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="whisperx-tui"
APP_DIR="$HOME/Library/Application Support/$APP_NAME"
VENV_DIR="$APP_DIR/venv"
MIN_PYTHON_MINOR=10

log() { printf '%s\n' "$*" >&2; }

# Compares two "major.minor" version strings; returns 0 (true) if $1 >= $2.
version_ge() {
  local v1_major v1_minor v2_major v2_minor
  IFS=. read -r v1_major v1_minor _ <<<"$1"
  IFS=. read -r v2_major v2_minor _ <<<"$2"
  if (( v1_major > v2_major )); then return 0; fi
  if (( v1_major < v2_major )); then return 1; fi
  (( v1_minor >= v2_minor ))
}

# Looks for a python3 on PATH that meets the minimum version. Prints its path
# and returns 0 on success; returns 1 (no output) if none qualifies.
find_system_python() {
  if command -v python3 >/dev/null 2>&1; then
    local ver
    ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if version_ge "$ver" "3.$MIN_PYTHON_MINOR"; then
      command -v python3
      return 0
    fi
    log "Found python3 ($ver) but it's older than the required 3.$MIN_PYTHON_MINOR."
  fi
  return 1
}

# Installs Python via Homebrew. Deliberately does NOT auto-install Homebrew
# itself if it's missing -- that's a system-wide change invasive enough that
# it should be a manual, explicit step for the user, not silent.
install_python_via_brew() {
  if ! command -v brew >/dev/null 2>&1; then
    log "python3 (>=3.$MIN_PYTHON_MINOR) not found, and Homebrew isn't installed either."
    log "Install Homebrew first: https://brew.sh"
    log "Or install Python directly: https://www.python.org/downloads/macos/"
    exit 1
  fi
  log "python3 (>=3.$MIN_PYTHON_MINOR) not found. Installing via Homebrew..."
  brew install python@3.12
}

# Step 1: make sure a qualifying system python3 exists, installing one via
# Homebrew if needed. "|| true" keeps `set -e` from tripping on the expected
# failure case where no python3 is found yet.
SYSTEM_PYTHON="$(find_system_python || true)"
if [[ -z "$SYSTEM_PYTHON" ]]; then
  install_python_via_brew
  SYSTEM_PYTHON="$(find_system_python || true)"
  if [[ -z "$SYSTEM_PYTHON" ]]; then
    log "Python installation via Homebrew did not put a usable python3 on PATH. Aborting."
    exit 1
  fi
fi

log "Using system Python: $SYSTEM_PYTHON"

# Step 2: create the app's dedicated venv if it doesn't exist yet. Isolated
# from other projects so whisperx's heavy, version-pinned deps (torch, etc.)
# never conflict with anything else on the system.
FRESH_VENV=0
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  log "Creating venv at $VENV_DIR"
  mkdir -p "$APP_DIR"
  "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
  FRESH_VENV=1
fi

# Step 3: only install into a freshly created venv -- reruns should be fast
# and skip straight past this once everything is already in place.
if [[ "$FRESH_VENV" -eq 1 ]]; then
  log "Installing TUI dependencies (textual, textual-fspicker)..."
  "$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
  "$VENV_DIR/bin/pip" install textual textual-fspicker
fi

log "Bootstrap complete. Launching whisperx-tui..."

# whisperx itself isn't installed here -- the app checks for it on startup
# and installs it (plus ffmpeg) via its own setup screen if missing.
cd "$SCRIPT_DIR"
exec "$VENV_DIR/bin/python" -m whisperx_tui.app
