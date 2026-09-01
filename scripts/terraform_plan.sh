#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo "Plan-only handoff: review infra/terraform and run ./skills/terraform/run.sh deploy infra/terraform --plan-only after filling envs/dev.tfvars. Do not apply from this script."
