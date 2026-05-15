Implement Hermes v0.2-C run-next --dry-run.

Read first:
- hermes.py
- README.md
- docs/ROADMAP.md
- docs/V0_2_CRACK_LITE_PLAN.md
- docs/crack-cli-benchmark.md
- docs/AGENT_RULE_GOVERNANCE.md
- scripts/smoke_v0_1.sh
- scripts/smoke_v0_2_a_plan_scaffold.sh
- scripts/smoke_v0_2_b_queue_parser.sh
- prompts/hermes-v0.2-b-queue-parser.md

Goal:
Add a read-only command:
  python3 hermes.py run-next <plan_id> --dry-run

Rules:
- Require --dry-run.
- Without --dry-run, fail clearly: real execution is not implemented in v0.2-C.
- Do not call Codex.
- Do not modify queue.md, state.json, log.md, morning_brief.md, or any plan file.
- Do not implement run-all.
- Do not add model routing.
- Do not auto push/merge/deploy.

Behavior:
- Read .hermes/plans/<plan_id>/state.json.
- Parse .hermes/plans/<plan_id>/queue.md using existing parser.
- Candidate units have status pending.
- dependencies may be "-", empty, or comma-separated unit ids.
- A pending unit is runnable only if all dependencies exist and have status completed.
- Pick the first runnable pending unit in queue order.
- If none exists, print selected_unit: none.
- Print:
  - plan_id
  - mode: dry-run
  - selected_unit
  - blocked_units
  - completed dependency map summary
  - queue parser warnings, if any
- Block reasons:
  - dependency_not_completed:<unit_id>
  - dependency_missing:<unit_id>

Add CLI:
- run-next subcommand
- plan_id argument
- --dry-run flag

Update README:
- Add v0.2-C run-next dry-run section.

Add smoke script:
scripts/smoke_v0_2_c_run_next_dry_run.sh

Smoke script:
- compile hermes.py
- create plan smoke-run-next
- overwrite queue.md with:
  | id | title | status | dependencies | notes |
  | --- | --- | --- | --- | --- |
  | unit-001 | Completed base | completed | - | Done |
  | unit-002 | Runnable pending | pending | unit-001 | Should be selected |
  | unit-003 | Blocked pending | pending | unit-999 | Missing dependency |
  | unit-004 | Later pending | pending | - | Should not be selected first |
- run python3 hermes.py run-next smoke-run-next --dry-run
- verify output contains mode dry-run, selected_unit, unit-002, blocked_units, unit-003, dependency_missing:unit-999
- clean only .hermes/plans/smoke-run-next

Preserve:
- bash scripts/smoke_v0_1.sh
- bash scripts/smoke_v0_2_a_plan_scaffold.sh
- bash scripts/smoke_v0_2_b_queue_parser.sh

Acceptance:
- python3 -m py_compile hermes.py
- python3 hermes.py --help
- bash scripts/smoke_v0_1.sh
- bash scripts/smoke_v0_2_a_plan_scaffold.sh
- bash scripts/smoke_v0_2_b_queue_parser.sh
- bash scripts/smoke_v0_2_c_run_next_dry_run.sh
- git status --short must not show .hermes/
- git diff --stat

After implementation:
- Show changed files.
- Show validation results.
- Stop.
