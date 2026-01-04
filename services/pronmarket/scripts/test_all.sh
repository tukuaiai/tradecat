#!/usr/bin/env bash
set -euo pipefail
# Run tests for all services
for svc in services/*/; do
  if [ -d "$svc/tests" ]; then
    echo "Running tests for $svc"
    python -m pytest "$svc/tests" || exit 1
  fi
done
