import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import benchmark as b
from validators.market_clock import validate


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=b.ROOT, prefix="harness-test-")
        self.base = Path(self.temp.name)
        self.root = self.base / "benchmark"
        self.root.mkdir()
        (self.root / "runs").mkdir()
        self.source = self.base / "source with spaces"
        self.source.mkdir()
        b.git(self.source, "init")
        b.git(self.source, "config", "user.email", "fixture@example.invalid")
        b.git(self.source, "config", "user.name", "Fixture")
        (self.source / "old.js").write_text("const oldValue = 1;\n")
        b.git(self.source, "add", ".")
        b.git(self.source, "commit", "-m", "baseline")
        self.commit = b.git(self.source, "rev-parse", "HEAD").decode().strip()
        self.run = self.root / "runs/test"
        self.run.mkdir()
        self.repo = self.run / "repo"
        self.root_patch = patch.object(b, "ROOT", self.root)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        # Test fixtures only; never completed experiments or the user's source.
        import os
        for current, dirs, files in os.walk(self.base):
            for name in files:
                os.chmod(Path(current) / name, 0o700)
        self.temp.cleanup()

    def clone(self):
        b.clone_baseline(self.repo, self.source, self.commit)

    def test_clone_pins_commit_and_excludes_dirty_source(self):
        (self.source / "old.js").write_text("dirty source\n")
        (self.source / "untracked.txt").write_text("local only")
        before = b.source_state(self.source)
        self.clone()
        self.assertEqual((self.repo / "old.js").read_text(), "const oldValue = 1;\n")
        self.assertFalse((self.repo / "untracked.txt").exists())
        self.assertEqual(before, b.source_state(self.source))
        self.assertEqual(b.git(self.repo, "remote"), b"")
        self.assertFalse((self.repo / ".git/objects/info/alternates").exists())

    def test_snapshot_covers_commits_staging_deletions_and_new_files(self):
        self.clone()
        b.git(self.repo, "config", "user.email", "fixture@example.invalid")
        b.git(self.repo, "config", "user.name", "Fixture")
        (self.repo / "committed.txt").write_text("committed\n")
        b.git(self.repo, "add", ".")
        b.git(self.repo, "commit", "-m", "agent commit")
        (self.repo / "old.js").unlink()
        (self.repo / "new file.js").write_text("const x = 1;\nconst y = 2;\n")
        b.git(self.repo, "add", "old.js")
        index_before = (self.repo / ".git/index").read_bytes()
        diff, names, added, deleted, _, _ = b.snapshot(self.repo, self.run, self.source, self.commit)
        self.assertEqual(set(names), {"old.js", "new file.js", "committed.txt"})
        self.assertEqual((added, deleted), (3, 1))
        self.assertIn(b"const y = 2", diff)
        self.assertEqual(index_before, (self.repo / ".git/index").read_bytes())

    def test_source_mutations_and_writable_targets_rejected(self):
        for command in ("reset", "clean", "checkout", "add", "push"):
            with self.assertRaises(ValueError):
                b.source_read(self.source, command)
        for target in (self.source, self.source / "child", self.root, self.root / "runs"):
            with self.assertRaises(ValueError):
                b.writable_repo(target, self.source)

    def test_validation_missing_zones_and_offsets(self):
        self.clone()
        result = validate(self.repo, ["old.js"], " M old.js")
        self.assertEqual(result["timezone_validation"], "failed")
        (self.repo / "old.js").write_text('const zones = ["Asia/Tokyo", "Europe/London", "America/New_York"];\nconst t = Date.now() + 9 * 3600000;\n')
        result = validate(self.repo, ["old.js"], " M old.js")
        self.assertTrue(result["hardcoded_offset_detected"])
        self.assertEqual(result["validation_passed"], "false")

    def test_missing_php_is_incomplete_not_passed(self):
        self.clone()
        (self.repo / "clock.php").write_text('<?php // Asia/Tokyo Europe/London America/New_York\n')
        with patch("validators.market_clock.shutil.which", return_value=None):
            result = validate(self.repo, ["clock.php"], "?? clock.php")
        self.assertEqual(result["php_validation"], "skipped_tool_missing")
        self.assertEqual(result["validation_passed"], "incomplete")

    def test_failure_is_recorded_and_run_preserved(self):
        (self.root / "prompts").mkdir()
        (self.root / "prompts/isolation.txt").write_text("isolated\n")
        (self.root / "prompts/minimal.txt").write_text("task\n")
        (self.root / "validators").mkdir()
        (self.root / "validators/market_clock.py").write_text("fixture")
        (self.root / "results/logs").mkdir(parents=True)
        (self.root / "results/diffs").mkdir()
        cfg = {"baseline_commit": self.commit, "models": {"older": "test"},
               "prompts": {"minimal": "prompts/minimal.txt"},
               "command": ["definitely-missing-benchmark-command.exe"],
               "version_command": ["definitely-missing-benchmark-command.exe"], "timeout_seconds": 1}
        with patch("builtins.print"):
            self.assertFalse(b.experiment(cfg, self.source, "older", "minimal", False))
        results = list((self.root / "runs").glob("*/result.json"))
        self.assertEqual(len(results), 1)
        self.assertEqual(json.loads(results[0].read_text())["task_success"], "error")
        self.assertTrue((results[0].parent / "repo").is_dir())

    def test_timeout_kills_child_and_keeps_logs(self):
        import subprocess
        import sys
        self.clone()
        with self.assertRaises(subprocess.TimeoutExpired):
            b.invoke([sys.executable, "-c", "import time; print('started', flush=True); time.sleep(20)"],
                     self.repo, "prompt", self.run, 0.5)
        self.assertIn("started", (self.run / "stdout.log").read_text())


if __name__ == "__main__":
    unittest.main()
