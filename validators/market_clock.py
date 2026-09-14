"""Dependency-free, deliberately conservative checks with per-file evidence."""
import re
import shutil
import subprocess
from pathlib import Path

ZONES = ("Asia/Tokyo", "Europe/London", "America/New_York")
CODE_SUFFIXES = {".php", ".js", ".mjs", ".cjs", ".html"}
OFFSET_PATTERNS = {
    "getTimezoneOffset": r"\bgetTimezoneOffset\s*\(",
    "manual hour adjustment": r"\bset(?:UTC)?Hours\s*\([^;\n]*[+-]\s*\d",
    "epoch offset": r"(?:getTime\s*\(\)|Date\.now\s*\(\))\s*[+-]",
    "offset variable": r"\b(?:\w*(?:utc|gmt|timezone|tz)\w*offset\w*|offset)\s*[:=]\s*[+-]?\d",
    "fixed hours in milliseconds": r"\b(?:[1-9]|1[0-4])\s*\*\s*(?:3600000|60\s*\*\s*60\s*\*\s*1000)",
    "fixed UTC/GMT timezone": r"(?:UTC|GMT)[+-]\d{1,2}",
}


def syntax_check(repo, paths, suffixes, executable, option):
    candidates = [p for p in paths if Path(p).suffix.lower() in suffixes and (repo / p).is_file()]
    if not candidates:
        return {"status": "not_applicable", "files": []}
    tool = shutil.which(executable)
    if not tool:
        return {"status": "skipped_tool_missing", "files": candidates}
    checks = []
    for name in candidates:
        try:
            result = subprocess.run([tool, option, str(repo / name)], cwd=repo,
                                    capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", timeout=30)
            checks.append({"file": name, "passed": result.returncode == 0,
                           "output": result.stdout + result.stderr})
        except (OSError, subprocess.TimeoutExpired) as exc:
            checks.append({"file": name, "passed": False, "output": str(exc)})
    return {"status": "passed" if all(c["passed"] for c in checks) else "failed", "files": checks}


def validate(repo, changed_files, git_status):
    php = syntax_check(repo, changed_files, {".php"}, "php", "-l")
    js = syntax_check(repo, changed_files, {".js", ".mjs", ".cjs"}, "node", "--check")
    zone_hits = {zone: [] for zone in ZONES}
    offsets = []
    for name in changed_files:
        path = repo / name
        if not path.is_file() or path.suffix.lower() not in CODE_SUFFIXES:
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(content.splitlines(), 1):
            for zone in ZONES:
                if zone in line:
                    zone_hits[zone].append({"file": name, "line": number})
            for label, pattern in OFFSET_PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    offsets.append({"file": name, "line": number, "pattern": label,
                                    "text": line.strip()[:250]})
    zones_ok = all(zone_hits.values())
    failed = not zones_ok or bool(offsets) or any(c["status"] == "failed" for c in (php, js))
    skipped = any(c["status"] == "skipped_tool_missing" for c in (php, js))
    return {
        "validation_passed": "false" if failed else ("incomplete" if skipped else "true"),
        "php_validation": php["status"], "js_validation": js["status"],
        "timezone_validation": "passed" if zones_ok else "failed",
        "hardcoded_offset_detected": bool(offsets),
        "php": php, "javascript": js, "timezone_evidence": zone_hits,
        "offset_evidence": offsets, "git_status": git_status, "changed_files": changed_files,
        "limitations": "Static heuristics only. Comments can match. Offsets can be missed. "
                        "Inline JavaScript in PHP is not syntax-checked. Manual browser/DST/scope review required.",
    }
