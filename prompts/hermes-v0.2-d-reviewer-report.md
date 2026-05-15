You are implementing Hermes Agent OS v0.2-D.

Repository:
- ceoYS/hermes-agent-os
- Current branch: feat/v0.2-d-reviewer-report
- Base: v0.2-C, main HEAD 4ec81a8
- v0.2-C already implemented run-next <plan_id> --dry-run only.

Goal:
Implement v0.2-D reviewer report / needs_work scaffold.

Hard constraints:
- Keep everything local and file-based.
- Do not execute queue units.
- Do not call Codex from plan commands.
- Do not implement real run-next execution.
- Do not implement run-all.
- Do not add Gemini/Gemma/Claude/Nous routing.
- Do not auto push, auto merge, or auto deploy.
- Do not mutate queue.md, state.json, log.md, morning_brief.md, or plan files from run-next dry-run.
- .hermes/ must remain ignored by Git.

Scope:
1. Add a plan-level reviewer report scaffold:
   .hermes/plans/<plan_id>/reviewer_report.md

2. Start with one reviewer_report.md per plan, not per unit.
   Do NOT add .hermes/plans/<plan_id>/reviews/<unit_id>.md yet.

3. Define reviewer verdict values in the scaffold:
   - pass
   - pass_with_notes
   - needs_work
   - blocked

4. Make needs_work a first-class reviewer stop signal in status/docs output.
   It should be clear in plan-status that needs_work means the plan should not proceed until reviewed/fixed.

5. Extend plan-init:
   - It should create reviewer_report.md along with existing plan scaffold files.
   - Existing plan-init behavior must remain compatible.
   - Existing smoke tests must continue to pass.

6. Extend plan-status:
   - Show whether reviewer_report.md exists.
   - If it exists, parse a simple verdict field from it.
   - Recommended field format:
     verdict: pending
     or
     verdict: needs_work
   - Accepted reviewer verdicts:
     pending
     pass
     pass_with_notes
     needs_work
     blocked
   - Unknown/missing verdict should be reported clearly but should not crash.
   - needs_work and blocked should be displayed as stop signals.
   - pass/pass_with_notes should be displayed as non-blocking reviewer status.
   - pending should be displayed as not yet reviewed.

7. Add smoke script:
   scripts/smoke_v0_2_d_reviewer_report.sh

Smoke script requirements:
- Use a temporary isolated directory.
- Copy or invoke the local hermes.py in a safe way consistent with existing smoke scripts.
- Validate that plan-init creates reviewer_report.md.
- Validate that plan-status reports reviewer report information.
- Validate that setting verdict: needs_work is reported as a stop signal.
- Validate that setting verdict: pass is reported as non-blocking/pass.
- Validate that existing v0.2-A/B/C smoke behavior is not broken.
- Validate that .hermes/ is not tracked by git status in the repo.

Required validation commands:
python3 -m py_compile hermes.py
python3 hermes.py --help
bash scripts/smoke_v0_1.sh
bash scripts/smoke_v0_2_a_plan_scaffold.sh
bash scripts/smoke_v0_2_b_queue_parser.sh
bash scripts/smoke_v0_2_c_run_next_dry_run.sh
bash scripts/smoke_v0_2_d_reviewer_report.sh
git status --short

Docs:
- Update README.md and/or docs/ROADMAP.md minimally to record v0.2-D.
- Add only necessary documentation.
- Keep wording clear that reviewer_report.md is plan-level for now.

Implementation notes:
- Prefer small, readable helper functions.
- Do not over-engineer.
- Do not introduce external dependencies.
- Keep Python stdlib-only.
- Preserve current CLI behavior.
- Ensure existing tests/smokes keep passing.

Deliverable:
- Code changes in hermes.py
- New smoke script
- Minimal docs/prompt updates
- A final summary with changed files and validation results
