"""Pure token annotation; no file access, model loading or inference."""

import re
import unicodedata

from .categories import (
    AMBIGUOUS_TERMS, BRAND_TERMS, CATEGORY_LEXICONS,
    EXTRA_COMPLETE_WORDS, FRAGMENT_TERMS, PLACE_TERMS,
)

def normalize(text: str) -> str:
    """Normalize boundary whitespace, Unicode form and case for word matching."""
    return unicodedata.normalize('NFC', text.strip()).casefold()


def annotate_token(data: dict, model: str, prompt: str, token_id: int, english_words: set) -> dict:
    """Classify one token using explicit inputs; never infer its missing suffix.

    Precedence is deliberate: special/formatting and baseline surface variants
    are separated before category matching. Supplied annotations are retained,
    while the exact-category endpoint remains defined by the fixed wordlists.
    """
    token_id = str(token_id)
    token = data['token_lookup'][model][token_id]
    text = token['text']
    word = normalize(text)
    baseline = normalize(data['baselines'][model][prompt]['token'])
    supplied = data.get('annotations', {}).get(model, {}).get(prompt, {}).get(token_id)
    if token['special']:
        kind, reason = 'special', 'tokenizer special-token flag'
    elif text and all(ch.isspace() or unicodedata.category(ch).startswith('P') for ch in text):
        kind, reason = 'formatting', 'whitespace/punctuation only'
    elif word and word == baseline:
        kind, reason = 'surface_variant', 'same baseline surface word after whitespace/case normalization'
    elif word in CATEGORY_LEXICONS[prompt]:
        kind, reason = 'lexical', 'explicit target-category lexicon'
    elif text.strip() in ('a', 'I'):
        kind, reason = 'lexical', 'complete article/pronoun, not a presumed subword fragment'
    elif supplied and supplied['kind'] in ('lexical', 'fragment'):
        kind, reason = supplied['kind'], 'supplied annotation'
    elif word in FRAGMENT_TERMS:
        kind, reason = 'fragment', 'explicitly reviewed incomplete English piece'
    elif len(word) <= 1 or word in AMBIGUOUS_TERMS[prompt]:
        kind, reason = 'uncertain', 'short/ambiguous piece; no presumed completion'
    elif re.fullmatch(r'[A-Za-z]+', word) and (word in english_words or word in EXTRA_COMPLETE_WORDS or word in BRAND_TERMS or word in PLACE_TERMS):
        kind, reason = 'lexical', 'English dictionary or explicit complete-word list; provisional token-kind label'
    else:
        kind, reason = 'uncertain', 'unreviewed string; not assumed to be a fragment or unrelated word'
    match = kind == 'lexical' and word in CATEGORY_LEXICONS[prompt] and word != baseline
    return {
        'text': text, 'piece': token['piece'], 'kind': kind,
        'category_match': match, 'reason': reason,
        'supplied_annotation': supplied,
        'brand_or_model_sensitivity_match': (
            match or (prompt in ('parking', 'pilot') and word in BRAND_TERMS and kind == 'lexical')
        ),
    }


def build_annotations(data: dict, english_words: set) -> dict:
    """Apply identical rules to all noisy outputs and clean comparison samples.

    Labels are scoped by model and prompt: a token can belong to the target
    category for one prompt but not another. Baseline token IDs are excluded
    from noisy alternatives; unchanged predictions are counted during analysis.
    """
    annotations = {}
    for model in data['models']:
        annotations[model] = {}
        for prompt in data['prompts']:
            baseline_id = data['baselines'][model][prompt]['token_id']
            token_ids = set(
                data['clean_alternative_samples'][model][prompt]['predictions']
            )
            token_ids.update(
                token_id
                for condition in data['conditions']
                if condition['model_name'] == model
                and condition['prompt_name'] == prompt
                for token_id in condition['predictions']
                if token_id != baseline_id
            )
            annotations[model][prompt] = {
                str(token_id): annotate_token(
                    data, model, prompt, token_id, english_words
                )
                for token_id in sorted(token_ids)
            }
    return annotations
