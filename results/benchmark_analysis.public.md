# Market-clock benchmark analysis

> Public copy of the preserved analysis. Evidence links lead to a provenance inventory; raw logs, patches and source checkouts are withheld. Historical inspection statements describe the original analysis, not independent public verification.

This experiment compares four agent implementations of one WordPress feature, with one observation per model/prompt condition. The strongest observed pattern is that detailed prompting coincided with smaller final patches and longer elapsed times in both models. The implementations differ in placement, feature breadth, runtime behavior and validation depth; the evidence does not establish a universal model winner or a visual-quality ranking.

Analysis scope: the four completed real runs specified below, excluding dry runs and other attempts. No models, validators, browser fixtures or production workflows were rerun for this analysis. The only requested output is this report.

**Experiment design and evidence**

The intended task was a responsive Tokyo/London/New York clock with country flags, live 12-hour AM/PM time, IANA/DST handling, site-consistent styling, no manual timezone arithmetic, and preservation of unrelated functionality. The factors were model (GPT-5.5 or GPT-6 Astra) and task prompt (minimal or detailed).

| Label | Model / prompt | Run ID |
|---|---|---|
| OM | GPT-5.5 / minimal | `20260913T110444_older_minimal_6450c480` |
| OD | GPT-5.5 / detailed | `20260913T111734_older_detailed_7464cd2c` |
| AM | GPT-6 Astra / minimal | `20260913T112243_astra_minimal_49f9c7f0` |
| AD | GPT-6 Astra / detailed | `20260913T114318_astra_detailed_8259781f` |

All four metadata records identify baseline, start and final HEAD as `a0f918e84b2f5bef1564f90ed0a73598f0bcfbf4`. Read-only Git inspection confirms that current HEAD is still this commit in every run. The source-before/source-after metadata records all have this HEAD and empty status. This supports preservation of the source's recorded Git state during execution; it is not a complete historical filesystem audit.

The recorded environment is identical across conditions: Codex CLI 0.154.0, Node 24.11.0, Python 3.14.0, Git 2.47.1.windows.2, medium reasoning effort, workspace-write sandbox, approvals set to never, and unavailable PHP. All recorded harness and validator hashes match each other and the current harness/validator files. Commands differ only in model and run-specific paths. They use the npm `codex.cmd` launcher and do **not** include `--ignore-user-config`; inherited CLI configuration was not fully captured.

The exact submitted prompts match across models within each style, including their recorded hashes. Both styles include the same substantial isolation instructions. Thus “minimal” means a minimal task description under a common safety prefix, not an unscaffolded one-line session. The detailed prompt bundles several changes: explicit inspection targets, a pre-implementation plan, a prescribed API and timezone IDs, an unrelated-file restriction, and a validation/retry checklist. It also explicitly directs attention to the homepage. This is not a test of prompt length alone. [OM prompt][om-prompt] [OD prompt][od-prompt] [AM metadata][am-meta] [AD metadata][ad-meta]

For each run, this analysis inspected the prompt, final response, metadata, result, changed-file list, saved patch, repository Git status/diff, changed source contents, and validation/execution logs. Saved patches match the existing snapshot-index diffs byte-for-byte. Every listed changed source file matches its saved index blob after CRLF/LF normalization. Each result matches its single corresponding CSV row. New untracked files were included through the existing snapshot index without staging anything; ordinary working-tree `git diff` alone omits them.

**Measured results**

Duration is the recorded harness wall time, including clone/setup, agent execution and validation, rather than a model-only latency measurement. Lines are net patch additions/deletions, including tests, assets, comments and whitespace.

| Model | Prompt | Duration (s) | Files changed | Lines added | Lines deleted | JS validation | Timezone validation | Hardcoded offsets detected | Changed file names |
|---|---|---:|---:|---:|---:|---|---|---|---|
| GPT-5.5 | Minimal | 186.387 | 3 | 250 | 0 | Passed | Passed | No (heuristic) | `assets/css/home.css`; `assets/js/main.js`; `front-page.php` |
| GPT-5.5 | Detailed | 237.650 | 3 | 101 | 0 | Passed | Passed | No (heuristic) | `assets/css/home.css`; `assets/js/main.js`; `front-page.php` |
| GPT-6 Astra | Minimal | 226.689 | 9 | 252 | 0 | Passed | Passed | No (heuristic) | `assets/css/components.css`; `assets/images/flags/gb.svg`; `assets/images/flags/jp.svg`; `assets/images/flags/us.svg`; `assets/js/market-clock.js`; `header.php`; `inc/enqueue.php`; `scripts/test-market-clock.cjs`; `template-parts/global/market-clock.php` |
| GPT-6 Astra | Detailed | 313.796 | 4 | 124 | 0 | Passed | Passed | No (heuristic) | `assets/css/home.css`; `assets/js/market-clock.js`; `front-page.php`; `inc/enqueue.php` |

Sources: the four [OM][om-result], [OD][od-result], [AM][am-result] and [AD][ad-result] result records, checked against changed-file lists and saved Git diffs.

All four have `exit_code=0`, `task_success=needs_manual_review`, `validation_passed=incomplete`, and `php_validation=skipped_tool_missing`. All manual scores and user-intervention fields are blank. These are completed agent invocations, not four independently established task successes. Blank intervention fields must not be reported as measured zeros.

| Patch composition | OM | OD | AM | AD |
|---|---:|---:|---:|---:|
| CSS additions | 132 | 54 | 65 | 47 |
| Runtime JavaScript additions | 69 | 30 | 53 | 36 |
| PHP/template/enqueue additions | 49 | 17 | 40 | 41 |
| Separate SVG asset additions | 0 | 0 | 13 | 0 |
| Retained test additions | 0 | 0 | 81 | 0 |
| Total additions | 250 | 101 | 252 | 124 |
| Newly created files | 0 | 0 | 6 | 1 |
| Recorded agent duration, seconds | 185.313 | 236.533 | 225.475 | 312.603 |

AD embeds its SVGs within PHP, so its flag code is counted in the PHP row. Both inline and external SVGs include compressed one-line markup; line count is not a language-neutral measure of complexity. AM contains 171 non-test added lines, substantially below OM's 250 despite almost identical total patch size.

**GPT-5.5 with minimal prompting (OM)**

Measured code facts: adds a standalone homepage section immediately after the hero and before featured posts, beginning at `front-page.php:153`. It uses existing container helpers, translation/escaping functions, homepage CSS and the already-enqueued `main.js`. No new files, dependencies or enqueue changes appear. Its three large cards include emoji flags, country names, seconds, local date/timezone labels, a heading, explanatory copy and decorative accents. JavaScript caches time and timezone-label formatters, filters invalid entries, updates semantic time elements once per second, and starts no interval when usable clocks are absent. [OM patch][om-patch] [OM JavaScript][om-js]

Interpretation: file-level scope is disciplined, but the feature presentation is more elaborate than the essential request. The 132 CSS lines and extra date/zone formatting explain much of its size. This is presentational and feature expansion, not a new general-purpose framework. Maintaining three duplicated card blocks and two formatters per city is more work than a bare three-clock display, although caching and invalid-zone handling are useful.

Potential concerns: without JavaScript or Intl, the empty time fields and “Loading” labels remain; no noscript explanation is supplied. Emoji flags depend on rendering support. The large nonwrapping time text and clipped cards deserve manual narrow-width inspection. These are review targets, not observed browser failures.

Autonomy evidence is specific: the log chooses placement and Intl without being told the API, corrects flag placeholders, and removes a noisy live-announcement attribute before finishing (stdout lines 27, 34, 37–48). It performs a mocked-DOM execution of the actual script and separate winter/summer Intl spot checks (lines 56 and 60). The latter test Intl independently, not the full implementation at those fixed instants. [OM execution log][om-log]

**GPT-5.5 with detailed prompting (OD)**

Measured code facts: inserts a small three-item grid inside the hero's text column, after its action buttons and before existing metadata (`front-page.php:90`). It changes the same three existing files as OM. The display is minutes-only, uses numeric HTML entities for emoji flags, and stacks at the existing 640px breakpoint. It reuses theme variables and adds no abstractions beyond a small update function and data attributes. [OD patch][od-patch] [OD JavaScript][od-js]

Interpretation: this is the smallest final patch and the tightest presentation scope. It removes the need for a separate section, country descriptions and date/timezone-label formatting. The existing-file approach is easy to locate but couples clock behavior to the shared navigation/progress script.

Simplicity has concrete tradeoffs: every tick re-queries each time child and constructs three Intl formatters, although only minutes are displayed. The interval is scheduled unconditionally on every page that loads `main.js`, including pages without clock elements. The function returns immediately on those pages, but the timer still exists. Invalid timezone construction is not caught. These are small efficiency/resilience issues, not a measured performance regression or a failure for the fixed valid zones.

The log follows the requested plan-before-editing workflow (line 34), changes flag encoding, and tightens the locale to `en-US`. It also records two failed validation one-liners caused by PowerShell quoting (lines 91 and 100), then falls back to simpler checks. Repeated source/syntax/diff checks are visible; some followed real corrections, so not all repetition is unnecessary. The winter/summer checks exercise standalone Intl formatting rather than a retained implementation-level test suite. [OD execution log][od-log]

**GPT-6 Astra with minimal prompting (AM)**

Measured code facts: adds a global template part immediately after the header and before the main-content element (`header.php:36`). Pages using this shared header receive the clock. It creates a data-driven PHP market list, three local SVG assets, an independent 53-line runtime script, and an 81-line Node test file. The existing enqueue helper supplies cache-busting and deferred footer loading; shared component CSS supplies styling. This follows existing template-parts/assets/enqueue architecture rather than introducing an external framework. [AM patch][am-patch] [AM template][am-template]

The runtime caches one formatter per city, displays seconds, catches unsupported zones, avoids timers on empty/unsupported pages, stops its timer while hidden, refreshes on visibility/page restoration, and prevents duplicate intervals. The markup has translated fallback text and a noscript explanation. The retained tests execute the actual runtime script with a mocked DOM and clock, asserting fixed expected outputs for ten instants spanning winter, summer, US/UK spring/fall changes, and noon/midnight behavior. They additionally check a running DST transition, datetime attributes, timer lifecycle, restoration and unsupported zones. Two logged executions pass; the three SVGs also parse as XML (stdout lines 19 and 23). [AM runtime][am-js] [AM tests][am-test] [AM execution log][am-log]

Interpretation: the largest file footprint has clear causes—modularity, flags and reusable validation. The abstraction count is proportionate to a global component, and the test is directly relevant to timezone risk. Calling all six new files unnecessary would ignore their purpose. Maintainability benefits include a single market data list, isolated behavior and retained regression evidence; costs include extra assets/integration points and a broader site-wide change.

Scope is ambiguous: the minimal task says “website,” not “homepage only.” Global placement is a defensible interpretation, but it changes more pages than the other runs and would require broader regression review. It is scope expansion relative to those implementations, not demonstrated violation of the prompt. No unrelated refactoring appears in the diff. The final response does not enumerate all changed files, making its handoff less traceable than the saved artifact list.

**GPT-6 Astra with detailed prompting (AD)**

Measured code facts: adds a compact homepage section below the hero (`front-page.php:153`), three inline SVG flags, homepage styles and a dedicated 36-line script. Enqueueing is inside the existing `is_front_page()` branch. It caches one formatter per element, shows minutes, updates every second, refreshes when the page becomes visible, and includes a noscript explanation. No reusable PHP component or test file remains in the final patch. [AD patch][ad-patch] [AD runtime][ad-js]

Interpretation: this is a balanced small integration: behavior is separated from shared navigation code and loaded only where needed, while markup remains local to its only use. Inline SVGs avoid separate flag-file management but lengthen template lines. Unlike AM, it has no explicit Intl/invalid-zone fallback, timer suspension, or pageshow handler. These omitted defenses are a simpler scope choice for fixed valid zones in modern browsers; they do not establish incorrect normal operation.

The log documents a pre-edit plan (line 14), creation of a temporary validation fixture, two outputs reporting 12 passing time cases, and two failed Edge attempts—initialization failure followed by timeout. The temporary fixture was deleted before final capture; its full test implementation is not preserved in the execution events, so its coverage is less independently inspectable than AM's retained suite. The log also records a quoting failure during flag adjustment, denied process inspection, and a policy-blocked combined edit/cleanup attempt, followed by successful separate operations. These are actual workflow costs, not extra retained production features. [AD execution log][ad-log] [AD stderr][ad-stderr]

The final width check uses a simplified arithmetic model at eight widths from 320 to 1440px, assuming fixed spacing and at least 150px content width. It does not measure glyphs, loaded fonts, rendered bounding boxes or actual overflow. The final response correctly reports that rendering remains unverified.

**Paired comparisons**

| Comparison | Observed time difference | Observed patch difference | Interpretation supported by code |
|---|---|---|---|
| GPT-5.5: detailed vs minimal | +51.263 s (+27.50%) | 250 → 101 added lines (−59.6%); 3 → 3 files | Detailed condition produced a smaller hero widget instead of a decorated section with extra date/zone information. |
| Astra: detailed vs minimal | +87.107 s (+38.43%) | 252 → 124 added lines (−50.8%); 9 → 4 files | Detailed condition narrowed placement and final artifacts; it also removed retained tests and some resilience behavior. |
| Minimal: Astra vs GPT-5.5 | +40.302 s (+21.62%) | 250 → 252 added lines; 3 → 9 files | Similar total line counts conceal different work: large presentation versus a global component with tests/assets. |
| Detailed: Astra vs GPT-5.5 | +76.146 s (+32.04%) | 101 → 124 added lines; 3 → 4 files | Astra isolated/cached the behavior and used SVG flags; GPT-5.5 minimized files/lines through existing main.js and emoji entities. |

Within GPT-5.5, the detailed condition is more restrained in output, but its runtime is not uniformly better engineered. Within Astra, detailed prompting coincides with narrower page scope and fewer persistent artifacts, not with a faster process or stronger retained validation. Excluding AM's 81 test lines, Astra's non-test additions decrease from 171 to 124 (27.5%), rather than 50.8%.

Under minimal prompting, both models independently choose Intl and IANA identifiers. GPT-5.5 finishes sooner; Astra leaves stronger inspectable regression tests and lifecycle handling. Under detailed prompting, GPT-5.5 again finishes sooner and writes fewer lines; Astra's conditional loading and cached formatters are specific architecture advantages. Neither pair supports a visual winner.

These are descriptive paired contrasts. One run in each cell cannot identify whether the differences were caused by prompting, stochastic choices, latency, or interactions with the environment.

**Behavioral evidence and interpretation**

| Topic | Concrete evidence | Defensible interpretation |
|---|---|---|
| Autonomy | Both minimal logs inspect context, select placement/API, implement, and validate without a logged clarification exchange. OM self-corrects live announcements; AM creates focused runtime tests. | Both demonstrate independent task execution within the supplied instructions. Intervention counts remain unknown because fields are blank. |
| Unnecessary work | OD rebuilds three formatters per tick and schedules an empty-page timer; OD quoting retries and AD flag-edit quoting failure generate no feature benefit. | These are identifiable avoidable costs. Their runtime or wall-time impact was not isolated quantitatively. |
| Context sensitivity | All use existing theme variables and WordPress conventions. OM/OD reuse main.js; AM follows global template/component conventions; AD uses homepage-only enqueueing. | All adapt to repository architecture. Reuse of different valid extension points is not evidence that one ignored context. |
| Over-scaffolding | Both detailed runs perform explicit plans and more recorded command invocations; AD tries a browser fixture and OD repeats checklist checks. Yet both final patches are smaller. | Process overhead is visible; harmful over-scaffolding is not established. A narrower output can coexist with more validation effort. |
| Prompt-induced constraint | Detailed prompts name front-page inspection, prescribe Intl and prohibit unrelated edits; both detailed outputs are compact homepage integrations. | Consistent with constraint guiding scope, but the bundled wording changes and n=1 prevent attribution to any single instruction. |
| Scope control | OD adds no files; AD loads its new script only on the homepage. AM adds the feature through the global header. All final diffs are feature-related additions. | OD/AD have narrower feature/page footprints. Global placement is not automatically unrelated work under the minimal wording. |
| Implementation simplicity | OD totals 101 lines; AD combines a 36-line cached-formatter script with conditional enqueueing; AM's data loop avoids three repeated PHP blocks. | Simplicity has several dimensions: line count, runtime work, duplication and integration surface. No single count captures all of them. |

Execution logs contain 23, 48, 6 and 15 completed command-execution events for OM, OD, AM and AD respectively. These are CLI event counts, not normalized shell-operation counts: Astra often batches several commands in one invocation. They corroborate different workflow shapes but are not a standalone efficiency score. No precise duration share can be assigned to browser failures, reading or retries from these counts.

**Validation facts versus remaining uncertainty**

The common validator checks JavaScript syntax, finds zone strings in changed PHP/JS/HTML-family files, and applies regex offset heuristics. It can count test-file strings, and does not prove correct DOM wiring, live updates or DST behavior. Here, source inspection additionally confirms the three zones are wired into Intl formatters in all implementations; no manual timezone arithmetic appears in the inspected clock logic. A 1000ms timer or numeric SVG geometry is not timezone arithmetic.

The agents' own tests provide unequal additional evidence: OM has a logged mocked-DOM smoke check plus independent seasonal Intl examples; OD has seasonal Intl examples and static checks; AM has a retained implementation-level test suite with passing logs; AD has logged fixture results but no retained fixture. “10 cases” versus “12 cases” is not a quality ranking because their definitions and inspectability differ.

No run supplies successful WordPress rendering or browser layout verification. CSS breakpoints and shared design tokens support intended responsiveness and stylistic integration, not an observed visual outcome. Numeric flag entities still represent emoji; they solve source-encoding concerns, not platform-independent flag rendering. SVGs provide explicit artwork but their appearance/fidelity also needs review. Page-level overflow clipping can conceal clipped content; it cannot substitute for a browser overflow check.

Unchanged old lines and feature-specific additions support source-level scope preservation. They do not prove that navigation, header layout, sliders or other behavior remains regression-free. Visual quality, accessibility behavior and overall task correctness require manual review for all four runs.

**Five strongest supported findings**

1. **Detailed conditions produced smaller final patches in both models.** GPT-5.5 fell from 250 to 101 added lines; Astra from 252 to 124. The code supports narrower presentation/features, with the Astra reduction partly explained by the absence of 81 retained test lines.
2. **Detailed conditions took longer in both models, and GPT-5.5 was faster under both styles in this sample.** The measured differences are +27.50% and +38.43% within models; these are elapsed-run observations, not general model-speed estimates.
3. **Minimal task prompting was sufficient for both agents to select the requested timezone architecture.** Both independently used Intl, the three IANA identifiers, 12-hour formatting and live updates. The detailed API prescription was not necessary to elicit that choice in these two observations.
4. **File/line counts do not rank maintainability or scope quality by themselves.** Astra minimal's nine files include relevant assets and the only retained runtime test suite; GPT-5.5 detailed's smallest patch includes avoidable repeated formatter construction and a site-wide empty-page timer.
5. **Common static checks do not separate the four implementations' correctness or visual quality.** All pass JS/zone scans with no detected offsets, yet all remain validation-incomplete and manually unscored; additional implementation-level evidence is strongest and most inspectable in Astra minimal's retained tests.

**Three experiment limitations**

1. **No replication or randomized order.** There is one run per condition, on one theme and feature, in a fixed time order. There are no variance estimates, confidence intervals, reliable interaction estimates or defensible general claims about model superiority, reliability or prompt effects.
2. **The prompts bundle constraints and allow different scope interpretations.** Homepage emphasis, prescribed APIs, planning and validation instructions change together. Global versus homepage placement, seconds versus minutes, extra labels, flag representation and test retention differ, so these are not identical deliverables with only phrasing changed.
3. **Incomplete and uneven evaluation/environment control.** PHP and rendered layout checks are missing; browser validation failed; manual correctness/visual/intervention fields are blank; agent tests differ in depth and persistence. The recorded command allows inherited CLI configuration, and elapsed time includes tool/setup/environment costs. Thus quality, cost, runtime performance and isolated model latency cannot be ranked from these artifacts.

**Recommended technical-blog charts and tables**

| Artifact | What to show | Required caveat |
|---|---|---|
| Two-panel paired dot chart | Minimal → detailed elapsed seconds, separately for each model; a second panel for added lines. Label all four raw observations and deltas. | n=1 per condition; connecting lines illustrate contrasts, not trends or causal effects. |
| Stacked additions chart | CSS, runtime JS, PHP/template/enqueue, SVG assets and retained tests using the composition table above. | Inline SVG belongs to PHP; compressed markup and tests distort raw line comparisons. |
| Architecture table | Placement/page scope, script loading, caching, timer lifecycle, flag mechanism, retained tests and fallback behavior. | Prefer this to a subjective “complexity score.” |
| Validation evidence matrix | Harness syntax/zone scans, PHP unavailable, smoke tests versus implementation tests, browser failure/unverified, manual scores absent. | Separate recorded checks from agent claims and untested acceptance criteria. |
| Evidence excerpts | Small code excerpts contrasting formatter creation inside OD's tick with AD's cached setup, plus AM's explicit DST assertions. | Explain the tradeoff; avoid equating fewer lines with better code. |

A useful blog framing is “smaller patches, longer runs, different tradeoffs.” Avoid a composite winner score, success-rate chart, visual ranking, cost claim or statistical significance language. If screenshots are later added, render each preserved implementation independently under the same viewport/content/font conditions and clearly label that as a separate evaluation phase.

**Artifact references**

The references below point to the preserved evidence. Log line references in the text are one-based JSONL lines. No completed run, prompt, CSV, saved log or patch was changed by this analysis.

| Run | Inputs and recorded outcomes | Code and validation evidence |
|---|---|---|
| OM | [Prompt][om-prompt]; [final response][om-final]; [metadata][om-meta]; [result][om-result] | [Changed files][om-files]; [patch][om-patch]; [validator report][om-val]; [execution log][om-log] |
| OD | [Prompt][od-prompt]; [final response][od-final]; [metadata][od-meta]; [result][od-result] | [Changed files][od-files]; [patch][od-patch]; [validator report][od-val]; [execution log][od-log] |
| AM | [Prompt][am-prompt]; [final response][am-final]; [metadata][am-meta]; [result][am-result] | [Changed files][am-files]; [patch][am-patch]; [validator report][am-val]; [execution log][am-log] |
| AD | [Prompt][ad-prompt]; [final response][ad-final]; [metadata][ad-meta]; [result][ad-result] | [Changed files][ad-files]; [patch][ad-patch]; [validator report][ad-val]; [execution log][ad-log] |

[om-prompt]: ../docs/evidence.md#om-prompt
[om-final]: ../docs/evidence.md#om-final
[om-meta]: ../docs/evidence.md#om-meta
[om-result]: ../docs/evidence.md#om-result
[om-files]: ../docs/evidence.md#om-files
[om-val]: ../docs/evidence.md#om-val
[om-log]: ../docs/evidence.md#om-log
[om-stderr]: ../docs/evidence.md#om-stderr
[om-patch]: ../docs/evidence.md#om-patch

[od-prompt]: ../docs/evidence.md#od-prompt
[od-final]: ../docs/evidence.md#od-final
[od-meta]: ../docs/evidence.md#od-meta
[od-result]: ../docs/evidence.md#od-result
[od-files]: ../docs/evidence.md#od-files
[od-val]: ../docs/evidence.md#od-val
[od-log]: ../docs/evidence.md#od-log
[od-stderr]: ../docs/evidence.md#od-stderr
[od-patch]: ../docs/evidence.md#od-patch

[am-prompt]: ../docs/evidence.md#am-prompt
[am-final]: ../docs/evidence.md#am-final
[am-meta]: ../docs/evidence.md#am-meta
[am-result]: ../docs/evidence.md#am-result
[am-files]: ../docs/evidence.md#am-files
[am-val]: ../docs/evidence.md#am-val
[am-log]: ../docs/evidence.md#am-log
[am-stderr]: ../docs/evidence.md#am-stderr
[am-patch]: ../docs/evidence.md#am-patch

[ad-prompt]: ../docs/evidence.md#ad-prompt
[ad-final]: ../docs/evidence.md#ad-final
[ad-meta]: ../docs/evidence.md#ad-meta
[ad-result]: ../docs/evidence.md#ad-result
[ad-files]: ../docs/evidence.md#ad-files
[ad-val]: ../docs/evidence.md#ad-val
[ad-log]: ../docs/evidence.md#ad-log
[ad-stderr]: ../docs/evidence.md#ad-stderr
[ad-patch]: ../docs/evidence.md#ad-patch

[om-js]: ../docs/evidence.md#om-js
[od-js]: ../docs/evidence.md#od-js
[am-js]: ../docs/evidence.md#am-js
[ad-js]: ../docs/evidence.md#ad-js
[am-template]: ../docs/evidence.md#am-template
[am-test]: ../docs/evidence.md#am-test

