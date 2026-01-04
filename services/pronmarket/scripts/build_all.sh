#!/usr/bin/env bash
set -euo pipefail
# Build all services
for svc in services/*/; do
  echo "Building $svc"
  docker build "$svc"
done
