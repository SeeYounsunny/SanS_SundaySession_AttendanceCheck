#!/bin/bash
set -e
# Ensure deps in case builder skipped install (e.g. Nixpacks used instead of Dockerfile)
pip install -q --no-cache-dir -r requirements.txt
if [ "${BOT_ROLE}" = "admin" ]; then
  exec python -m admin_bot
else
  exec python -m field_bot
fi
