Implement Hermes v0.2-A Crack-lite Plan Scaffold.

Read first:
- hermes.py
- README.md
- docs/ROADMAP.md
- docs/V0_2_CRACK_LITE_PLAN.md
- docs/crack-cli-benchmark.md
- docs/AGENT_RULE_GOVERNANCE.md
- scripts/smoke_v0_1.sh

Goal:
Add the minimum plan-scaffold layer for Hermes Agent OS.

This is NOT the full Crack-lite runner.
This PR must only create and inspect plan directories.
Do not implement run-next.
Do not implement run-all.
Do not call Codex from plan commands.
Do not add Nous Hermes, Gemma, PLUR, RTK, Telegram, or Antigravity integration.

Scope:
1. Add `.hermes/` to `.gitignore`.
   - Plan working directories are local runtime artifacts.
   - Do not commit generated `.hermes/plans/*`.

2. Add command:
   `python3 hermes.py plan-init <plan_id> --title <title> --objective <objective>`

   Behavior:
   - Create `.hermes/inbox.md` if missing.
   - Create `.hermes/plans/<plan_id>/`.
   - Reject plan_id with path separators, spaces, `..`, or unsafe characters.
   - Create:
     - plan.md
     - queue.md
     - log.md
     - state.json
     - morning_brief.md
   - Fail if the plan already exists unless `--force` is explicitly provided.
   - If `--force` is added, it must only overwrite files inside the exact plan directory.
   - Use Path.resolve() and relative_to() style safety checks.
   - No broad delete.
   - No shell rm -rf.
   - No git push/merge/deploy.

3. Add command:
   `python3 hermes.py plan-status <plan_id>`

   Behavior:
   - Read `.hermes/plans/<plan_id>/state.json`.
   - Print:
     - plan_id
     - title
     - status
     - created_at
     - updated_at
     - plan_dir
     - queue counts if queue.md has simple status markers
   - If the plan does not exist, return a clear error.

4. Template requirements:

   plan.md should include:
   - title
   - objective
   - constraints
   - non-goals
   - acceptance criteria
   - ordered units placeholder

   queue.md should include a simple Markdown table:
   | id | title | status | dependencies | notes |
   with one placeholder row:
   | unit-001 | Define first unit | pending | - | Replace this row |

   log.md should be append-only style:
   - created timestamp entry

   state.json should include:
   - schema_version: 1
   - hermes_version
   - plan_id
   - title
   - objective
   - status: created
   - created_at
   - updated_at
   - plan_dir
   - files block with paths

   morning_brief.md should include:
   - empty summary section
   - pending decisions section
   - next actions section

5. Update README.md:
   - Add v0.2-A Plan Scaffold section.
   - Show example commands:
     python3 hermes.py plan-init trader-d129-docs-only --title "Trader D129 docs-only review" --objective "Prepare a docs-only review plan"
     python3 hermes.py plan-status trader-d129-docs-only
   - State that generated `.hermes/` runtime plans are local and ignored by Git.

6. Add a portable smoke script:
   `scripts/smoke_v0_2_a_plan_scaffold.sh`

   It must:
   - Remove only `/tmp/hermes-v02a-smoke-repo` if used, or use the current repo safely.
   - Run:
     - python3 -m py_compile hermes.py
     - python3 hermes.py --help
     - python3 hermes.py plan-init smoke-plan --title "Smoke Plan" --objective "Verify plan scaffold"
     - python3 hermes.py plan-status smoke-plan
   - Verify generated files exist.
   - Verify `.hermes/plans/smoke-plan/state.json` contains plan_id smoke-plan.
   - Clean up only `.hermes/plans/smoke-plan` and leave `.hermes/inbox.md` if created, or clean the whole `.hermes` only if it is under the current repo and contains only smoke-owned content.
   - Be conservative.

7. Preserve all v0.1 behavior:
   - python3 hermes.py validate examples/trader-review.yaml may still be machine-specific.
   - bash scripts/smoke_v0_1.sh must still pass.

Acceptance:
- python3 -m py_compile hermes.py
- python3 hermes.py --help
- bash scripts/smoke_v0_1.sh
- bash scripts/smoke_v0_2_a_plan_scaffold.sh
- python3 hermes.py plan-init manual-smoke --title "Manual Smoke" --objective "Manual test"
- python3 hermes.py plan-status manual-smoke
- git status --short must not show `.hermes/`
- git diff --stat

After implementation:
- Show changed files.
- Show validation results.
- Stop.

Safety:
- No Codex nested execution.
- No auto push.
- No auto merge.
- No auto deploy.
- No run-next.
- No run-all.
