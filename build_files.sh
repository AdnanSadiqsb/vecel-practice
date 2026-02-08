#!/usr/bin/env bash
set -euo pipefail

# Use python3.12 if available, otherwise fallback to python3
PY=python3.12
if ! command -v "$PY" >/dev/null 2>&1; then
	PY=python3
fi

# Create an isolated virtual environment to avoid modifying system-managed Python
$PY -m venv .venv
. .venv/bin/activate

# Install dependencies into the venv and collect static files
pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput