"""Assemble study results from explicit data, annotations and count statistics.

This module is independent of file paths and report formatting. It performs no
model inference and makes no claim that wordlist labels are semantic truth.
"""

import collections

from .annotation import build_annotations
from .categories import CATEGORY_DEFINITIONS, CATEGORY_LEXICONS
from .data_io import validate_export
from .statistics import adjust_holm, fisher_greater, wilson

def summarize_predictions(predictions: list, baseline_id: int, token_annotations: dict) -> dict:
    """Count one sample without confusing all-trial and changed-trial rates.

    Zero changed predictions gives None, not zero, for the proportion
    conditional on a change. Pooled samples are only descriptive mixtures.
    """
    counts = collections.Counter(predictions)
    kinds = collections.Counter()
    category_count = 0
    expanded_count = 0
    tokens = []
    for token_id, count in counts.items():
        if token_id == baseline_id:
            kinds['unchanged'] += count
            continue
        a = token_annotations[str(token_id)]
        kinds[a['kind']] += count
        category_count += count*int(a['category_match'])
        expanded_count += count*int(a['brand_or_model_sensitivity_match'])
        tokens.append({'token_id': token_id, 'count': count, **a})
    changed = len(predictions)-counts[baseline_id]
    assert sum(kinds.values()) == len(predictions)
    return {
        'n_trials': len(predictions), 'changed': changed,
        'category_count': category_count,
        'category_rate_all': category_count/len(predictions),
        'category_rate_changed': category_count/changed if changed else None,
        'category_rate_changed_wilson95': wilson(category_count, changed),
        'expanded_category_count': expanded_count,
        'expanded_category_rate_changed': expanded_count/changed if changed else None,
        'kind_counts': dict(kinds),
        'unknown_semantic_upper_changed': (category_count+kinds['uncertain'])/changed if changed else None,
        'tokens': sorted(tokens, key=lambda x: (-x['count'], x['token_id'])),
    }


def analyse_dataset(data: dict, source_sha256: str,
                    word_aid_sha256: str, english_words: set) -> dict:
    """Build the same machine-readable analysis as the original research script."""
    validate_export(data)
    annotations = build_annotations(data, english_words)

    # Exactly one clean sample is summarized per model/prompt. Reusing it for
    # comparisons does not turn it into new independent data for each condition.
    null_results = {}
    for model in data['models']:
        null_results[model] = {}
        for prompt in data['prompts']:
            baseline_id = data['baselines'][model][prompt]['token_id']
            predictions = data['clean_alternative_samples'][model][prompt]['predictions']
            null_results[model][prompt] = summarize_predictions(
                predictions, baseline_id, annotations[model][prompt]
            )

    results = []
    for row in data['conditions']:
        model, prompt = row['model_name'], row['prompt_name']
        result = summarize_predictions(
            row['predictions'], row['baseline_id'], annotations[model][prompt]
        )
        clean = null_results[model][prompt]
        result.update({key: row[key] for key in [
            'model_name', 'prompt_name', 'scaling_method', 'layer_idx',
            'delta', 'seed', 'mean_noise_l2', 'mean_relative_noise',
        ]})
        result['is_final_layer'] = row['layer_idx'] == data['models'][model]['total_layers']-1
        result['null_category_count'] = clean['category_count']
        result['null_n'] = clean['n_trials']
        result['null_category_rate'] = clean['category_rate_changed']
        result['difference_percentage_points'] = (
            100*(result['category_rate_changed']-result['null_category_rate'])
            if result['changed'] else None
        )
        result['fisher_greater_p'] = fisher_greater(
            result['category_count'], result['changed'],
            clean['category_count'], clean['n_trials'],
        )
        result['expanded_fisher_p'] = fisher_greater(
            result['expanded_category_count'], result['changed'],
            clean['expanded_category_count'], clean['n_trials'],
        )

        # Conservative sensitivity exercise, not a universal semantic bound:
        # assign uncertain clean tokens to the target and add no uncertain
        # noisy outputs to the target. Keep it separate from the primary test.
        result['uncertain_clean_count'] = clean['kind_counts'].get('uncertain', 0)
        result['uncertainty_sensitivity_p'] = fisher_greater(
            result['category_count'], result['changed'],
            clean['category_count']+result['uncertain_clean_count'],
            clean['n_trials'],
        )
        results.append(result)

    # Correct each declared family over all 300 conditions, including conditions
    # with no changes. Selecting significant final-layer examples first would
    # change the comparison family and would not reproduce the original analysis.
    for raw_key, adjusted_key in [
        ('fisher_greater_p', 'holm_p_300'),
        ('expanded_fisher_p', 'expanded_holm_p_300'),
        ('uncertainty_sensitivity_p', 'uncertainty_sensitivity_holm_300'),
    ]:
        adjust_holm(results, raw_key, adjusted_key)

    final_results = [row for row in results if row['is_final_layer']]
    pooled = []
    for model in data['models']:
        for prompt in data['prompts']:
            selected = [
                row for row in final_results
                if row['model_name'] == model and row['prompt_name'] == prompt
            ]
            predictions = [
                token_id for row in data['conditions']
                if row['model_name'] == model and row['prompt_name'] == prompt
                and row['layer_idx'] == data['models'][model]['total_layers']-1
                for token_id in row['predictions']
            ]
            pool = summarize_predictions(
                predictions, data['baselines'][model][prompt]['token_id'],
                annotations[model][prompt],
            )
            pool.update(
                model_name=model, prompt_name=prompt,
                null_category_rate=null_results[model][prompt]['category_rate_changed'],
                conditions=len(selected),
            )
            pooled.append(pool)

    # Preserve the existing output schema and ordering for exact reproduction.
    return {
        'status': 'Exploratory exact-token category analysis; not independent human semantic ground truth.',
        'source_sha256': source_sha256,
        'definitions': CATEGORY_DEFINITIONS,
        'lexicons': {prompt: sorted(words) for prompt, words in CATEGORY_LEXICONS.items()},
        'dictionary_word_kind_aid_sha256': word_aid_sha256,
        'normalization': 'NFC, strip boundary whitespace, casefold. Baseline-normalized word variants treated separately.',
        'primary_scope': '60 final-layer conditions, all ten model/prompt pairs; all 300 conditions supplied as supplementary results.',
        'test': 'Exploratory one-sided Fisher exact comparison of category matches among changed outputs vs 1000 clean alternatives. Holm correction across all 300 conditions. Shared null not multiplied by condition count.',
        'annotations': annotations,
        'null_results': null_results,
        'conditions': results,
        'final_layer_pooled_descriptive_only': pooled,
    }
