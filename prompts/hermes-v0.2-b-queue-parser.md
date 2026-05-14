Implement Hermes v0.2-B Queue Parser + Plan Status hardening.

Read first:
- hermes.py
- README.md
- docs/ROADMAP.md
- docs/V0_2_CRACK_LITE_PLAN.md
- docs/crack-cli-benchmark.md
- docs/AGENT_RULE_GOVERNANCE.md
- scripts/smoke_v0_1.sh
- scripts/smoke_v0_2_a_plan_scaffold.sh
- prompts/hermes-v0.2-a-plan-scaffold.md

Goal:
Improve Hermes plan-status so it can parse queue.md more reliably and report queue unit state.

This is NOT run-next.
This is NOT run-all.
This must not execute Codex.
This must not modify queue statuses.
This must only read and report plan queue information.

Scope:
1. Add a queue unit parser.

   It should parse `.hermes/plans/<plan_id>/queue.md`.

   Expected queue table:

   | id | title | status | dependencies | notes |
   | --- | --- | --- | --- | --- |
   | unit-001 | Define first unit | pending | - | Replace this row |

   Create an internal representation such as:
   - id
   - title
   - status
   - dependencies
   - notes
   - line_number
   - errors

2. Supported statuses:
   - pending
   - running
   - completed
   - needs_work
   - failed
   - skipped

3. Parser behavior:
   - Ignore blank lines.
   - Ignore non-table lines before or after the queue table.
   - Ignore the header row.
   - Ignore the separator row.
   - Trim whitespace around cells.
   - Require at least 5 cells.
   - Report malformed rows as warnings, not crashes.
   - Duplicate unit ids should be reported as warnings.
   - Unknown statuses should be counted as `unknown` and reported as warnings.
   - Empty id should be a warning.
   - Empty status should be a warning.

4. Update `plan-status <plan_id>`.

   It should print:
   - plan_id
   - title
   - status
   - created_at
   - updated_at
   - plan_dir
   - queue_counts
   - queue_units table/list
   - warnings count
   - warnings detail if any

   Keep output simple and terminal-friendly.

5. Update state.json only if needed.

   Prefer not to mutate state on plan-status.
   plan-status should be read-only.

6. Add or update smoke coverage.

   Update `scripts/smoke_v0_2_a_plan_scaffold.sh` or create:
   `scripts/smoke_v0_2_b_queue_parser.sh`

   Prefer creating a new v0.2-B smoke script.

   The script should:
   - Run python3 -m py_compile hermes.py
   - Create a smoke plan via plan-init
   - Overwrite that plan's queue.md with several rows:
     - pending
     - running
     - completed
     - needs_work
     - failed
     - skipped
     - unknown_status
     - duplicate id row
     - malformed short row
   - Run plan-status
   - Verify output contains:
     - pending
     - running
     - completed
     - needs_work
     - failed
     - skipped
     - unknown
     - warnings
   - Clean only the smoke plan directory.
   - Do not remove anything outside `.hermes/plans/<smoke-plan-id>`.

7. Update README.md.

   Add a short v0.2-B section:
   - plan-status now parses queue.md
   - supported statuses
   - smoke command example:
     bash scripts/smoke_v0_2_b_queue_parser.sh

8. Preserve existing behavior:
   - bash scripts/smoke_v0_1.sh must pass
   - bash scripts/smoke_v0_2_a_plan_scaffold.sh must pass
   - plan-init behavior must remain compatible

Non-scope:
- Do not implement run-next.
- Do not implement run-all.
- Do not execute queue units.
- Do not add Codex execution to plan commands.
- Do not add Gemini/Gemma/Claude routing.
- Do not add Nous Hermes integration.
- Do not add PLUR/RTK/hermesd.
- Do not auto push.
- Do not auto merge.
- Do not auto deploy.

Acceptance commands:
- python3 -m py_compile hermes.py
- python3 hermes.py --help
- bash scripts/smoke_v0_1.sh
- bash scripts/smoke_v0_2_a_plan_scaffold.sh
- bash scripts/smoke_v0_2_b_queue_parser.sh
- python3 hermes.py plan-init manual-queue-smoke --title "Manual Queue Smoke" --objective "Manual queue parser test"
- python3 hermes.py plan-status manual-queue-smoke
- git status --short must not show `.hermes/`
- git diff --stat

After implementation:
- Show changed files.
- Show validation results.
- Stop.
