# Hermes Operator Checklist

This checklist closes the Hermes v0.2 operating line before any v0.3
execution work is considered. It is for a human operator. It does not add
runner behavior, automation, reviewer execution, model routing, push, merge,
or deploy capability.

## Baseline Checks

Run these checks from the repository root before starting a release branch,
merge, or tag operation:

```bash
git checkout main
git fetch origin --prune --tags
git pull --ff-only origin main
git status --short
git log --oneline -10
git tag --list "hermes-v0.2*"
```

Confirm:

- `main` is current with `origin/main`.
- The expected release tag exists.
- `git status --short` is empty before starting release work.
- No generated `.hermes/` runtime state is staged or committed.

## Plan Setup

Create a local plan scaffold with `plan-init`:

```bash
python3 hermes.py plan-init <plan_id> --title "<title>" --objective "<objective>"
```

Confirm the generated local plan directory:

```bash
python3 hermes.py plan-status <plan_id>
```

The generated `.hermes/plans/<plan_id>/` directory is local runtime state and
must remain ignored by Git.

## Queue Review

Open `.hermes/plans/<plan_id>/queue.md` and confirm:

- each planned unit is explicit
- each unit has a stable id
- each unit has a supported status
- dependencies are either empty, `-`, or comma-separated unit ids
- pending units do not skip required completed dependencies
- no queue unit implies automatic push, merge, deploy, or reviewer execution

Then run:

```bash
python3 hermes.py plan-status <plan_id>
python3 hermes.py run-next <plan_id> --dry-run
```

Confirm `run-next --dry-run` only reports the first runnable pending unit and
does not modify plan files or execute Codex.

## Reviewer Report

Open `.hermes/plans/<plan_id>/reviewer_report.md` and confirm the plan-level
reviewer verdict is present and current:

```markdown
verdict: pending
```

Supported verdicts:

- `pending`
- `pass`
- `pass_with_notes`
- `needs_work`
- `blocked`

Run:

```bash
python3 hermes.py plan-status <plan_id>
```

Confirm the `review_gate` summary:

- `blocked_by_reviewer` means the operator must stop until `needs_work` or
  `blocked` is resolved.
- `open` means the current verdict is non-blocking.
- `unknown` means the operator must inspect and correct the reviewer report.

Hermes v0.2 reports this gate only. It does not enforce the gate automatically.

## Manual Review Checkpoints

Open `.hermes/plans/<plan_id>/log.md` and append human-authored audit rows under
`Manual Review Checkpoints` for major decisions.

Each checkpoint should record:

- reviewer or operator
- checkpoint name
- verdict
- date or relevant link
- notes needed for later audit

Manual Review Checkpoints remain audit history only. They do not replace the
machine-readable current verdict in `reviewer_report.md`.

## Pre-Merge And Pre-Tag Checks

Before merge or tag, run the existing smoke checks:

```bash
python3 -m py_compile hermes.py
bash scripts/smoke_v0_1.sh
bash scripts/smoke_v0_2_a_plan_scaffold.sh
bash scripts/smoke_v0_2_b_queue_parser.sh
bash scripts/smoke_v0_2_c_run_next_dry_run.sh
bash scripts/smoke_v0_2_d_reviewer_report.sh
bash scripts/smoke_v0_2_e_review_gate.sh
bash scripts/smoke_v0_2_f_review_checkpoint_log.sh
```

Confirm:

- all smoke checks pass
- `git status --short` only shows intended committed or staged release changes
- no `.hermes/` runtime state is included
- no code behavior changed for a documentation-only release

## Wrong Tag Recovery

If a release tag is created at the wrong commit, stop and inspect before
changing anything:

```bash
git rev-parse --short HEAD
git rev-parse --short <tag_name>
git show --no-patch --oneline <tag_name>
```

If the wrong tag has not been pushed, delete and recreate it locally:

```bash
git tag -d <tag_name>
git tag <tag_name> <correct_commit>
git show --no-patch --oneline <tag_name>
```

If the wrong tag has already been pushed, require explicit human approval before
changing the remote tag:

```bash
git tag -d <tag_name>
git tag <tag_name> <correct_commit>
git push origin :refs/tags/<tag_name>
git push origin <tag_name>
```

Record the correction in the release notes or operator log.

## Explicit Non-Goals

Hermes is not yet an autonomous multi-task executor.

Hermes does not auto-route models.

Hermes does not auto-run reviewers.

Hermes does not auto-push, auto-merge, or auto-deploy.

Hermes does not enforce reviewer gates automatically yet.

Manual Review Checkpoints remain human-authored audit logs.

## Safety Boundaries

These boundaries remain active through v0.2 closure:

- no Codex execution expansion
- no run-all
- no model routing
- no auto push, merge, or deploy
- no auto reviewer execution
- no per-unit review files
- `.hermes/` remains local runtime ignored state
