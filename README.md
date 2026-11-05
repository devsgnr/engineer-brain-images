# Task 4: offline analysis of activation-perturbation outputs

This directory contains the code and input data used for the exploratory Task 4 analysis. It can be added as a subdirectory of the existing image repository; it does not change the images or their paths.

## Run

Use Python 3.10 or newer. All imports are from the Python standard library: no pip installation, GPU, PyTorch, Transformers, Hugging Face login, or model downloads are required.

From this directory:

```bash
python analyse_task4.py data/task_4_data.zip results
```

Paths containing spaces should be quoted. The first argument is the exported input ZIP; the second is the output directory. Use the bundled data for exact reproduction of the reported analysis. The script intentionally validates this study's 300-condition, 100-trials-per-condition dataset and ten 1,000-draw clean comparison samples; it is not a general-purpose evaluation framework.

## Files

```text
task_4_analysis_code/
  analyse_task4.py                 # Small command-line entry point
  task4/
    __init__.py
    cli.py                         # Arguments and orchestration
    data_io.py                     # ZIP loading and raw-data validation
    categories.py                  # Explicit wordlists and category definitions
    annotation.py                  # Token normalization and classification
    statistics.py                  # Wilson, Fisher exact and Holm correction
    analysis.py                    # Counts, comparisons and sensitivity analyses
    reporting.py                   # Markdown/JSON reports and console output
  task_4_word_kind_aid.json         # Fixed aid for lexical/uncertain labels
  tests/
    test_analysis.py
    expected_results.json          # Regression reference from the earlier analysis
  data/
    task_4_data.zip
  README.md
  .gitignore
```

Keep `task_4_word_kind_aid.json` beside the script. It freezes the finite dictionary subset used to assist provisional lexical/uncertain token-kind labels. It does not define the instrument, vehicle, aircraft, geographic-name, or door-interaction categories: those explicit wordlists and their definitions live in `task4/categories.py`. The modular release requires this bundled aid and reports a missing file instead of silently using a different machine's dictionary.

`data/task_4_data.zip` is the original exported input. It contains all 30,000 perturbed token IDs, 10,000 clean alternative-token samples, model revisions, baseline information, decoded token lookup tables, and the annotations supplied at export time. These samples are already collected; running the analysis does not resample them.

## Generated outputs

- `results/task_4_offline_report.md`: findings, definitions, all 60 final-layer comparisons, sensitivity checks, and interpretation limits.
- `results/task_4_annotation_review.md`: review tables for all ten model/prompt pairs, covering final-layer outputs and clean comparison samples.
- `results/task_4_offline_analysis.json`: results for all 300 conditions, explicit category wordlists, derived annotations, preserved supplied annotations, clean summaries, and the source-data SHA-256.
- `results/task_4_word_kind_aid.json`: copy of the word-kind aid used for the run.

The default `.gitignore` excludes generated `results/`, which can be regenerated. To publish the generated reports as well, change that rule or place selected reports in a separate tracked directory.

## What the code does

1. Validates the input ZIP and checks each reported baseline count, alternative counter, and change rate against the actual token IDs.
2. Applies the same exact-token category rules to perturbed predictions and clean alternative samples. Boundary whitespace and case are normalized for category matching; variants of the baseline word are tracked separately. Special-token and formatting labels use tokenizer flags and Unicode character categories. Unrecognized strings are not automatically called fragments.
3. Reports category matches both per all trials and per changed trials, plus formatting, lexical, fragment, special, surface-variant and uncertain token-kind counts.
4. Compares category matches among changed outputs with one clean next-token sample per model/prompt, conditioned on excluding the exact baseline token. The same 1,000 clean draws are reused for the appropriate conditions, not counted as fresh independent draws each time.
5. Calculates pointwise Wilson 95% intervals, exploratory one-sided Fisher exact tests, and Holm-adjusted p-values across all 300 conditions. Conditions with no changes have an undefined conditional category proportion and receive p=1 for multiplicity adjustment.
6. Supplies sensitivity checks for adding a manufacturer/model-name list and for assigning uncertain-kind clean outputs to the target category while retaining only confirmed noisy category matches. Each sensitivity family has its own 300-condition Holm adjustment.
7. Covers all ten model/prompt pairs. The detailed final-layer slice contains 60 conditions; the machine-readable output retains all 300. Pooled final-layer inventory percentages are explicitly descriptive mixtures across six different conditions, not an additional confirmatory test.

## Scope and limitations to report with the paper

- **Retrospective definitions:** category dictionaries were drafted with the results visible. They define reproducible wordlist endpoints, not independently validated semantic ground truth. Multiplicity correction does not remove this post-hoc choice. Review the category rules and borderline cases before adopting semantic claims.
- **Tokenization:** this is single-token category membership. A partial token is not expanded into a presumed word; completed instrument names can tokenize differently across models.
- **Different questions by prompt:** parking, aviation, and music use baseline-word categories. Location uses geographic-name matches, and action uses door-interaction verbs. Those last two are contextual categories, not semantic similarity to the baseline `the`, `feel`, or `walk`, and not a measure of fluent or appropriate continuations.
- **Conditional comparator:** clean alternative samples are not uniform vocabulary draws, clean greedy errors, or human chance rates. They are the clean model's own next-token distribution with the exact baseline token excluded.
- **Dependence and uncertainty:** scaling methods share seeds and are paired. The shared clean sample creates dependence across comparisons. Holm adjustment permits dependent comparisons, but does not address annotation validity. Wordlist nonmatches are not automatically semantically unrelated, and unresolved token-kind labels remain visible.
- **Model comparison:** model families, tokenizers, magnitude grids, and absolute calibrations differ. Do not interpret this analysis as an isolated effect of parameter count.
- **Generation:** the one-step generation-interference example is retained as a reproducible appendix demonstration. Systematic generation experiments were deferred; this script does not evaluate generation fluency or divergence.

## Verification performed

The standalone package was run against its bundled input and reproduced the earlier report, review tables, and analysis JSON byte for byte in the test environment. Primary Fisher p-values were independently checked against integer-combinatorial hypergeometric sums. Count arithmetic and output coverage were checked against the raw input.

## Statistical references

- [Fisher exact test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html)
- [Holm multiplicity adjustment](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html)

The implementation uses the standard library (`math.lgamma` and log-space summation for Fisher tail probabilities); SciPy is cited for the statistical definition, not required as a dependency.


## Separation of concerns

The entry point delegates argument parsing to `cli.py`. Input loading and validation are isolated in `data_io.py`; validation remains active under `python -O`. `annotation.py` takes the data and frozen word-kind aid explicitly. It does not read files, run models, or calculate p-values. `statistics.py` operates only on counts and has no dataset or annotation dependencies. `analysis.py` composes those functions using explicit parameters; `reporting.py` formats the resulting analysis and writes the files.

Importing any module or the entry-point file does not open the export, create output directories, or start analysis. File writes occur only when the CLI is run. The CLI supports `--help`, `--quiet`, and `--word-kind-aid PATH`.

Comments and docstrings explain methodological choices: annotation precedence, undefined proportions when no prediction changes, the shared clean sample, separate correction families, and the descriptive nature of pooled conditions. Statistical outputs and released classifications are unchanged by the refactor.

The Markdown report retains study-specific narrative for reproduction of the archived analysis. If you revise the dataset or category rules, review that prose in `reporting.py` as well as the regenerated tables; it is not a generic automatic interpretation engine.

## Tests

From this directory:

```bash
python -m unittest discover -s tests -v
```

Tests check:

- All 300 condition results, ten clean summaries, ten pooled inventories, definitions, and the complete annotation fingerprint against the earlier analysis. Numerical comparisons allow small cross-platform floating-point differences.
- Fisher upper-tail probabilities against an independent exact-integer hypergeometric calculation.
- Wilson boundary cases, Holm family adjustment, and conditions without changed predictions.
- Ambiguous prefixes, complete adjectives, special tokens, and baseline surface variants.
- Rejection of inconsistent counts, duplicate conditions, and baseline-contaminated clean samples.
- Side-effect-free imports and output-file generation.

The refactored CLI was also checked against the four original output files byte for byte in the development environment. No third-party testing packages are needed.
