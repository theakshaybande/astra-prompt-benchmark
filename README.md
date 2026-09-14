# Prompting Less, Getting More?

A small, auditable coding-agent experiment comparing GPT-5.5 and GPT-6 Astra on one WordPress market-clock task. The 2×2 design crosses two models with minimal and detailed task prompts, with **one completed observation per condition**.

Detailed prompting coincided with smaller patches and longer wall time in both models. That is a descriptive observation, not statistical significance or an overall model ranking.

## Research question and task

How does prompt detail relate to implementation scope, elapsed time and validation evidence when coding agents begin from the same theme commit?

The task was to implement live Tokyo, London and New York clocks with country flags, 12-hour AM/PM display, daylight-saving handling and styling appropriate to the existing desktop/mobile site. The minimal prompt stated outcomes; the detailed prompt additionally prescribed inspection, planning, integration guidance, Intl/IANA timezone handling and validation steps. Both inherited [common isolation instructions](prompts/isolation.txt). Minimal therefore does not mean no context. The detailed treatment changes several instructions together; this experiment cannot identify which instruction caused a difference.

## Results

| Model | Prompt | Wall time (s) | Files changed | Lines added | Lines deleted |
|---|---|---:|---:|---:|---:|
| GPT-5.5 | Minimal | 186.387 | 3 | 250 | 0 |
| GPT-5.5 | Detailed | 237.650 | 3 | 101 | 0 |
| GPT-6 Astra | Minimal | 226.689 | 9 | 252 | 0 |
| GPT-6 Astra | Detailed | 313.796 | 4 | 124 | 0 |

JavaScript syntax and timezone checks passed for all four; no hardcoded timezone-offset arithmetic was detected by the heuristic. PHP syntax validation was **skipped because PHP CLI was unavailable**, leaving aggregate validation incomplete. All completed invocations still require manual review. Browser/visual correctness was not fully validated, and the manual score fields are blank.

The [curated CSV](results/benchmark_results.csv) contains only these four real conditions, retains recorded metric/status fields and replaces free-form notes with a safe summary. Duration formatting uses three decimal places. [Sanitized metadata](results/conditions.json) retains identifiers, recorded tool versions and hashes. [Full public analysis](results/benchmark_analysis.public.md) discusses implementation differences; [evidence inventory](docs/evidence.md) preserves attempt history and explains withheld artifacts.

## Key observations and interpretation

Detailed prompts coincided with 59.6% fewer added lines for GPT-5.5 and 50.8% fewer for Astra, while elapsed time increased by 27.5% and 38.4%, respectively. Patch size is not quality: Astra minimal retained 81 lines of tests, so its non-test comparison is 171 versus 124 additions (27.5% smaller with detailed prompting).

Both minimal implementations independently chose Intl and the required IANA zones. GPT-5.5 detailed produced the smallest patch. Astra minimal retained the strongest test artifact of these four runs. Placement, feature breadth and lifecycle behavior differed, so none of these facts establishes an overall winner or a visual-quality ranking.

## Design, isolation and metrics

Each run uses a fresh independent Git clone from a bundle pinned to one full baseline SHA. Dirty/untracked source files are excluded; the clone's origin is removed, linked paths are rejected, and source HEAD/status are compared before and after. Common instructions forbid production, deployment and shared-site access. These safeguards support isolation but are not proof of complete filesystem noninterference.

The harness records elapsed wall time including cloning/setup and validation, changed files, added/deleted lines, static checks and manual-review fields. A separate index captures committed, staged and unstaged nonignored changes relative to baseline. It does not equate successful process exit or static checks with task correctness. See [methodology](docs/methodology.md).

## Requirements and reproduction

Python 3.10+ (standard library only), Git, Node.js for JavaScript checks and PHP CLI for PHP checks. Real runs also require an authenticated Codex CLI and access to the configured model identifiers. Availability and future CLI compatibility are not guaranteed. The recorded environment used Python 3.14.0, Git 2.47.1.windows.2, Node 24.11.0 and Codex CLI 0.154.0 on Windows; PHP was missing.

The original theme baseline is **not distributed here**. Exact historical reproduction requires authorized access to that source at the recorded commit. Running against your own licensed theme exercises the methodology but produces a new experiment, not a reproduction of these numerical results.

From this repository root in PowerShell, first run the tests:

```powershell
python -m unittest discover -s tests -v
python benchmark.py --help
```

For a new checkout, copy the example once (preserve any existing local config):

```powershell
Copy-Item config.example.yaml config.yaml
```

Edit source_repo to your independent source repository and baseline_commit to its full 40-character commit SHA. The example retains the historical SHA only as provenance; it must exist in your chosen source. Source and benchmark roots must be disjoint, without junctions/symlinks. Relative source paths resolve from the process working directory, so run commands from this root. The config is JSON, a subset of YAML 1.2; the parser uses json.load and does not accept arbitrary YAML syntax.

The example uses codex.cmd from Windows PATH. On other systems replace both executable entries with codex (or an installed native executable path). Check local CLI help for compatibility before a real run; keep the argument vector, no shell wrapper. Real model authentication is external to this repository.

```powershell
python benchmark.py --config config.yaml --all --dry-run
python benchmark.py --config config.yaml --model older --prompt minimal --dry-run
```

Dry runs clone the configured source and exercise capture/validation with a two-line JavaScript fixture. They invoke neither the configured agent command nor its version command. They are not implementations or evidence of model quality. Runs append to the ignored local results/results.csv and create ignored runs, logs and diffs; they never update the curated public CSV.

Only when deliberately starting a new experiment, the following commands make real model calls and may incur charges:

```powershell
python benchmark.py --config config.yaml --model older --prompt minimal
python benchmark.py --config config.yaml --model older --prompt detailed
python benchmark.py --config config.yaml --model astra --prompt minimal
python benchmark.py --config config.yaml --model astra --prompt detailed
# Alternatively, run the complete configured matrix sequentially:
python benchmark.py --config config.yaml --all
```

Do not combine --all with --model/--prompt. A stale results/.benchmark.lock should be removed only after verifying no runner is active; retain evidence first. Cleanup is optional and never part of reproduction: --clean-run RUN_ID previews a specific run deletion; adding --confirm deletes that local run, retaining CSV/diffs/logs. Do not use cleanup on historical evidence.

## Limitations and future experiments

There are no repeats, randomized order, confidence intervals or significance tests. One task and one baseline cannot establish general model capability. The bundled prompt treatment confounds instruction effects. Inherited CLI configuration was not fully captured (the recorded command did not use --ignore-user-config). Static checks do not prove DST runtime behavior, browser rendering, accessibility or WordPress integration. Wall time is not model inference time or token cost. Public provenance omits raw source, logs and patches, limiting independent verification.

A stronger follow-up would preregister scoring, randomize repeated trials across several tasks, isolate prompt factors, capture complete execution settings and costs, and run PHP, WordPress/browser, accessibility and DST transition checks with blinded manual review.

## Repository structure and licensing

See [publication audit](docs/publication-audit.md) for the exact public file list and exclusions. Harness, prompts and validators are preserved unchanged. Local config, raw CSV/analysis, failed attempts, logs, patches, Git bundles and copied theme checkouts remain private and untouched. Do not publish the whole working folder or force-add ignored artifacts.

MIT is recommended for the original harness and documentation. [LICENSE](LICENSE) is a proposed template pending confirmation of the copyright holder; it does not grant rights to the separately owned source theme or third-party artifacts. Resolve its placeholder before publication.
