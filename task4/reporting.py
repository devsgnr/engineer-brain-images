"""Format and write reports without performing statistical calculations.

Tables are derived from the analysis package. Study-specific narrative is
retained to reproduce the archived report; review that prose if the dataset or
category definitions change. Reporting must not silently redefine an endpoint.
"""

import collections
import json
from pathlib import Path

def pct(x): return 'N/A' if x is None else f'{100*x:.1f}%'


def _annotation_table(model, prompt, data, annotations, pooled):
    """Show exact decoded tokens and both observed and clean counts."""
    final=next(r for r in pooled if r['model_name']==model and r['prompt_name']==prompt)
    obs={t['token_id']:t['count'] for t in final['tokens']}
    null=collections.Counter(data['clean_alternative_samples'][model][prompt]['predictions'])
    ids=set(obs)|set(null)
    lines=['| ID | Token | Noisy count | Clean count | Kind | Category match |','|---:|---|---:|---:|---|---|']
    for token_id in sorted(ids,key=lambda t: (-(obs.get(t,0)+null[t]),t)):
        a=annotations[model][prompt][str(token_id)]
        token=json.dumps(a['text'],ensure_ascii=False).replace('|','\\|')
        lines.append(f'| {token_id} | `{token}` | {obs.get(token_id,0)} | {null[token_id]} | {a["kind"]} | {a["category_match"]} |')
    return '\n'.join(lines)


def build_annotation_review(data: dict, package: dict) -> str:
    """Build all ten inventories; a category nonmatch is not a semantic verdict."""
    annotations = package['annotations']
    pooled = package['final_layer_pooled_descriptive_only']
    definitions = package['definitions']
    review=['# Task 4: token category review\n','These are retrospective, assistant-assisted annotations. Review the explicit category definitions before using them as manuscript semantic labels. Unrecognized strings remain uncertain; they are not automatically called fragments. Exact category matches do not exhaust semantic relatedness.\n']
    for model in data['models']:
        for prompt in data['prompts']:
            review.extend([f'\n## {model}: {prompt}\n',definitions[prompt]+'\n',_annotation_table(model, prompt, data, annotations, pooled)])
    return '\n'.join(review)


def build_report(package: dict) -> str:
    """Build the archived study report with explicit denominators and caveats."""
    definitions = package['definitions']
    pooled = package['final_layer_pooled_descriptive_only']
    final_results = [row for row in package['conditions'] if row['is_final_layer']]
    summary=['# Task 4: offline analysis\n',
        'Generation interference is retained as a single reproducible appendix demonstration. No additional GPU generation experiments were performed.\n',
        '## Main findings\n',
        'The comparison supports conditional structure in selected cases, not a general claim that activation noise preferentially produces semantically related replacements. Clean alternative distributions are themselves structured.\n',
        '- **SmolLM2 aviation, final layer, std, delta 0.30:** 30 of 41 changed predictions match the aircraft-category lexicon (73.2%), or 30 of all 100 trials. The clean alternative sample contains 328/1000 matches (32.8%).\n- **Gemma music, final layer, std, delta 0.05:** all 47 changed predictions match the instrument lexicon, or 47/100 trials; clean alternatives match at 777/1000 (77.7%). The categorical result is less secure under a deliberately conservative reassignment of unresolved clean tokens, as the sensitivity section shows.\n- **Parking:** neither model has a final-layer category-enrichment result surviving the declared 300-condition correction. Vehicle alternatives occur, but their mere occurrence does not establish enrichment over clean alternatives.\n- **Location and action:** all results are included, but their target metrics are contextual category matches, not semantic similarity to the original baseline word. Gemma shows exploratory enrichment of explicitly listed door-interaction verbs in some conditions; this should not be presented as validated semantic substitution or fluent generation.\n',
        'The definitions were formed retrospectively with the supplied results visible. Treat the p-values as exploratory wordlist comparisons pending review, not confirmatory proof of a semantic mechanism. No new GPU runs are needed for that review.\n',
        '## Data validation\n',
        '- 300 conditions, each with 100 predictions; all baseline counts, alternative counters and change rates match the raw token IDs.\n- 10 clean alternative samples, each with 1,000 token IDs; baseline token IDs are absent as intended.\n- All ten model/prompt pairs covered. Final-layer primary slice: 60 conditions, 6,000 noisy predictions.\n',
        '## What was measured\n',
        'The analysis uses explicit retrospective exact-token category lexicons. This is a reproducible lexical-category endpoint, not a complete human semantic annotation. The parking, aviation and music targets approximate the baseline word category. Location and action have separate contextual category definitions: they are not semantic substitutions for the baseline words the, feel or walk.\n',
        'Token kinds are provisionally assisted by supplied annotations and an English dictionary. Dictionary-unknown strings remain uncertain. Complete adjectives such as electric are lexical, not fragments. Presumed completions of ob, harmon, or partial place names are not inferred. The full annotation table is included for review.\n',
        'The bundled word-kind aid is restricted to strings in this export. It affects provisional lexical/uncertain labels, not the exact category lexicons. Supplied annotations are preserved alongside the derived labels in the JSON.\n',
        '## Category definitions\n']
    for p,definition in definitions.items(): summary.append(f'- **{p}:** {definition}')
    summary.extend(['\n## Final-layer pooled inventory summary\n',
        'Each row pools six different intervention conditions (three strengths and two methods), 600 trials total. Percentages are descriptive mixtures; do not use these rows as an independent confirmatory experiment or pool the shared clean null six times.\n',
        '| Model | Prompt | Changed / 600 | Category / all | Category / changed | Clean category / 1000 | Uncertain kinds among changes |',
        '|---|---|---:|---:|---:|---:|---:|'])
    for r in pooled:
        summary.append(f'| {r["model_name"]} | {r["prompt_name"]} | {r["changed"]} | {pct(r["category_rate_all"])} | {pct(r["category_rate_changed"])} | {pct(r["null_category_rate"])} | {r["kind_counts"].get("uncertain",0)} |')
    summary.extend(['\n## Per-condition final-layer comparisons\n',
        'Each estimate below concerns one 100-trial condition. Clean category rates are estimated from one shared 1,000-draw clean distribution per model/prompt, conditional on excluding the exact baseline token. Category / all and category / changed have different denominators. Intervals are pointwise Wilson 95% intervals for category / changed. p-values compare exact lexicon matches among changed predictions with the clean alternative sample using a one-sided Fisher exact test, with Holm correction across all 300 conditions. Conditions with no changes have no conditional category proportion and are assigned p=1 for correction.\n',
        '| Model | Prompt | Method | Layer | Strength | Category / all | Category / changed | Wilson 95% | Clean | Holm p |',
        '|---|---|---|---:|---:|---:|---:|---|---:|---:|'])
    for r in final_results:
        ci=r['category_rate_changed_wilson95']
        ci_text='N/A' if ci is None else f'{pct(ci[0])}–{pct(ci[1])}'
        summary.append(f'| {r["model_name"]} | {r["prompt_name"]} | {r["scaling_method"]} | {r["layer_idx"]} | {r["delta"]:g} | {r["category_count"]}/100 | {r["category_count"]}/{r["changed"]} | {ci_text} | {pct(r["null_category_rate"])} | {r["holm_p_300"]:.4g} |')
    summary.extend(['\n## Annotation sensitivity\n',
        'The primary endpoint counts exact members of declared category wordlists. Two additional exploratory checks are supplied: an expanded manufacturer/model-name list for parking and aviation, and treating every uncertain-kind clean alternative as a target while adding no uncertain noisy outputs. The latter is a conservative reassignment exercise, not a validated bound on every semantic interpretation. Each sensitivity analysis is separately Holm-adjusted across all 300 conditions.\n',
        '| Model | Prompt | Method | Strength | Primary Holm p | Brands/models Holm p | Uncertain-clean reassignment Holm p |',
        '|---|---|---|---:|---:|---:|---:|'])
    for r in final_results:
        if r['holm_p_300']<.05:
            brand = f'{r["expanded_holm_p_300"]:.4g}' if r['prompt_name'] in ('parking','pilot') else 'N/A'
            summary.append(f'| {r["model_name"]} | {r["prompt_name"]} | {r["scaling_method"]} | {r["delta"]:g} | {r["holm_p_300"]:.4g} | {brand} | {r["uncertainty_sensitivity_holm_300"]:.4g} |')
    summary.extend(['\n## Interpretation limits\n',
        '- Single-token category membership is not completed-word semantic interpretation. Instrument names can split into different tokens across models; presumed fragment completions are not inferred. These are not tokenizer-independent semantic scores.\n- Location and action targets are contextual categories, not similarity to the baseline words. Door-interaction verbs include actions that may not be plausible in this specific opening scenario; this is not a fluency/coherence measure.\n',
        '- All lexical definitions and hypothesis tests are retrospective/exploratory; the dictionaries were inspected against the supplied data. Multiplicity correction does not correct post-hoc category choice. Human review or independently fixed rules are required before calling this validated semantic evidence.\n- Exact lexicon nonmatches are not automatically semantically unrelated. Full words outside the dictionary, ambiguous brands, abbreviations, multilingual outputs and fragments can remain unresolved.\n- Clean samples are an alternative-token comparator, not human chance, not clean greedy error rates and not a causal model of speech errors.\n- The same clean sample is reused across conditions; adjusted tests permit dependent comparisons, and pooled repeated-null pseudo-replication is avoided.\n- The interval and test calculations assume trials provide independent sampled noise within each condition; std/absolute conditions share seeds and are paired, so do not treat them as independent replicates.\n- Cross-model magnitudes/calibrations differ; this does not rank model robustness by parameter count.\n- Report five prompts as selected case studies, not a representative sample of semantic categories.\n',
        '## Statistical references\n',
        '- [Fisher exact test documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html)\n- [Holm multiplicity adjustment documentation](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html)\n'])
    return '\n'.join(summary)


def write_outputs(data: dict, package: dict, output_dir: Path,
                  word_aid_bytes: bytes) -> None:
    """Write the same four release artifacts using explicit UTF-8 encoding."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir/'task_4_word_kind_aid.json').write_bytes(word_aid_bytes)
    (output_dir/'task_4_offline_analysis.json').write_text(
        json.dumps(package, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    (output_dir/'task_4_annotation_review.md').write_text(
        build_annotation_review(data, package), encoding='utf-8'
    )
    (output_dir/'task_4_offline_report.md').write_text(
        build_report(package), encoding='utf-8'
    )


def print_summary(package: dict) -> None:
    """Print results without changing the statistical comparison family."""
    pooled = package['final_layer_pooled_descriptive_only']
    results = package['conditions']
    final_results = [row for row in results if row['is_final_layer']]
    print('Validated 300 conditions / 30000 noisy predictions / 10000 clean samples.')
    print('\nFINAL LAYER POOLED (descriptive mixtures, not inference)')
    for r in pooled:
        print(r['model_name'],r['prompt_name'],'changes',r['changed'],'category',r['category_count'],'category/changed',pct(r['category_rate_changed']),'null',pct(r['null_category_rate']),'kinds',r['kind_counts'])
    print('\nENRICHMENT AFTER HOLM-300')
    for r in results:
        if r['holm_p_300']<.05:
            print(r['model_name'],r['prompt_name'],r['scaling_method'],r['layer_idx'],r['delta'],'matches',r['category_count'],'/',r['changed'],'null',pct(r['null_category_rate']),'p',r['holm_p_300'],'final',r['is_final_layer'])
    print('\nFINAL LAYER CONDITIONS')
    for r in final_results:
        print(r['model_name'],r['prompt_name'],r['scaling_method'],r['delta'],f'{r["category_count"]}/{r["changed"]}',pct(r['category_rate_changed']),pct(r['null_category_rate']),r['holm_p_300'])
