#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SMOKE_PLAN_ID="smoke-run-next"
HERMES_ROOT="$REPO_ROOT/.hermes"
SMOKE_PLAN_DIR="$HERMES_ROOT/plans/$SMOKE_PLAN_ID"

run() {
  echo "+ $*"
  "$@"
}

safe_remove_smoke_plan() {
  local target="$1"
  case "$target" in
    "$REPO_ROOT/.hermes/plans/$SMOKE_PLAN_ID")
      if [[ -d "$target" ]]; then
        rm -f -- \
          "$target/plan.md" \
          "$target/queue.md" \
          "$target/log.md" \
          "$target/state.json" \
          "$target/morning_brief.md" \
          "$target/reviewer_report.md"
        rmdir -- "$target"
      fi
      ;;
    *)
      echo "refusing to remove unexpected path: $target" >&2
      exit 1
      ;;
  esac
}

assert_output_contains() {
  local output="$1"
  local needle="$2"
  if ! grep -Fq -- "$needle" <<<"$output"; then
    echo "expected run-next output to contain: $needle" >&2
    exit 1
  fi
}

main() {
  cd "$REPO_ROOT"

  safe_remove_smoke_plan "$SMOKE_PLAN_DIR"

  run python3 -m py_compile hermes.py
  run python3 hermes.py plan-init "$SMOKE_PLAN_ID" \
    --title "Smoke Run Next" \
    --objective "Verify run-next dry-run selection"

  cat > "$SMOKE_PLAN_DIR/queue.md" <<'EOF'
| id | title | status | dependencies | notes |
| --- | --- | --- | --- | --- |
| unit-001 | Completed base | completed | - | Done |
| unit-002 | Runnable pending | pending | unit-001 | Should be selected |
| unit-003 | Blocked pending | pending | unit-999 | Missing dependency |
| unit-004 | Later pending | pending | - | Should not be selected first |
EOF

  local output
  output="$(python3 hermes.py run-next "$SMOKE_PLAN_ID" --dry-run)"
  printf '%s\n' "$output"

  assert_output_contains "$output" "mode: dry-run"
  assert_output_contains "$output" "selected_unit"
  assert_output_contains "$output" "unit-002"
  assert_output_contains "$output" "blocked_units"
  assert_output_contains "$output" "unit-003"
  assert_output_contains "$output" "dependency_missing:unit-999"

  safe_remove_smoke_plan "$SMOKE_PLAN_DIR"

  echo "Hermes v0.2-C run-next dry-run smoke test passed"
}

main "$@"
