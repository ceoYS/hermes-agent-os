#!/usr/bin/env python3
"""Hermes v0: a minimal local single-task runner."""

from __future__ import annotations

import argparse
import fnmatch
import getpass
import json
import math
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


HERMES_VERSION = "0.2.0-f"
SCHEMA_VERSION = 1

EXIT_SUCCESS = 0
EXIT_GENERAL = 1
EXIT_VALIDATION = 2
EXIT_CODEX = 3
EXIT_GIT = 4
EXIT_SAFETY = 5

STATUSES = {
    "created",
    "validated",
    "run_dir_created",
    "worktree_created",
    "prompt_built",
    "running_codex",
    "codex_completed",
    "collecting_git_outputs",
    "completed",
    "completed_with_warnings",
    "failed",
}

PLAN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
PLAN_FILES = [
    "plan.md",
    "queue.md",
    "log.md",
    "state.json",
    "morning_brief.md",
    "reviewer_report.md",
]
REVIEWER_VERDICTS = {
    "pending",
    "pass",
    "pass_with_notes",
    "needs_work",
    "blocked",
}
REVIEWER_STOP_VERDICTS = {"needs_work", "blocked"}
REVIEWER_OPEN_VERDICTS = {"pending", "pass", "pass_with_notes"}
QUEUE_STATUSES = {
    "pending",
    "running",
    "completed",
    "needs_work",
    "failed",
    "skipped",
}
QUEUE_COUNT_ORDER = [
    "pending",
    "running",
    "completed",
    "needs_work",
    "failed",
    "skipped",
    "unknown",
]

FORBIDDEN_CONTEXT_PATTERNS = [
    ".env",
    ".env.*",
    "secrets.*",
    "credentials.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_ed25519",
    "node_modules",
    ".venv",
    ".git",
    ".ssh",
    ".aws",
    ".gnupg",
]

REQUIRED_FIELDS = [
    "id",
    "repo_path",
    "base_branch",
    "branch_prefix",
    "runs_root",
    "risk_level",
    "task_type",
    "allow_edits",
    "allow_push",
    "allow_draft_pr",
    "codex.model",
    "codex.effort",
    "codex.sandbox",
    "codex.timeout_minutes",
    "limits.max_context_chars",
    "limits.max_prompt_chars",
    "limits.max_stdout_mb",
    "limits.max_stderr_mb",
    "context_files",
    "objective",
    "acceptance_criteria",
]


class HermesError(Exception):
    exit_code = EXIT_GENERAL

    def __init__(self, message: str, exit_code: int | None = None):
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class ValidationError(HermesError):
    exit_code = EXIT_VALIDATION


class GitError(HermesError):
    exit_code = EXIT_GIT


class SafetyError(HermesError):
    exit_code = EXIT_SAFETY


class CodexError(HermesError):
    exit_code = EXIT_CODEX


class Logger:
    def __init__(self, path: Path | None = None, backlog: list[str] | None = None):
        self.path = path
        self.backlog = backlog if backlog is not None else []
        if self.path is not None and self.backlog:
            with open_text(self.path, "a") as handle:
                for line in self.backlog:
                    handle.write(line.rstrip("\n") + "\n")
            self.backlog.clear()

    def attach(self, path: Path) -> None:
        self.path = path
        if self.backlog:
            with open_text(self.path, "a") as handle:
                for line in self.backlog:
                    handle.write(line.rstrip("\n") + "\n")
            self.backlog.clear()

    def log(self, message: str) -> None:
        line = f"{now_iso()} {message}"
        if self.path is None:
            self.backlog.append(line)
            return
        with open_text(self.path, "a") as handle:
            handle.write(line + "\n")


@dataclass
class QueueUnit:
    id: str
    title: str
    status: str
    dependencies: str
    notes: str
    line_number: int
    errors: list[str] = field(default_factory=list)


@dataclass
class BlockedQueueUnit:
    unit: QueueUnit
    reasons: list[str]


@dataclass
class ReviewerReport:
    exists: bool
    verdict: str | None
    status: str
    stop_signal: bool
    detail: str


def now_local() -> datetime:
    return datetime.now().astimezone()


def now_iso() -> str:
    return now_local().isoformat(timespec="seconds")


def timestamp_slug() -> str:
    return now_local().strftime("%Y%m%d-%H%M%S")


def open_text(path: Path, mode: str):
    return open(path, mode, encoding="utf-8", errors="replace")


def read_text(path: Path) -> str:
    with open_text(path, "r") as handle:
        return handle.read()


def write_text(path: Path, text: str) -> None:
    with open_text(path, "w") as handle:
        handle.write(text)


def write_json(path: Path, data: dict[str, Any]) -> None:
    with open_text(path, "w") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def command_line() -> str:
    return " ".join(shlex.quote(arg) for arg in sys.argv)


def format_cmd(args: list[str]) -> str:
    return " ".join(shlex.quote(str(arg)) for arg in args)


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ValidationError(
            "PyYAML is required to read task YAML. Install it with: python3 -m pip install pyyaml"
        ) from exc

    try:
        with open_text(path, "r") as handle:
            loaded = yaml.safe_load(handle)
    except FileNotFoundError as exc:
        raise ValidationError(f"task file not found: {path}") from exc
    except Exception as exc:
        raise ValidationError(f"failed to read task YAML: {exc}") from exc

    if not isinstance(loaded, dict):
        raise ValidationError("task YAML must contain a mapping at the top level")
    return loaded


def get_nested(data: dict[str, Any], dotted: str) -> Any:
    value: Any = data
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def require_string(task: dict[str, Any], key: str) -> str:
    value = get_nested(task, key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{key} must be a non-empty string")
    return value


def require_bool(task: dict[str, Any], key: str) -> bool:
    value = get_nested(task, key)
    if not isinstance(value, bool):
        raise ValidationError(f"{key} must be a boolean")
    return value


def require_positive_number(task: dict[str, Any], key: str) -> int | float:
    value = get_nested(task, key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValidationError(f"{key} must be a positive number")
    return value


def require_string_list(task: dict[str, Any], key: str) -> list[str]:
    value = get_nested(task, key)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValidationError(f"{key} must be a list of strings")
    return value


def validate_schema(task: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if get_nested(task, field) is None]
    if missing:
        raise ValidationError("missing required fields: " + ", ".join(missing))
    if "run_id" in task:
        raise ValidationError("run_id is generated by Hermes v0 and must not be supplied")

    task_id = require_string(task, "id")
    if "/" in task_id or "\\" in task_id or ".." in Path(task_id).parts:
        raise ValidationError("id must not contain path separators or '..'")

    for key in [
        "repo_path",
        "base_branch",
        "branch_prefix",
        "runs_root",
        "risk_level",
        "task_type",
        "codex.model",
        "codex.effort",
        "codex.sandbox",
        "objective",
    ]:
        require_string(task, key)

    for key in ["allow_edits", "allow_push", "allow_draft_pr"]:
        require_bool(task, key)

    for key in [
        "codex.timeout_minutes",
        "limits.max_context_chars",
        "limits.max_prompt_chars",
        "limits.max_stdout_mb",
        "limits.max_stderr_mb",
    ]:
        require_positive_number(task, key)

    require_string_list(task, "context_files")
    acceptance = get_nested(task, "acceptance_criteria")
    if not isinstance(acceptance, list) or any(
        not isinstance(item, str) or not item.strip() for item in acceptance
    ):
        raise ValidationError("acceptance_criteria must be a list of non-empty strings")


def enforce_risk_policy(task: dict[str, Any]) -> None:
    risk_level = require_string(task, "risk_level")
    task_type = require_string(task, "task_type")
    allow_edits = require_bool(task, "allow_edits")
    allow_push = require_bool(task, "allow_push")
    allow_draft_pr = require_bool(task, "allow_draft_pr")
    sandbox = require_string(task, "codex.sandbox")

    if allow_push:
        raise SafetyError("allow_push must be false in Hermes v0")
    if allow_draft_pr:
        raise SafetyError("allow_draft_pr must be false in Hermes v0")
    if sandbox not in {"read-only", "workspace-write"}:
        if sandbox == "danger-full-access":
            raise SafetyError("danger-full-access is rejected in Hermes v0")
        raise SafetyError("codex.sandbox must be read-only or workspace-write")

    if risk_level == "critical":
        errors = []
        if task_type != "review":
            errors.append("task_type must be review")
        if allow_edits:
            errors.append("allow_edits must be false")
        if allow_push:
            errors.append("allow_push must be false")
        if allow_draft_pr:
            errors.append("allow_draft_pr must be false")
        if sandbox != "read-only":
            errors.append("codex.sandbox must be read-only")
        if errors:
            raise SafetyError("critical risk policy violation: " + "; ".join(errors))


def run_process(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: int | float | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            cwd=str(cwd) if cwd is not None else None,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ValidationError(f"command not found: {args[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValidationError(f"command timed out: {format_cmd(args)}") from exc


def run_git(
    repo_path: Path,
    git_args: list[str],
    *,
    logger: Logger | None = None,
    timeout: int | float | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    args = ["git", "-C", str(repo_path), *git_args]
    if logger is not None:
        logger.log("RUN " + format_cmd(args))
    result = run_process(args, timeout=timeout)
    if check and result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        detail = stderr or stdout or f"exit code {result.returncode}"
        raise GitError(f"git command failed: {format_cmd(args)}: {detail}")
    return result


def run_git_output_to_file(
    worktree_path: Path,
    git_args: list[str],
    output_path: Path,
    *,
    logger: Logger,
) -> str:
    result = run_git(worktree_path, git_args, logger=logger)
    write_text(output_path, result.stdout)
    return result.stdout


def verify_repo(task: dict[str, Any], logger: Logger) -> Path:
    repo_path = Path(require_string(task, "repo_path")).expanduser()
    if not repo_path.exists():
        raise ValidationError(f"repo_path does not exist: {repo_path}")
    if not repo_path.is_dir():
        raise ValidationError(f"repo_path is not a directory: {repo_path}")
    repo_path = repo_path.resolve()

    result = run_git(repo_path, ["rev-parse", "--is-inside-work-tree"], logger=logger)
    if result.stdout.strip() != "true":
        raise ValidationError(f"repo_path is not a git work tree: {repo_path}")
    return repo_path


def preflight_codex(logger: Logger) -> dict[str, str]:
    outputs: dict[str, str] = {}
    version_cmd = ["codex", "--version"]
    logger.log("RUN " + format_cmd(version_cmd))
    version = run_process(version_cmd, timeout=10)
    if version.returncode != 0:
        raise ValidationError(
            "codex --version failed: " + (version.stderr.strip() or version.stdout.strip())
        )
    outputs["codex_version"] = (version.stdout or version.stderr).strip()

    help_cmd = ["codex", "exec", "--help"]
    logger.log("RUN " + format_cmd(help_cmd))
    help_result = run_process(help_cmd, timeout=10)
    outputs["codex_exec_help"] = (
        "STDOUT:\n"
        + help_result.stdout
        + "\nSTDERR:\n"
        + help_result.stderr
        + f"\nEXIT_CODE: {help_result.returncode}\n"
    )
    if help_result.returncode != 0:
        raise ValidationError(
            "codex exec --help failed: "
            + (help_result.stderr.strip() or help_result.stdout.strip())
        )
    return outputs


def get_command_version(command: list[str]) -> str | None:
    try:
        result = run_process(command, timeout=10)
    except HermesError:
        return None
    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        return None
    return output or None


def normalize_context_path(raw_path: str) -> str:
    path = Path(raw_path)
    if path.is_absolute():
        raise ValidationError(f"context file must be relative: {raw_path}")
    if any(part == ".." for part in path.parts):
        raise ValidationError(f"context file must not contain '..': {raw_path}")
    if not raw_path.strip():
        raise ValidationError("context file path must not be empty")
    if raw_path.endswith("/"):
        raise ValidationError(f"context file must be a file path, not a directory: {raw_path}")

    normalized = path.as_posix()
    full = normalized
    for pattern in FORBIDDEN_CONTEXT_PATTERNS:
        if fnmatch.fnmatchcase(full, pattern):
            raise SafetyError(f"context file matches forbidden pattern {pattern}: {raw_path}")
    for component in Path(normalized).parts:
        for pattern in FORBIDDEN_CONTEXT_PATTERNS:
            if fnmatch.fnmatchcase(component, pattern):
                raise SafetyError(
                    f"context file component matches forbidden pattern {pattern}: {raw_path}"
                )
    return normalized


def load_context_files(
    repo_path: Path,
    base_commit: str,
    paths: list[str],
    logger: Logger,
) -> list[dict[str, str]]:
    context_entries: list[dict[str, str]] = []
    for raw_path in paths:
        rel_path = normalize_context_path(raw_path)
        ls_tree = run_git(repo_path, ["ls-tree", base_commit, "--", rel_path], logger=logger)
        line = ls_tree.stdout.strip()
        if not line:
            raise ValidationError(f"context file missing at base commit: {rel_path}")
        meta = line.split(None, 3)
        if len(meta) < 4:
            raise ValidationError(f"unexpected git ls-tree output for {rel_path}")
        mode, object_type = meta[0], meta[1]
        if mode == "120000":
            raise SafetyError(f"context file is a symlink at base commit: {rel_path}")
        if object_type != "blob":
            raise ValidationError(f"context path is not a file at base commit: {rel_path}")

        show = run_git(repo_path, ["show", f"{base_commit}:{rel_path}"], logger=logger)
        context_entries.append({"path": rel_path, "content": show.stdout})
    return context_entries


def build_prompt(
    task: dict[str, Any],
    *,
    mode: str,
    prompt_template: str,
    base_commit: str,
    context_entries: list[dict[str, str]],
) -> str:
    criteria = "\n".join(f"- {item}" for item in get_nested(task, "acceptance_criteria"))
    constraints = [
        f"risk_level: {require_string(task, 'risk_level')}",
        f"task_type: {require_string(task, 'task_type')}",
        f"allow_edits: {require_bool(task, 'allow_edits')}",
        "allow_push: false",
        "allow_draft_pr: false",
        "do not push",
        "do not create a PR",
        "do not merge",
        "do not deploy",
    ]

    if not require_bool(task, "allow_edits"):
        constraints.extend(
            [
                "mode: review only",
                "do not modify files",
                "do not create commits",
                "output findings to stdout",
            ]
        )
    else:
        constraints.extend(
            [
                "mode: implementation",
                "you may edit files inside the worktree",
                "do not commit unless the objective explicitly requires commits",
            ]
        )

    chunks = [
        "# Hermes Task",
        "",
        f"Task ID: {require_string(task, 'id')}",
        f"Mode: {mode}",
        f"Prompt Template: {prompt_template}",
        f"Base Branch: {require_string(task, 'base_branch')}",
        f"Base Commit: {base_commit}",
        "",
        "## Objective",
        require_string(task, "objective").rstrip(),
        "",
        "## Acceptance Criteria",
        criteria,
        "",
        "## Constraints",
        "\n".join(f"- {item}" for item in constraints),
        "",
        "## Context Files",
    ]

    if not context_entries:
        chunks.append("No context files were supplied.")
    for entry in context_entries:
        chunks.extend(
            [
                "",
                f"### {entry['path']}",
                "```",
                entry["content"].rstrip("\n"),
                "```",
            ]
        )
    chunks.append("")
    return "\n".join(chunks)


def estimate_input_tokens(prompt_text: str) -> int:
    # Intentionally conservative for Korean/CJK-heavy prompts where character/token ratios are lower.
    return math.ceil(len(prompt_text) / 2)


def prompt_template_for(task: dict[str, Any]) -> str:
    if require_string(task, "task_type") == "review" or not require_bool(task, "allow_edits"):
        return "review.v0"
    return "implementation.v0"


def mode_for(task: dict[str, Any]) -> str:
    if require_bool(task, "allow_edits"):
        return "implementation"
    return "review"


def build_plan_values(task: dict[str, Any]) -> dict[str, Any]:
    stamp = timestamp_slug()
    run_id = f"{require_string(task, 'id')}-{stamp}"
    branch = f"{require_string(task, 'branch_prefix')}-{stamp}"
    runs_root = Path(require_string(task, "runs_root")).expanduser().resolve()
    run_dir = runs_root / run_id
    worktree_path = run_dir / "worktree"
    return {
        "stamp": stamp,
        "run_id": run_id,
        "branch": branch,
        "runs_root": runs_root,
        "run_dir": run_dir,
        "worktree_path": worktree_path,
    }


def validate_task(task_path: Path, *, execute: bool = False) -> dict[str, Any]:
    logger = Logger()
    task = load_yaml(task_path)
    validate_schema(task)
    enforce_risk_policy(task)
    repo_path = verify_repo(task, logger)

    codex_preflight: dict[str, str] = {}
    if execute:
        codex_preflight = preflight_codex(logger)

    base_branch = require_string(task, "base_branch")
    run_git(repo_path, ["rev-parse", "--verify", base_branch], logger=logger)
    base_commit_result = run_git(repo_path, ["rev-parse", base_branch], logger=logger)
    base_commit = base_commit_result.stdout.strip()
    if not base_commit:
        raise GitError(f"could not resolve base commit for {base_branch}")

    dirty = run_git(repo_path, ["status", "--porcelain"], logger=logger)
    if dirty.stdout.strip():
        raise ValidationError(f"repo_path has uncommitted changes: {repo_path}")

    context_entries = load_context_files(
        repo_path,
        base_commit,
        require_string_list(task, "context_files"),
        logger,
    )
    context_chars = sum(len(entry["content"]) for entry in context_entries)
    max_context_chars = int(require_positive_number(task, "limits.max_context_chars"))
    if context_chars > max_context_chars:
        raise ValidationError(
            f"context size {context_chars} exceeds limits.max_context_chars {max_context_chars}"
        )

    prompt_template = prompt_template_for(task)
    prompt_text = build_prompt(
        task,
        mode=mode_for(task),
        prompt_template=prompt_template,
        base_commit=base_commit,
        context_entries=context_entries,
    )
    max_prompt_chars = int(require_positive_number(task, "limits.max_prompt_chars"))
    if len(prompt_text) > max_prompt_chars:
        raise ValidationError(
            f"prompt size {len(prompt_text)} exceeds limits.max_prompt_chars {max_prompt_chars}"
        )
    estimated_tokens = estimate_input_tokens(prompt_text)

    plan = build_plan_values(task)
    conflict = run_git(
        repo_path,
        ["rev-parse", "--verify", f"refs/heads/{plan['branch']}"],
        logger=logger,
        check=False,
    )
    if conflict.returncode == 0:
        raise SafetyError(f"branch already exists: {plan['branch']}")

    return {
        "task": task,
        "repo_path": repo_path,
        "base_commit": base_commit,
        "context_entries": context_entries,
        "context_chars": context_chars,
        "prompt_template": prompt_template,
        "prompt_text": prompt_text,
        "estimated_input_tokens": estimated_tokens,
        "plan": plan,
        "preflight_log": logger.backlog[:],
        "codex_preflight": codex_preflight,
    }


def environment_snapshot(
    *,
    started_in_cwd: Path,
    codex_version: str | None = None,
) -> dict[str, Any]:
    return {
        "hermes_version": HERMES_VERSION,
        "schema_version": SCHEMA_VERSION,
        "command_line": command_line(),
        "python_version": sys.version.replace("\n", " "),
        "codex_version": codex_version if codex_version is not None else get_command_version(["codex", "--version"]),
        "git_version": get_command_version(["git", "--version"]),
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "started_in_cwd": str(started_in_cwd),
    }


def output_paths(run_dir: Path) -> dict[str, str]:
    return {
        "hermes_log": str(run_dir / "hermes.log"),
        "task_yaml": str(run_dir / "task.yaml"),
        "prompt": str(run_dir / "prompt.md"),
        "codex_stdout": str(run_dir / "codex_stdout.log"),
        "codex_stderr": str(run_dir / "codex_stderr.log"),
        "git_status_raw": str(run_dir / "git_status_raw.txt"),
        "git_status": str(run_dir / "git_status.txt"),
        "git_diff_stat": str(run_dir / "git_diff_stat.txt"),
        "git_diff_patch": str(run_dir / "git_diff.patch"),
        "git_commits_since_base": str(run_dir / "git_commits_since_base.txt"),
        "git_branch_diff_patch": str(run_dir / "git_branch_diff.patch"),
        "state": str(run_dir / "state.json"),
    }


def validate_plan_id(plan_id: str) -> str:
    if not plan_id:
        raise ValidationError("plan_id must not be empty")
    if plan_id.strip() != plan_id:
        raise ValidationError("plan_id must not contain leading or trailing whitespace")
    if any(separator in plan_id for separator in ["/", "\\"]):
        raise ValidationError("plan_id must not contain path separators")
    if any(character.isspace() for character in plan_id):
        raise ValidationError("plan_id must not contain spaces or whitespace")
    if ".." in plan_id:
        raise ValidationError("plan_id must not contain '..'")
    if not PLAN_ID_RE.fullmatch(plan_id):
        raise ValidationError("plan_id may only contain letters, numbers, '.', '_', and '-'")
    return plan_id


def hermes_root() -> Path:
    return (Path.cwd() / ".hermes").resolve()


def plan_paths(plan_id: str) -> dict[str, Path]:
    safe_plan_id = validate_plan_id(plan_id)
    root = hermes_root()
    plans_root = (root / "plans").resolve()
    plan_dir = (plans_root / safe_plan_id).resolve()
    try:
        plan_dir.relative_to(plans_root)
    except ValueError as exc:
        raise SafetyError(f"plan directory escapes .hermes/plans: {plan_dir}") from exc

    files = {name: (plan_dir / name).resolve() for name in PLAN_FILES}
    for path in files.values():
        try:
            path.relative_to(plan_dir)
        except ValueError as exc:
            raise SafetyError(f"plan file escapes plan directory: {path}") from exc

    return {
        "root": root,
        "plans_root": plans_root,
        "plan_dir": plan_dir,
        "inbox": (root / "inbox.md").resolve(),
        **files,
    }


def render_plan_md(*, title: str, objective: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "## Objective",
            objective,
            "",
            "## Constraints",
            "- No auto push",
            "- No auto merge",
            "- No auto deploy",
            "- Execute at most one future unit at a time",
            "",
            "## Non-Goals",
            "- run-next implementation",
            "- run-all implementation",
            "- External agent integration",
            "",
            "## Acceptance Criteria",
            "- Plan scaffold is reviewable before execution",
            "- Queue units are explicit and ordered",
            "",
            "## Ordered Units",
            "1. unit-001 - Define first unit",
            "",
        ]
    )


def render_queue_md() -> str:
    return "\n".join(
        [
            "| id | title | status | dependencies | notes |",
            "| --- | --- | --- | --- | --- |",
            "| unit-001 | Define first unit | pending | - | Replace this row |",
            "",
        ]
    )


def render_plan_log_md(*, created_at: str) -> str:
    return "\n".join(
        [
            "# Plan Log",
            "",
            f"- {created_at} created plan scaffold",
            "",
            "## Manual Review Checkpoints",
            "",
            "Human reviewers can record major plan-level review decisions here as the plan progresses.",
            "This section is a human-maintained audit log, not an automatic source of truth for Hermes decisions.",
            "",
            "Accepted verdicts: `pending`, `pass`, `pass_with_notes`, `needs_work`, `blocked`.",
            "",
            "| timestamp | reviewer | checkpoint | verdict | notes |",
            "| --- | --- | --- | --- | --- |",
            "| YYYY-MM-DDTHH:MM:SS+09:00 | reviewer-name | checkpoint name | pending | Notes or links |",
            "",
        ]
    )


def render_morning_brief_md(*, title: str) -> str:
    return "\n".join(
        [
            f"# Morning Brief: {title}",
            "",
            "## Summary",
            "",
            "## Pending Decisions",
            "",
            "## Next Actions",
            "",
        ]
    )


def render_reviewer_report_md() -> str:
    return "\n".join(
        [
            "# Reviewer Report",
            "",
            "verdict: pending",
            "",
            "Accepted verdicts:",
            "- pending",
            "- pass",
            "- pass_with_notes",
            "- needs_work",
            "- blocked",
            "",
            "## Notes",
            "",
            "## Required Fixes",
            "",
        ]
    )


def parse_reviewer_report(report_path: Path) -> ReviewerReport:
    if not report_path.exists():
        return ReviewerReport(
            exists=False,
            verdict=None,
            status="missing_report",
            stop_signal=False,
            detail="reviewer_report.md does not exist",
        )

    verdict: str | None = None
    for line in read_text(report_path).splitlines():
        match = re.fullmatch(r"\s*verdict\s*:\s*(.*?)\s*", line)
        if match:
            verdict = match.group(1).strip()
            break

    if not verdict:
        return ReviewerReport(
            exists=True,
            verdict=None,
            status="missing_verdict",
            stop_signal=False,
            detail="verdict field is missing or empty",
        )

    normalized = verdict.lower()
    if normalized not in REVIEWER_VERDICTS:
        return ReviewerReport(
            exists=True,
            verdict=verdict,
            status="unknown_verdict",
            stop_signal=False,
            detail="unknown reviewer verdict",
        )
    if normalized in REVIEWER_STOP_VERDICTS:
        return ReviewerReport(
            exists=True,
            verdict=normalized,
            status="stop_signal",
            stop_signal=True,
            detail="plan should not proceed until reviewed and fixed",
        )
    if normalized == "pending":
        return ReviewerReport(
            exists=True,
            verdict=normalized,
            status="not_yet_reviewed",
            stop_signal=False,
            detail="review has not been completed",
        )
    return ReviewerReport(
        exists=True,
        verdict=normalized,
        status="non_blocking",
        stop_signal=False,
        detail="reviewer verdict does not block the plan",
    )


def reviewer_gate_status(reviewer_report: ReviewerReport) -> str:
    if reviewer_report.verdict in REVIEWER_STOP_VERDICTS:
        return "blocked_by_reviewer"
    if reviewer_report.verdict in REVIEWER_OPEN_VERDICTS:
        return "open"
    return "unknown"


def is_queue_header_row(cells: list[str]) -> bool:
    lowered = [cell.lower() for cell in cells[:5]]
    return lowered == ["id", "title", "status", "dependencies", "notes"]


def is_queue_separator_cell(cell: str) -> bool:
    return bool(re.fullmatch(r":?-{3,}:?", cell.strip()))


def is_queue_separator_row(cells: list[str]) -> bool:
    if len(cells) < 5:
        return False
    return all(is_queue_separator_cell(cell) for cell in cells[:5])


def parse_queue_units(queue_path: Path) -> tuple[list[QueueUnit], dict[str, int], list[str]]:
    units: list[QueueUnit] = []
    warnings: list[str] = []
    counts = {status: 0 for status in QUEUE_COUNT_ORDER}

    if not queue_path.exists():
        warnings.append(f"queue file not found: {queue_path}")
        return units, counts, warnings

    seen_ids: dict[str, int] = {}
    in_queue_table = False
    queue_table_closed = False
    for line_number, line in enumerate(read_text(queue_path).splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("|") or not stripped.endswith("|"):
            if in_queue_table:
                in_queue_table = False
                queue_table_closed = True
            continue

        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if queue_table_closed:
            continue
        if is_queue_header_row(cells):
            in_queue_table = True
            continue
        if not in_queue_table:
            continue
        if is_queue_separator_row(cells):
            continue
        if len(cells) < 5:
            warnings.append(
                f"line {line_number}: malformed queue row has {len(cells)} cells, expected at least 5"
            )
            continue

        unit_id, title, raw_status, dependencies = cells[:4]
        notes = " | ".join(cells[4:])
        unit_errors: list[str] = []

        if not unit_id:
            unit_errors.append("empty id")
        elif unit_id in seen_ids:
            unit_errors.append(f"duplicate id also seen on line {seen_ids[unit_id]}")
        else:
            seen_ids[unit_id] = line_number

        normalized_status = raw_status.lower()
        if not normalized_status:
            unit_errors.append("empty status")
            normalized_status = "unknown"
        elif normalized_status not in QUEUE_STATUSES:
            unit_errors.append(f"unknown status: {raw_status}")
            normalized_status = "unknown"

        counts[normalized_status] += 1
        unit = QueueUnit(
            id=unit_id,
            title=title,
            status=normalized_status,
            dependencies=dependencies,
            notes=notes,
            line_number=line_number,
            errors=unit_errors,
        )
        units.append(unit)
        for error in unit_errors:
            label = unit_id if unit_id else "<empty id>"
            warnings.append(f"line {line_number}: {label}: {error}")

    return units, counts, warnings


def parse_unit_dependencies(raw_dependencies: str) -> list[str]:
    stripped = raw_dependencies.strip()
    if not stripped or stripped == "-":
        return []
    return [dependency.strip() for dependency in stripped.split(",") if dependency.strip()]


def queue_units_by_id(units: list[QueueUnit]) -> dict[str, QueueUnit]:
    by_id: dict[str, QueueUnit] = {}
    for unit in units:
        if unit.id and unit.id not in by_id:
            by_id[unit.id] = unit
    return by_id


def dependency_block_reasons(unit: QueueUnit, units_by_id: dict[str, QueueUnit]) -> list[str]:
    reasons: list[str] = []
    for dependency_id in parse_unit_dependencies(unit.dependencies):
        dependency = units_by_id.get(dependency_id)
        if dependency is None:
            reasons.append(f"dependency_missing:{dependency_id}")
        elif dependency.status != "completed":
            reasons.append(f"dependency_not_completed:{dependency_id}")
    return reasons


def select_next_runnable_unit(
    units: list[QueueUnit],
) -> tuple[QueueUnit | None, list[BlockedQueueUnit], dict[str, QueueUnit]]:
    units_by_id = queue_units_by_id(units)
    selected_unit: QueueUnit | None = None
    blocked_units: list[BlockedQueueUnit] = []

    for unit in units:
        if unit.status != "pending":
            continue
        reasons = dependency_block_reasons(unit, units_by_id)
        if reasons:
            blocked_units.append(BlockedQueueUnit(unit=unit, reasons=reasons))
            continue
        if selected_unit is None:
            selected_unit = unit

    return selected_unit, blocked_units, units_by_id


def initial_state(
    validation: dict[str, Any],
    *,
    started_at: str,
    started_in_cwd: Path,
) -> dict[str, Any]:
    task = validation["task"]
    plan = validation["plan"]
    codex_preflight = validation["codex_preflight"]
    env = environment_snapshot(
        started_in_cwd=started_in_cwd,
        codex_version=codex_preflight.get("codex_version"),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": plan["run_id"],
        "task_id": require_string(task, "id"),
        "status": "created",
        "created_at": started_at,
        "updated_at": started_at,
        "repo_path": str(validation["repo_path"]),
        "run_dir": str(plan["run_dir"]),
        "worktree_path": str(plan["worktree_path"]),
        "base_branch": require_string(task, "base_branch"),
        "base_commit": validation["base_commit"],
        "branch": plan["branch"],
        "risk_level": require_string(task, "risk_level"),
        "task_type": require_string(task, "task_type"),
        "allow_edits": require_bool(task, "allow_edits"),
        "allow_push": require_bool(task, "allow_push"),
        "allow_draft_pr": require_bool(task, "allow_draft_pr"),
        "prompt_template": validation["prompt_template"],
        "codex": {
            "model": require_string(task, "codex.model"),
            "effort": require_string(task, "codex.effort"),
            "sandbox": require_string(task, "codex.sandbox"),
            "timeout_minutes": require_positive_number(task, "codex.timeout_minutes"),
            "exit_code": None,
            "timed_out": False,
            "estimated_input_tokens": validation["estimated_input_tokens"],
        },
        "environment": env,
        "errors": [],
        "warnings": [],
        "outputs": output_paths(plan["run_dir"]),
    }


def update_state(state: dict[str, Any], status: str, run_dir: Path) -> None:
    if status not in STATUSES:
        raise ValueError(f"unknown status: {status}")
    state["status"] = status
    state["updated_at"] = now_iso()
    write_json(run_dir / "state.json", state)


def append_journal(
    runs_root: Path,
    *,
    state: dict[str, Any],
    started_monotonic: float,
) -> None:
    runs_root.mkdir(parents=True, exist_ok=True)
    journal_path = runs_root / "journal.jsonl"
    row = {
        "schema_version": SCHEMA_VERSION,
        "run_id": state["run_id"],
        "task_id": state["task_id"],
        "status": state["status"],
        "started_at": state["created_at"],
        "duration_seconds": round(time.monotonic() - started_monotonic, 3),
        "codex_exit_code": state["codex"]["exit_code"],
        "estimated_input_tokens": state["codex"]["estimated_input_tokens"],
        "warnings_count": len(state.get("warnings", [])),
    }
    with open_text(journal_path, "a") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def copy_task_yaml(src: Path, dst: Path) -> None:
    write_text(dst, read_text(src))


def write_marker(path: Path, *, state: dict[str, Any]) -> None:
    marker = "\n".join(
        [
            f"run_id={state['run_id']}",
            f"created_at={state['created_at']}",
            f"branch={state['branch']}",
            f"base_commit={state['base_commit']}",
            "",
        ]
    )
    write_text(path, marker)


def log_preflight_outputs(logger: Logger, validation: dict[str, Any]) -> None:
    codex_help = validation["codex_preflight"].get("codex_exec_help")
    if codex_help:
        logger.log("codex exec --help output follows")
        with open_text(logger.path, "a") as handle:
            handle.write(codex_help.rstrip("\n") + "\n")


def run_codex(
    *,
    state: dict[str, Any],
    task: dict[str, Any],
    prompt_text: str,
    worktree_path: Path,
    run_dir: Path,
    logger: Logger,
) -> None:
    stdout_path = run_dir / "codex_stdout.log"
    stderr_path = run_dir / "codex_stderr.log"
    max_stdout_bytes = int(require_positive_number(task, "limits.max_stdout_mb") * 1024 * 1024)
    max_stderr_bytes = int(require_positive_number(task, "limits.max_stderr_mb") * 1024 * 1024)
    timeout_seconds = float(require_positive_number(task, "codex.timeout_minutes")) * 60
    effort_config = f"model_reasoning_effort={json.dumps(require_string(task, 'codex.effort'))}"
    cmd = [
        "codex",
        "exec",
        "--model",
        require_string(task, "codex.model"),
        "--sandbox",
        require_string(task, "codex.sandbox"),
        "-c",
        effort_config,
        "-",
    ]
    logger.log("RUN " + format_cmd(cmd))
    start = time.monotonic()
    next_size_check = start

    with open_text(stdout_path, "w") as stdout_handle, open_text(stderr_path, "w") as stderr_handle:
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(worktree_path),
                stdin=subprocess.PIPE,
                stdout=stdout_handle,
                stderr=stderr_handle,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError as exc:
            raise CodexError("codex command not found") from exc

        try:
            if proc.stdin is not None:
                try:
                    proc.stdin.write(prompt_text)
                    proc.stdin.close()
                except BrokenPipeError:
                    pass

            while proc.poll() is None:
                now = time.monotonic()
                if now >= next_size_check:
                    stdout_handle.flush()
                    stderr_handle.flush()
                    stdout_size = stdout_path.stat().st_size if stdout_path.exists() else 0
                    stderr_size = stderr_path.stat().st_size if stderr_path.exists() else 0
                    if stdout_size > max_stdout_bytes:
                        proc.kill()
                        proc.wait()
                        state["codex"]["exit_code"] = EXIT_CODEX
                        state["errors"].append(
                            f"codex stdout exceeded limits.max_stdout_mb ({task['limits']['max_stdout_mb']})"
                        )
                        raise CodexError("codex stdout size limit exceeded")
                    if stderr_size > max_stderr_bytes:
                        proc.kill()
                        proc.wait()
                        state["codex"]["exit_code"] = EXIT_CODEX
                        state["errors"].append(
                            f"codex stderr exceeded limits.max_stderr_mb ({task['limits']['max_stderr_mb']})"
                        )
                        raise CodexError("codex stderr size limit exceeded")
                    next_size_check = now + 5
                if now - start > timeout_seconds:
                    proc.kill()
                    proc.wait()
                    state["codex"]["timed_out"] = True
                    state["codex"]["exit_code"] = EXIT_CODEX
                    state["errors"].append("codex execution timed out")
                    raise CodexError("codex execution timed out")
                time.sleep(0.2)

            exit_code = proc.wait()
            state["codex"]["exit_code"] = exit_code
            if exit_code != 0:
                state["errors"].append(f"codex exited with code {exit_code}")
                raise CodexError(f"codex exited with code {exit_code}")
        finally:
            stdout_handle.flush()
            stderr_handle.flush()


def collect_git_outputs(
    *,
    state: dict[str, Any],
    validation: dict[str, Any],
    run_dir: Path,
    worktree_path: Path,
    logger: Logger,
) -> None:
    base_commit = validation["base_commit"]
    raw_status = run_git_output_to_file(
        worktree_path,
        ["status", "--short"],
        run_dir / "git_status_raw.txt",
        logger=logger,
    )
    write_text(run_dir / "git_status.txt", filter_git_status(raw_status))
    run_git_output_to_file(
        worktree_path,
        ["diff", "--stat"],
        run_dir / "git_diff_stat.txt",
        logger=logger,
    )
    run_git_output_to_file(
        worktree_path,
        ["diff"],
        run_dir / "git_diff.patch",
        logger=logger,
    )
    commits = run_git_output_to_file(
        worktree_path,
        ["log", "--oneline", f"{base_commit}..HEAD"],
        run_dir / "git_commits_since_base.txt",
        logger=logger,
    )
    run_git_output_to_file(
        worktree_path,
        ["diff", f"{base_commit}...HEAD"],
        run_dir / "git_branch_diff.patch",
        logger=logger,
    )

    objective = require_string(validation["task"], "objective").lower()
    if commits.strip() and "commit" not in objective:
        state["warnings"].append("commits exist but the task objective did not explicitly require commits")


def filter_git_status(raw_status: str) -> str:
    kept_lines = []
    for line in raw_status.splitlines():
        if line[3:] == ".hermes-managed":
            continue
        kept_lines.append(line)
    if not kept_lines:
        return ""
    return "\n".join(kept_lines) + "\n"


def run_task(task_path: Path, *, execute: bool) -> int:
    started_at = now_iso()
    started_monotonic = time.monotonic()
    started_in_cwd = Path.cwd()
    state: dict[str, Any] | None = None
    run_dir: Path | None = None
    runs_root: Path | None = None
    logger: Logger | None = None

    try:
        validation = validate_task(task_path, execute=execute)
        task = validation["task"]
        plan = validation["plan"]
        runs_root = plan["runs_root"]
        run_dir = plan["run_dir"]
        worktree_path = plan["worktree_path"]

        run_dir.mkdir(parents=True, exist_ok=False)
        logger = Logger(run_dir / "hermes.log", validation["preflight_log"])
        logger.log(f"Hermes v{HERMES_VERSION} run started")
        logger.log(f"base_commit={validation['base_commit']}")
        log_preflight_outputs(logger, validation)

        state = initial_state(validation, started_at=started_at, started_in_cwd=started_in_cwd)
        update_state(state, "created", run_dir)
        update_state(state, "validated", run_dir)

        copy_task_yaml(task_path, run_dir / "task.yaml")
        write_text(run_dir / "codex_stdout.log", "")
        write_text(run_dir / "codex_stderr.log", "")
        update_state(state, "run_dir_created", run_dir)

        run_git(
            validation["repo_path"],
            [
                "worktree",
                "add",
                str(worktree_path),
                "-b",
                plan["branch"],
                require_string(task, "base_branch"),
            ],
            logger=logger,
        )
        write_marker(worktree_path / ".hermes-managed", state=state)
        update_state(state, "worktree_created", run_dir)

        write_text(run_dir / "prompt.md", validation["prompt_text"])
        update_state(state, "prompt_built", run_dir)

        codex_error: CodexError | None = None
        if execute:
            update_state(state, "running_codex", run_dir)
            try:
                run_codex(
                    state=state,
                    task=task,
                    prompt_text=validation["prompt_text"],
                    worktree_path=worktree_path,
                    run_dir=run_dir,
                    logger=logger,
                )
                update_state(state, "codex_completed", run_dir)
            except CodexError as exc:
                codex_error = exc
                update_state(state, "failed", run_dir)

        update_state(state, "collecting_git_outputs", run_dir)
        collect_git_outputs(
            state=state,
            validation=validation,
            run_dir=run_dir,
            worktree_path=worktree_path,
            logger=logger,
        )

        if codex_error is not None:
            update_state(state, "failed", run_dir)
            append_journal(runs_root, state=state, started_monotonic=started_monotonic)
            return EXIT_CODEX

        final_status = "completed_with_warnings" if state["warnings"] else "completed"
        update_state(state, final_status, run_dir)
        append_journal(runs_root, state=state, started_monotonic=started_monotonic)
        print(f"run_id: {state['run_id']}")
        print(f"status: {state['status']}")
        print(f"run_dir: {run_dir}")
        print(f"worktree_path: {worktree_path}")
        return EXIT_SUCCESS
    except HermesError as exc:
        if state is not None and run_dir is not None:
            state["errors"].append(str(exc))
            update_state(state, "failed", run_dir)
            if runs_root is not None:
                append_journal(runs_root, state=state, started_monotonic=started_monotonic)
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:
        if state is not None and run_dir is not None:
            state["errors"].append(str(exc))
            update_state(state, "failed", run_dir)
            if runs_root is not None:
                append_journal(runs_root, state=state, started_monotonic=started_monotonic)
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_GENERAL


def validate_command(task_path: Path) -> int:
    try:
        validation = validate_task(task_path, execute=False)
    except HermesError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return exc.exit_code
    print("validation ok")
    print(f"base_commit: {validation['base_commit']}")
    print(f"context_files: {len(validation['context_entries'])}")
    print(f"prompt_chars: {len(validation['prompt_text'])}")
    print(f"estimated_input_tokens: {validation['estimated_input_tokens']}")
    return EXIT_SUCCESS


def dry_run_command(task_path: Path) -> int:
    try:
        validation = validate_task(task_path, execute=False)
    except HermesError as exc:
        print(f"dry-run validation failed: {exc}", file=sys.stderr)
        return exc.exit_code

    plan = validation["plan"]
    print(f"planned run_id: {plan['run_id']}")
    print(f"branch: {plan['branch']}")
    print(f"run_dir: {plan['run_dir']}")
    print(f"worktree_path: {plan['worktree_path']}")
    print(f"base_commit: {validation['base_commit']}")
    print("context files:")
    for entry in validation["context_entries"]:
        print(f"- {entry['path']}")
    print(f"prompt size chars: {len(validation['prompt_text'])}")
    print(f"estimated input tokens: {validation['estimated_input_tokens']}")
    print("codex pre-flight would be needed: no")
    return EXIT_SUCCESS


def list_command(runs_root: Path, *, limit: int) -> int:
    if limit <= 0:
        print("list failed: --limit must be positive", file=sys.stderr)
        return EXIT_VALIDATION

    runs_root = runs_root.expanduser()
    journal_path = runs_root / "journal.jsonl"
    if not journal_path.exists():
        print(f"journal not found: {journal_path}")
        return EXIT_SUCCESS

    rows: list[dict[str, Any]] = []
    try:
        with open_text(journal_path, "r") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
    except Exception as exc:
        print(f"list failed: failed to read {journal_path}: {exc}", file=sys.stderr)
        return EXIT_VALIDATION

    print(
        "run_id\ttask_id\tstatus\tduration_seconds\tcodex_exit_code\t"
        "estimated_input_tokens"
    )
    for row in rows[-limit:]:
        print(
            "\t".join(
                str(row.get(key, ""))
                for key in [
                    "run_id",
                    "task_id",
                    "status",
                    "duration_seconds",
                    "codex_exit_code",
                    "estimated_input_tokens",
                ]
            )
        )
    return EXIT_SUCCESS


def find_run_state(runs_root: Path, run_id: str) -> dict[str, Any]:
    if not run_id.strip():
        raise ValidationError("run_id must not be empty")

    direct_state_path = runs_root / run_id / "state.json"
    if direct_state_path.exists():
        return read_json(direct_state_path)

    if not runs_root.exists():
        raise ValidationError(f"runs_root does not exist: {runs_root}")
    if not runs_root.is_dir():
        raise ValidationError(f"runs_root is not a directory: {runs_root}")

    for child in sorted(runs_root.iterdir()):
        if not child.is_dir():
            continue
        state_path = child / "state.json"
        if not state_path.exists():
            continue
        try:
            state = read_json(state_path)
        except HermesError:
            continue
        if state.get("run_id") == run_id:
            return state

    raise ValidationError(f"run not found under {runs_root}: {run_id}")


def status_command(runs_root: Path, run_id: str) -> int:
    runs_root = runs_root.expanduser()
    try:
        state = find_run_state(runs_root, run_id)
    except HermesError as exc:
        print(f"status failed: {exc}", file=sys.stderr)
        return exc.exit_code

    codex = state.get("codex", {})
    if not isinstance(codex, dict):
        codex = {}
    warnings = state.get("warnings", [])
    errors = state.get("errors", [])
    outputs = state.get("outputs", {})

    print(f"run_id: {state.get('run_id', '')}")
    print(f"task_id: {state.get('task_id', '')}")
    print(f"status: {state.get('status', '')}")
    print(f"created_at: {state.get('created_at', '')}")
    print(f"updated_at: {state.get('updated_at', '')}")
    print(f"repo_path: {state.get('repo_path', '')}")
    print(f"worktree_path: {state.get('worktree_path', '')}")
    print(f"base_commit: {state.get('base_commit', '')}")
    print(f"branch: {state.get('branch', '')}")
    print(f"codex_exit_code: {codex.get('exit_code', '')}")
    print(f"codex_timed_out: {codex.get('timed_out', '')}")
    print(f"codex_estimated_input_tokens: {codex.get('estimated_input_tokens', '')}")
    print(f"warnings: {len(warnings) if isinstance(warnings, list) else 0}")
    print(f"errors: {len(errors) if isinstance(errors, list) else 0}")
    print("outputs:")
    if isinstance(outputs, dict):
        for key, value in outputs.items():
            print(f"- {key}: {value}")
    return EXIT_SUCCESS


def plan_init_command(plan_id: str, *, title: str, objective: str, force: bool) -> int:
    try:
        paths = plan_paths(plan_id)
        root = paths["root"]
        plans_root = paths["plans_root"]
        plan_dir = paths["plan_dir"]
        inbox_path = paths["inbox"]

        if plan_dir.exists() and not plan_dir.is_dir():
            raise ValidationError(f"plan path exists and is not a directory: {plan_dir}")
        if plan_dir.exists() and not force:
            raise ValidationError(f"plan already exists: {plan_id} (use --force to overwrite scaffold files)")

        root.mkdir(parents=True, exist_ok=True)
        plans_root.mkdir(parents=True, exist_ok=True)
        if not inbox_path.exists():
            write_text(inbox_path, "# Hermes Inbox\n\n")

        plan_dir.mkdir(parents=True, exist_ok=True)
        created_at = now_iso()
        files = {
            "plan": str(paths["plan.md"]),
            "queue": str(paths["queue.md"]),
            "log": str(paths["log.md"]),
            "state": str(paths["state.json"]),
            "morning_brief": str(paths["morning_brief.md"]),
            "reviewer_report": str(paths["reviewer_report.md"]),
        }
        state = {
            "schema_version": SCHEMA_VERSION,
            "hermes_version": HERMES_VERSION,
            "plan_id": plan_id,
            "title": title,
            "objective": objective,
            "status": "created",
            "created_at": created_at,
            "updated_at": created_at,
            "plan_dir": str(plan_dir),
            "files": files,
        }

        write_text(paths["plan.md"], render_plan_md(title=title, objective=objective))
        write_text(paths["queue.md"], render_queue_md())
        write_text(paths["log.md"], render_plan_log_md(created_at=created_at))
        write_json(paths["state.json"], state)
        write_text(paths["morning_brief.md"], render_morning_brief_md(title=title))
        write_text(paths["reviewer_report.md"], render_reviewer_report_md())
    except HermesError as exc:
        print(f"plan-init failed: {exc}", file=sys.stderr)
        return exc.exit_code

    print(f"plan_id: {plan_id}")
    print("status: created")
    print(f"plan_dir: {paths['plan_dir']}")
    return EXIT_SUCCESS


def plan_status_command(plan_id: str) -> int:
    try:
        paths = plan_paths(plan_id)
        plan_dir = paths["plan_dir"]
        state_path = paths["state.json"]
        if not plan_dir.exists():
            raise ValidationError(f"plan does not exist: {plan_id}")
        if not state_path.exists():
            raise ValidationError(f"plan state not found: {state_path}")
        state = read_json(state_path)
        units, counts, warnings = parse_queue_units(paths["queue.md"])
        reviewer_report = parse_reviewer_report(paths["reviewer_report.md"])
        review_gate = reviewer_gate_status(reviewer_report)
    except HermesError as exc:
        print(f"plan-status failed: {exc}", file=sys.stderr)
        return exc.exit_code

    print(f"plan_id: {state.get('plan_id', '')}")
    print(f"title: {state.get('title', '')}")
    print(f"status: {state.get('status', '')}")
    print(f"created_at: {state.get('created_at', '')}")
    print(f"updated_at: {state.get('updated_at', '')}")
    print(f"plan_dir: {state.get('plan_dir', plan_dir)}")
    print(f"review_gate: {review_gate}")
    print("reviewer_report:")
    print(f"- exists: {'yes' if reviewer_report.exists else 'no'}")
    print(f"- path: {paths['reviewer_report.md']}")
    print(f"- verdict: {reviewer_report.verdict or 'missing'}")
    print(f"- status: {reviewer_report.status}")
    print(f"- stop_signal: {'yes' if reviewer_report.stop_signal else 'no'}")
    print(f"- detail: {reviewer_report.detail}")
    print("queue_counts:")
    for status in QUEUE_COUNT_ORDER:
        print(f"- {status}: {counts.get(status, 0)}")
    print("queue_units:")
    if units:
        print("line\tid\tstatus\tdependencies\ttitle\tnotes")
        for unit in units:
            print(
                "\t".join(
                    [
                        str(unit.line_number),
                        unit.id,
                        unit.status,
                        unit.dependencies,
                        unit.title,
                        unit.notes,
                    ]
                )
            )
    else:
        print("(none)")
    print(f"warnings: {len(warnings)}")
    if warnings:
        print("warnings_detail:")
        for warning in warnings:
            print(f"- {warning}")
    return EXIT_SUCCESS


def run_next_command(plan_id: str, *, dry_run: bool) -> int:
    if not dry_run:
        print("run-next failed: real execution is not implemented in v0.2-C; use --dry-run", file=sys.stderr)
        return EXIT_VALIDATION

    try:
        paths = plan_paths(plan_id)
        plan_dir = paths["plan_dir"]
        state_path = paths["state.json"]
        if not plan_dir.exists():
            raise ValidationError(f"plan does not exist: {plan_id}")
        if not state_path.exists():
            raise ValidationError(f"plan state not found: {state_path}")
        state = read_json(state_path)
        units, _counts, warnings = parse_queue_units(paths["queue.md"])
        selected_unit, blocked_units, units_by_id = select_next_runnable_unit(units)
    except HermesError as exc:
        print(f"run-next failed: {exc}", file=sys.stderr)
        return exc.exit_code

    completed_units = [
        unit_id
        for unit_id, unit in units_by_id.items()
        if unit.status == "completed"
    ]

    print(f"plan_id: {state.get('plan_id', plan_id)}")
    print("mode: dry-run")
    if selected_unit is None:
        print("selected_unit: none")
    else:
        print(f"selected_unit: {selected_unit.id}")
    print("blocked_units:")
    if blocked_units:
        print("line\tid\treasons\ttitle")
        for blocked in blocked_units:
            print(
                "\t".join(
                    [
                        str(blocked.unit.line_number),
                        blocked.unit.id,
                        ",".join(blocked.reasons),
                        blocked.unit.title,
                    ]
                )
            )
    else:
        print("(none)")
    print("completed_dependency_map_summary:")
    print(f"- completed_count: {len(completed_units)}")
    if completed_units:
        print(f"- completed_units: {', '.join(completed_units)}")
    else:
        print("- completed_units: none")
    print(f"queue_parser_warnings: {len(warnings)}")
    if warnings:
        print("queue_parser_warnings_detail:")
        for warning in warnings:
            print(f"- {warning}")
    return EXIT_SUCCESS


def parse_older_than(value: str) -> timedelta:
    if len(value) < 2:
        raise ValidationError("--older-than must look like 7d, 12h, or 30m")
    unit = value[-1]
    number_text = value[:-1]
    try:
        amount = int(number_text)
    except ValueError as exc:
        raise ValidationError("--older-than must start with an integer") from exc
    if amount <= 0:
        raise ValidationError("--older-than must be positive")
    if unit == "d":
        return timedelta(days=amount)
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "m":
        return timedelta(minutes=amount)
    raise ValidationError("--older-than unit must be d, h, or m")


def read_json(path: Path) -> dict[str, Any]:
    try:
        with open_text(path, "r") as handle:
            data = json.load(handle)
    except Exception as exc:
        raise ValidationError(f"failed to read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return data


def parse_state_time(value: Any, fallback_path: Path) -> datetime:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.fromtimestamp(fallback_path.stat().st_mtime).astimezone()


def is_hermes_run_dir(run_dir: Path) -> tuple[bool, dict[str, Any] | None]:
    state_path = run_dir / "state.json"
    if not state_path.exists():
        return False, None
    try:
        state = read_json(state_path)
        if state.get("schema_version") != SCHEMA_VERSION:
            return False, None
        run_id = state.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            return False, None
        worktree_value = state.get("worktree_path")
        if not isinstance(worktree_value, str) or not worktree_value:
            return False, None
        resolved_run_dir = run_dir.resolve()
        worktree_path = Path(worktree_value).expanduser().resolve()
        try:
            worktree_path.relative_to(resolved_run_dir)
        except ValueError:
            return False, None
        marker_path = worktree_path / ".hermes-managed"
        if not marker_path.exists():
            return False, None
        marker = read_text(marker_path)
        if f"run_id={run_id}" not in marker:
            return False, None
        return True, state
    except Exception:
        return False, None


def cleanup_command(runs_root: Path, *, dry_run: bool, older_than: str) -> int:
    try:
        threshold = parse_older_than(older_than)
    except HermesError as exc:
        print(f"cleanup failed: {exc}", file=sys.stderr)
        return exc.exit_code

    runs_root = runs_root.expanduser()
    if not runs_root.exists():
        print(f"runs_root does not exist: {runs_root}")
        return EXIT_SUCCESS
    cutoff = now_local() - threshold
    removed = 0
    candidates = 0

    for child in sorted(runs_root.iterdir()):
        if not child.is_dir():
            continue
        owned, state = is_hermes_run_dir(child)
        if not owned or state is None:
            continue
        created = parse_state_time(state.get("created_at"), child)
        if created > cutoff:
            continue
        candidates += 1
        worktree_path = Path(state["worktree_path"]).expanduser()
        repo_path = Path(state.get("repo_path", "")).expanduser()
        if dry_run:
            print(f"would remove: {child}")
            continue
        if worktree_path.exists():
            try:
                result = run_process(
                    [
                        "git",
                        "-C",
                        str(repo_path),
                        "worktree",
                        "remove",
                        str(worktree_path),
                        "--force",
                    ]
                )
            except HermesError as exc:
                print(
                    f"skipped, git worktree remove failed for {child}: {exc}",
                    file=sys.stderr,
                )
                continue
            if result.returncode != 0:
                print(
                    "skipped, git worktree remove failed for "
                    f"{child}: {result.stderr.strip() or result.stdout.strip()}",
                    file=sys.stderr,
                )
                continue
        if worktree_path.exists():
            print(f"skipped, worktree still exists after git removal: {worktree_path}", file=sys.stderr)
            continue
        shutil.rmtree(child)
        removed += 1
        print(f"removed: {child}")

    if dry_run:
        print(f"cleanup candidates: {candidates}")
    else:
        print(f"cleanup removed: {removed}")
    return EXIT_SUCCESS


def ensure_improvements_file() -> None:
    path = Path("IMPROVEMENTS.md")
    if path.exists():
        return
    write_text(path, "# Hermes Improvements\n\n## Inbox\n-\n\n## Triaged\n-\n\n## Done\n-\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes v0 local single-task runner")
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser("validate", help="validate a task.yaml")
    validate_parser.add_argument("task_yaml")

    dry_run_parser = subparsers.add_parser("dry-run", help="validate and print planned run details")
    dry_run_parser.add_argument("task_yaml")

    run_parser = subparsers.add_parser("run", help="create a worktree and optionally run Codex")
    run_parser.add_argument("task_yaml")
    run_mode = run_parser.add_mutually_exclusive_group(required=True)
    run_mode.add_argument("--no-codex", action="store_true", help="do not run codex exec")
    run_mode.add_argument("--execute", action="store_true", help="run codex exec")

    list_parser = subparsers.add_parser("list", help="list recent Hermes runs")
    list_parser.add_argument(
        "--runs-root",
        default="~/hermes-runs",
        help="runs root containing journal.jsonl; defaults to ~/hermes-runs",
    )
    list_parser.add_argument("--limit", type=int, default=10, help="number of recent runs to show")

    status_parser = subparsers.add_parser("status", help="show a Hermes run summary")
    status_parser.add_argument("run_id")
    status_parser.add_argument(
        "--runs-root",
        default="~/hermes-runs",
        help="runs root containing run dirs; defaults to ~/hermes-runs",
    )

    plan_init_parser = subparsers.add_parser("plan-init", help="create a local plan scaffold")
    plan_init_parser.add_argument("plan_id")
    plan_init_parser.add_argument("--title", required=True, help="human-readable plan title")
    plan_init_parser.add_argument("--objective", required=True, help="plan objective")
    plan_init_parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite scaffold files inside the exact plan directory",
    )

    plan_status_parser = subparsers.add_parser("plan-status", help="show a local plan summary")
    plan_status_parser.add_argument("plan_id")

    run_next_parser = subparsers.add_parser("run-next", help="select the next runnable plan unit")
    run_next_parser.add_argument("plan_id")
    run_next_parser.add_argument("--dry-run", action="store_true", help="select without executing a unit")

    cleanup_parser = subparsers.add_parser("cleanup", help="remove old Hermes-owned run dirs")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="show what would be removed")
    cleanup_parser.add_argument("--older-than", required=True, help="age threshold such as 7d")
    cleanup_parser.add_argument(
        "--runs-root",
        default="~/hermes-runs",
        help="runs root to clean; defaults to ~/hermes-runs",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    ensure_improvements_file()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return validate_command(Path(args.task_yaml))
    if args.command == "dry-run":
        return dry_run_command(Path(args.task_yaml))
    if args.command == "run":
        return run_task(Path(args.task_yaml), execute=args.execute)
    if args.command == "list":
        return list_command(Path(args.runs_root), limit=args.limit)
    if args.command == "status":
        return status_command(Path(args.runs_root), args.run_id)
    if args.command == "plan-init":
        return plan_init_command(
            args.plan_id,
            title=args.title,
            objective=args.objective,
            force=args.force,
        )
    if args.command == "plan-status":
        return plan_status_command(args.plan_id)
    if args.command == "run-next":
        return run_next_command(args.plan_id, dry_run=args.dry_run)
    if args.command == "cleanup":
        return cleanup_command(
            Path(args.runs_root),
            dry_run=args.dry_run,
            older_than=args.older_than,
        )

    parser.print_help()
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
