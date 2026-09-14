# Publication audit

This is a proposed file set, not a staged or published repository. No top-level Git repository exists, so there are no tracked files, remotes or commits to inspect. Git status/log/diff commands report that the folder is not a repository. No initialization, staging, commit, push or GitHub creation was performed.

## Exact proposed public files (KEEP)

```text
.gitignore
LICENSE
README.md
benchmark.py
config.example.yaml
docs/evidence.md
docs/methodology.md
docs/publication-audit.md
prompts/isolation.txt
prompts/market_clock_detailed.txt
prompts/market_clock_minimal.txt
results/benchmark_analysis.public.md
results/benchmark_results.csv
results/conditions.json
tests/test_benchmark.py
validators/__init__.py
validators/market_clock.py
```

LICENSE is additionally NEEDS REVIEW: confirm ownership and replace its explicit placeholders before release. The original baseline/source availability also needs review for any claim of exact independent reproduction.

## Excluded local files

REMOVE FROM PUBLIC REPO means exclude from the proposed publication, not delete locally. This category covers config.yaml, every runs/ file (all 14 directories, including repo copies and Git internals, bundles, prompts, responses, metadata and snapshot indexes), original results/results.csv, original results/benchmark_analysis.md, results/logs/ and results/diffs/. Clean results use explicit .gitignore exceptions. IGNORE covers Python bytecode/caches and future virtual environments/editor state/temp files. The local .publication-audit/ stores the complete per-file inventory, original hashes, old README/ignore copies and verification artifacts; it is excluded in full. No original research evidence was deleted or rewritten.

## Privacy/security findings

The original config, README, raw CSV and analysis reference definitions contain machine-specific paths. Remediation: preserve original config/results privately, back up old README locally, replace public docs/config with portable text and remap analysis links to an explicit withheld-evidence inventory. Raw logs/source Git history contain user-specific information; exclude those entire trees. Bundles contain binary Git history and are not certified secret-free.

The original text scan found no private-key or common token-value signatures. Credential-related words occur in code, prompt and analysis discussion; they are not by themselves secrets. tests/test_benchmark.py uses fixture@example.invalid as a deliberate non-personal test identity. No original file exceeded 1 MB (largest approximately 163 KB); size does not establish safety. No secret values are reproduced in this report. This is a candidate-file audit, not a guarantee about ignored binary histories or future additions.

## Validation

Verification completed: all 7 existing unit tests passed; all 4 isolated CLI --all --dry-run fixtures passed with nonexistent agent/version commands, proving neither command was invoked. The fixture source remained unchanged. Curated CSV metric/status fields matched the original. SHA-256 comparisons confirmed all original evidence, harness, validators and prompts remained unchanged. Git ignore checks included all 17 public candidates and excluded the private artifact patterns. Candidate scanning found no machine paths, private-key signatures or common token-value signatures; remaining keyword hits were documentation and intentional fixture identities. Reproduction flags were matched to the argparse interface. No real model calls were made. Full outputs and per-file scan locations are retained in the ignored local audit directory.
