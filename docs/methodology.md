# Methodology

## Design and baseline

Four completed real runs on 2026-09-13 cross model (gpt-5.5, gpt-6-astra) and task prompt (minimal, detailed), once each. All use baseline a0f918e84b2f5bef1564f90ed0a73598f0bcfbf4. Earlier setup attempts and dry runs remain in the private raw archive and the public attempt inventory. No repeated-trial inference is supported.

The task is the same WordPress market-clock feature. Every prompt concatenates prompts/isolation.txt with its task prompt; hashes of the combined prompts are recorded. Detailed prompting bundles inspection, planning, implementation prescriptions and validation, so the treatment is not a single controlled instruction change.

## Clone and execution boundaries

The harness verifies a full baseline commit and disjoint source/benchmark roots. It bundles source Git history, clones into a unique runs directory, removes origin and checks out the baseline detached. Source uncommitted changes are not copied. The bundle can contain all source refs/history and is therefore excluded from publication, as are the cloned repositories. Reparse points, symlinks, submodules and object alternates are rejected where checked. Source HEAD and porcelain status are recorded before and after; these observations cannot establish a complete filesystem audit.

The recorded Codex command uses exec, --ephemeral, workspace-write, medium reasoning, approvals never, network_access=false, empty additional writable roots, --cd to the experiment clone, JSON output and a final-response file. Prompts prohibit outside workflows, production access and commits. Settings are requested constraints, not independent proof of every action. The command did not disable all inherited user configuration. Standard output/error are captured; timeout is 1800 seconds and process termination is attempted. Public metadata excludes commands/config paths.

## Timing and patch measurement

duration_seconds includes cloning/setup, agent execution and validation before final result serialization. agent_duration_seconds is separately recorded for the agent process. Neither measures pure inference or monetary cost. Timing overhead varies across runs.

A separate Git index reads the baseline, stages current nonignored files and compares against baseline with binary diff, no text conversion and no rename detection. This captures committed/staged/unstaged/deleted/new nonignored changes while preserving the agent index. Renames count as deletion/addition. Binary changes count as files but not text lines. Tests and SVG markup contribute to patch size; lower counts do not imply better code.

## Automatic validation

Changed JavaScript-family files use node --check; changed PHP files use php -l when available. Missing applicable tools yield incomplete validation. Inline JavaScript is not separately syntax-checked. Timezone checks search changed supported text files for Asia/Tokyo, Europe/London and America/New_York. Regular expressions look for common fixed-offset arithmetic. These checks can have false positives/negatives, including matches in comments/tests, and do not execute the clocks or verify actual DST transitions.

All four completed runs passed JS/timezone checks and had no detected offset arithmetic. PHP was unavailable, so aggregate validation remained incomplete. A zero exit code means an invocation completed; task_success remains needs_manual_review. No automatic metric is a visual-quality or overall-correctness score.

## Manual and unavailable evidence

manual_correctness_score, manual_visual_score and manual_scope_score remain blank, not zero. Browser/visual behavior was not fully validated. Retained or temporary model-created tests are discussed in the analysis as run-specific evidence, not a common controlled validation battery. User interventions are a recorded field, not independently reconstructed interaction counts.

## Reproduction boundary and future controls

Original harness/validator code and prompt hashes are retained. CLI/tool versions are recorded, but model backends, user settings, nondeterminism and unavailable private source prevent guaranteed exact reproduction. Use an authorized baseline to run a new series; do not treat fixture dry runs as experimental data. Future work needs repeated randomized trials, factor-isolated prompts, complete environment capture, runtime/browser/PHP checks and blinded scoring.
