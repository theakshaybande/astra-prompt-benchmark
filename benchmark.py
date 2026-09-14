"""Reproducible Task 001 runner. Python 3.10+, Git; no third-party packages."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

from validators.market_clock import validate

ROOT = Path(__file__).resolve().parent
COLUMNS = "run_id timestamp model prompt_type baseline_commit duration_seconds task_success validation_passed files_changed lines_added lines_deleted php_validation js_validation timezone_validation hardcoded_offset_detected user_interventions manual_correctness_score manual_visual_score manual_scope_score notes".split()


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def within(path, parent):
    return path.resolve().is_relative_to(parent.resolve())


def disjoint(a, b):
    return not within(a, b) and not within(b, a)


def reject_links(path):
    """Reject symlinks and Windows reparse points, including junctions."""
    for item in [path, *path.parents]:
        if item.exists() and (item.is_symlink() or getattr(item.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError(f"Linked/reparse path is not allowed: {item}")


def check_tree(path):
    reject_links(path)
    for current, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            reject_links(Path(current) / name)


def load_config(path):
    # JSON is a YAML 1.2 subset. Require this subset to avoid a PyYAML dependency.
    cfg = json.loads(path.read_text(encoding="utf-8-sig"))
    source = Path(cfg["source_repo"]).resolve(strict=True)
    if not disjoint(source, ROOT):
        raise ValueError("Benchmark and source directories must be disjoint.")
    if not re.fullmatch(r"[0-9a-f]{40}", cfg["baseline_commit"]):
        raise ValueError("Pin baseline_commit to a full 40-character Git commit SHA.")
    if not isinstance(cfg["command"], list) or not all(isinstance(v, str) for v in cfg["command"]):
        raise ValueError("command must be an argument array, not shell text.")
    if float(cfg["timeout_seconds"]) <= 0:
        raise ValueError("timeout_seconds must be positive.")
    for folder in (ROOT / "runs", ROOT / "results", ROOT / "results/diffs", ROOT / "results/logs"):
        reject_links(folder)
        folder.mkdir(parents=True, exist_ok=True)
    return cfg, source


def git_env(source=None):
    # Do not inherit GIT_DIR, GIT_WORK_TREE, alternate object stores, etc.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    if source:
        env.update(GIT_CONFIG_COUNT="2", GIT_CONFIG_KEY_0="safe.directory",
                   GIT_CONFIG_VALUE_0=source.as_posix(), GIT_CONFIG_KEY_1="safe.directory",
                   GIT_CONFIG_VALUE_1=(source / ".git").as_posix())
    return env


def git(repo, *args, env=None):
    result = subprocess.run(["git", "-c", "core.hooksPath=NUL" if os.name == "nt" else "core.hooksPath=/dev/null",
                             "-c", "core.autocrlf=false", "-C", str(repo), *args],
                            env=env or git_env(), capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace"))
    return result.stdout


def source_read(source, *args):
    # Deliberately no generic source mutation escape hatch.
    if args[0] not in {"rev-parse", "status", "cat-file", "ls-tree"}:
        raise ValueError("Only allowlisted read-only Git operations may target the source.")
    return git(source, *args, env=git_env(source)).decode("utf-8", "replace").strip()


def source_state(source):
    return {"head": source_read(source, "rev-parse", "HEAD"),
            "status": source_read(source, "status", "--porcelain=v1", "--untracked-files=all")}


def writable_repo(repo, source):
    reject_links(repo)
    if not within(repo, ROOT / "runs") or repo.resolve() == (ROOT / "runs").resolve() or not disjoint(repo, source):
        raise ValueError(f"Unsafe experiment directory: {repo}")
    if repo.exists():
        check_tree(repo)
        if not (repo / ".git").is_dir():
            raise ValueError("Experiment must have its own .git directory, not a shared worktree.")
        actual = Path(git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
        gitdir = Path(git(repo, "rev-parse", "--absolute-git-dir").decode().strip()).resolve()
        if actual != repo.resolve() or gitdir != (repo / ".git").resolve():
            raise ValueError("Experiment Git metadata escapes the isolated checkout.")
        if (gitdir / "objects/info/alternates").exists():
            raise ValueError("Shared Git object stores are not permitted.")


def clone_baseline(repo, source, baseline):
    writable_repo(repo, source)
    # bundle create reads source objects and writes ONLY this explicitly confined output.
    # Cloning a bundle avoids shared objects and ownership checks in upload-pack subprocesses.
    bundle = repo.parent / "source.bundle"
    reject_links(bundle)
    if not within(bundle, ROOT / "runs") or not disjoint(bundle, source):
        raise ValueError("Unsafe bundle output.")
    git(source, "bundle", "create", str(bundle), "--all", baseline, env=git_env(source))
    git(ROOT, "clone", "--no-checkout", "--", str(bundle), str(repo))
    writable_repo(repo, source)
    git(repo, "remote", "remove", "origin")
    # Refuse checked-in links before materializing them on Windows.
    tree = git(repo, "ls-tree", "-r", baseline).decode("utf-8", "replace")
    if any(line.startswith(("120000 ", "160000 ")) for line in tree.splitlines()):
        raise ValueError("Baseline contains symlinks or submodules; provision a safe fixture first.")
    git(repo, "checkout", "--detach", baseline)
    if git(repo, "rev-parse", "HEAD").decode().strip() != baseline or git(repo, "status", "--porcelain").strip():
        raise RuntimeError("Clone is not clean at the pinned baseline.")


def snapshot(repo, run_dir, source, baseline):
    writable_repo(repo, source)
    status = git(repo, "status", "--porcelain=v1", "--untracked-files=all").decode("utf-8", "replace")
    # A separate index includes new files and committed changes without altering the agent's index.
    env = git_env()
    env["GIT_INDEX_FILE"] = str(run_dir / "snapshot.index")
    git(repo, "read-tree", baseline, env=env)
    git(repo, "add", "-A", "--", ".", env=env)
    common = ("diff", "--cached", "--no-ext-diff", "--no-textconv", "--no-renames")
    diff = git(repo, *common, "--binary", baseline, env=env)
    names = git(repo, *common, "--name-only", "-z", baseline, env=env).decode("utf-8", "replace").split("\0")
    stats = git(repo, *common, "--numstat", "-z", baseline, env=env).decode("utf-8", "replace")
    added = deleted = binaries = 0
    for record in filter(None, stats.split("\0")):
        a, d, _ = record.split("\t", 2)
        if a == "-":
            binaries += 1
        else:
            added += int(a)
            deleted += int(d)
    return diff, list(filter(None, names)), added, deleted, binaries, status


def invoke(command, repo, prompt, log_dir, timeout):
    """No shell interpolation; stream logs to disk and kill the process tree on timeout."""
    with (log_dir / "stdout.log").open("wb") as out, (log_dir / "stderr.log").open("wb") as err:
        process = subprocess.Popen(command, cwd=repo, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                   env=git_env(), start_new_session=os.name != "nt")
        try:
            process.communicate(prompt.encode("utf-8"), timeout=timeout)
            return process.returncode
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            if os.name == "nt":
                killed = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                        capture_output=True, timeout=10)
                if killed.returncode and process.poll() is None:
                    err.write(b"\nProcess-tree termination failed; killing direct process. Check for descendants.\n")
                    err.write(killed.stderr)
                    process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=15)
            raise


def tool_version(command):
    try:
        p = subprocess.run(command, capture_output=True, text=True, timeout=15)
        return (p.stdout + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return str(exc)


def append_row(row):
    path = ROOT / "results/results.csv"
    reject_links(path)
    if path.exists() and path.stat().st_size:
        with path.open(newline="", encoding="utf-8") as f:
            if next(csv.reader(f)) != COLUMNS:
                raise ValueError("Existing CSV header differs; archive it before continuing.")
    new = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if new:
            writer.writeheader()
        writer.writerow(row)


def experiment(cfg, source, model_key, style, dry_run):
    baseline = cfg["baseline_commit"]
    before = source_state(source)
    source_read(source, "cat-file", "-e", baseline + "^{commit}")
    timestamp = datetime.now(timezone.utc).isoformat()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + ("dry_" if dry_run else "") + model_key + "_" + style + "_" + uuid4().hex[:8]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Model and prompt keys must use only letters, digits, underscores or hyphens.")
    run_dir = ROOT / "runs" / run_id
    run_dir.mkdir()
    repo = run_dir / "repo"
    log_dir = ROOT / "results/logs" / run_id
    log_dir.mkdir()
    task_path = (ROOT / cfg["prompts"][style]).resolve()
    if not within(task_path, ROOT / "prompts"):
        raise ValueError("Task prompt must be inside prompts/.")
    task = task_path.read_text(encoding="utf-8")
    prompt = (ROOT / "prompts/isolation.txt").read_text(encoding="utf-8") + "\n" + task
    (run_dir / "task_prompt.txt").write_text(task, encoding="utf-8")
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    response = run_dir / "final_response.txt"
    values = {"model": cfg["models"][model_key], "repo": str(repo), "run_dir": str(run_dir),
              "prompt_file": str(run_dir / "prompt.txt"), "response_file": str(response)}
    command = [arg.format_map(values) for arg in cfg["command"]]
    metadata = {"run_id": run_id, "timestamp": timestamp, "dry_run": dry_run,
                "model": values["model"], "prompt_type": style, "baseline_commit": baseline,
                "source_before": before, "command": command, "config": cfg,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "python": sys.version, "git": tool_version(["git", "--version"]),
                "node": tool_version(["node", "--version"]), "php": tool_version(["php", "--version"]),
                "cli_version": "not invoked (dry run)" if dry_run else tool_version(cfg["version_command"]),
                "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "validator_sha256": hashlib.sha256((ROOT / "validators/market_clock.py").read_bytes()).hexdigest()}
    save_json(run_dir / "metadata.json", metadata)
    row = dict.fromkeys(COLUMNS, "")
    row.update({k: metadata[k] for k in ("run_id", "timestamp", "model", "prompt_type", "baseline_commit")})
    row.update(task_success="not_evaluated" if dry_run else "needs_manual_review", validation_passed="error")
    error = ""
    exit_code = None
    start = time.perf_counter()
    try:
        clone_baseline(repo, source, baseline)
        metadata["start_commit"] = git(repo, "rev-parse", "HEAD").decode().strip()
        agent_start = time.perf_counter()
        if dry_run:
            # Deliberately not a working clock: exercise new-file, diff and validator paths.
            (repo / "benchmark-dry-run.js").write_text(
                '// DRY RUN FIXTURE: not an implementation\n'
                'const benchmarkZones = ["Asia/Tokyo", "Europe/London", "America/New_York"];\n', encoding="utf-8")
            (log_dir / "stdout.log").write_text("DRY RUN: simulated agent; no model invoked.\n", encoding="utf-8")
            (log_dir / "stderr.log").write_text("", encoding="utf-8")
            response.write_text("DRY RUN ONLY. Added syntax-valid timezone fixture. No clock implemented.\n", encoding="utf-8")
            exit_code = 0
        else:
            exit_code = invoke(command, repo, prompt, log_dir, float(cfg["timeout_seconds"]))
        metadata["agent_duration_seconds"] = round(time.perf_counter() - agent_start, 3)
        if exit_code:
            error = f"Agent exited with code {exit_code}."
    except (Exception, KeyboardInterrupt) as exc:
        error = f"{type(exc).__name__}: {exc}"
    try:
        diff, names, added, deleted, binaries, status = snapshot(repo, run_dir, source, baseline)
        (ROOT / "results/diffs" / (run_id + ".patch")).write_bytes(diff)
        checks = validate(repo, names, status)
        save_json(log_dir / "validation.json", checks)
        save_json(run_dir / "changed_files.json", names)
        (log_dir / "git_status.txt").write_text(status, encoding="utf-8")
        row.update({k: checks[k] for k in ("validation_passed", "php_validation", "js_validation", "timezone_validation", "hardcoded_offset_detected")})
        row.update(files_changed=len(names), lines_added=added, lines_deleted=deleted)
        metadata["binary_files_changed"] = binaries
        metadata["final_commit"] = git(repo, "rev-parse", "HEAD").decode().strip()
    except Exception as exc:
        error += f" Snapshot/validation error: {exc}"
    after = source_state(source)
    metadata["source_after"] = after
    if after != before:
        error += " Source HEAD/status changed during experiment; stop and investigate."
    if not response.exists():
        response.write_text("No final agent response was produced. Inspect stdout/stderr logs.\n", encoding="utf-8")
    for name in ("stdout.log", "stderr.log"):
        (log_dir / name).touch(exist_ok=True)
    row["duration_seconds"] = round(time.perf_counter() - start, 3)
    if error:
        row["task_success"] = "error"
    row["notes"] = ("DRY RUN; fixture only; no model call. " if dry_run else "Manual correctness/visual/scope review required. ") + error
    metadata.update(exit_code=exit_code, error=error, duration_seconds=row["duration_seconds"], completed=True)
    save_json(run_dir / "metadata.json", metadata)
    save_json(run_dir / "result.json", row)
    append_row(row)
    print(json.dumps(row, indent=2))
    print(f"Preserved run: {run_dir}")
    return not error


def clean_run(run_id, source, confirmed):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID.")
    path = ROOT / "runs" / run_id
    if not path.is_dir() or not (path / "metadata.json").is_file():
        raise ValueError("Not a recognized benchmark run.")
    check_tree(path)
    if not within(path, ROOT / "runs") or not disjoint(path, source):
        raise ValueError("Unsafe cleanup target.")
    print(f"Cleanup target: {path.resolve()}")
    if not confirmed:
        print("Preview only. Add --confirm to remove this run. CSV, diffs and logs are retained.")
        return
    def onerror(func, name, exc):
        os.chmod(name, 0o700)  # Git object files can be read-only on Windows.
        func(name)
    shutil.rmtree(path, onerror=onerror)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    parser.add_argument("--model", help="Model key from config.yaml, e.g. older or astra")
    parser.add_argument("--prompt", choices=["minimal", "detailed"])
    parser.add_argument("--all", action="store_true", help="Run the configured matrix sequentially")
    parser.add_argument("--dry-run", action="store_true", help="Exercise workflow without model calls")
    parser.add_argument("--clean-run", metavar="RUN_ID", help="Preview cleanup of one preserved run")
    parser.add_argument("--confirm", action="store_true", help="Confirm explicit --clean-run deletion")
    args = parser.parse_args()
    cfg, source = load_config(args.config)
    lock = ROOT / "results/.benchmark.lock"
    reject_links(lock)
    try:
        handle = lock.open("x")
    except FileExistsError:
        raise ValueError("Another runner may be active; see README for stale lock recovery.")
    try:
        with handle:
            handle.write(str(os.getpid()))
        if args.clean_run:
            clean_run(args.clean_run, source, args.confirm)
            return 0
        if args.confirm or (args.all and (args.model or args.prompt)):
            parser.error("Use --all OR --model/--prompt; --confirm is only for --clean-run.")
        if not args.all and not (args.model and args.prompt):
            parser.error("Choose --all or both --model and --prompt.")
        matrix = [(m, p) for m in cfg["models"] for p in cfg["prompts"]] if args.all else [(args.model, args.prompt)]
        for m, p in matrix:
            if m not in cfg["models"] or p not in cfg["prompts"]:
                parser.error("Unknown model or prompt key.")
            if not experiment(cfg, source, m, p, args.dry_run):
                return 1
        return 0
    finally:
        lock.unlink()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
