"""Read the archived export and validate this study's recorded dataset.

Validation raises explicit errors rather than relying on assert statements,
which Python can disable with -O. The expected sizes describe the archived
study and are not a general-purpose schema for arbitrary future experiments.
"""

from collections import Counter
from io import BytesIO
import hashlib
import json
import math
from pathlib import Path
import zipfile

EXPECTED_CONDITIONS = 300
EXPECTED_TRIALS = 100
EXPECTED_CLEAN_SAMPLES = 1000
EXPECTED_FINAL_CONDITIONS = 60


def load_export(path: Path) -> tuple:
    """Return the decoded input and a SHA-256 of its original ZIP bytes.

    Read the named JSON member directly. Nothing is extracted from the ZIP,
    so archive paths cannot create or overwrite files on disk.
    """
    raw = Path(path).read_bytes()
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f'Corrupt archive member: {bad_member}')
        data = json.loads(archive.read('task_4_data.json'))
    return data, hashlib.sha256(raw).hexdigest()


def load_word_kind_aid(path: Path) -> tuple:
    """Load the frozen lexical aid without using a host-dependent dictionary.

    Missing this file is an error: silently falling back to another machine's
    dictionary could change lexical/uncertain labels and sensitivity results.
    Category membership itself is defined separately in categories.py.
    """
    raw = Path(path).read_bytes()
    words = json.loads(raw)
    if not isinstance(words, list) or not all(isinstance(word, str) for word in words):
        raise ValueError('The word-kind aid must be a JSON list of strings.')
    return set(words), raw, hashlib.sha256(raw).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_export(data: dict) -> None:
    """Check reported counts against raw IDs and check clean-sample exclusions."""
    try:
        conditions = data['conditions']
        _require(len(conditions) == EXPECTED_CONDITIONS,
                 f'Expected {EXPECTED_CONDITIONS} conditions.')
        identities = set()

        for index, row in enumerate(conditions):
            label = f'Condition {index}: '
            model, prompt = row['model_name'], row['prompt_name']
            predictions = row['predictions']
            baseline_id = row['baseline_id']
            _require(model in data['models'] and prompt in data['prompts'],
                     label + 'unknown model or prompt.')
            _require(baseline_id == data['baselines'][model][prompt]['token_id'],
                     label + 'baseline ID differs from the saved baseline.')
            _require(len(predictions) == row['n_trials'] == EXPECTED_TRIALS,
                     label + 'trial count differs from predictions.')
            _require(predictions.count(baseline_id) == row['baseline_count'],
                     label + 'baseline count differs from predictions.')
            _require(math.isclose(row['change_rate'],
                                 1-row['baseline_count']/row['n_trials'],
                                 abs_tol=1e-12),
                     label + 'change rate differs from the counts.')
            alternatives = dict(Counter(
                str(token_id) for token_id in predictions if token_id != baseline_id
            ))
            _require(alternatives == row['alternatives'],
                     label + 'alternative counter differs from predictions.')
            _require(all(str(token_id) in data['token_lookup'][model]
                         for token_id in predictions),
                     label + 'a token ID is missing from the lookup.')
            _require(0 <= row['layer_idx'] < data['models'][model]['total_layers'],
                     label + 'layer index is outside the model.')
            identities.add((model, prompt, row['scaling_method'],
                            row['layer_idx'], row['delta']))

        _require(len(identities) == EXPECTED_CONDITIONS,
                 'Duplicate experimental conditions.')
        _require(sum(row['n_trials'] for row in conditions) == 30000,
                 'Expected 30000 perturbed predictions.')

        for model in data['models']:
            for prompt in data['prompts']:
                baseline_id = data['baselines'][model][prompt]['token_id']
                clean = data['clean_alternative_samples'][model][prompt]
                _require(len(clean['predictions']) == clean['n_samples'] == EXPECTED_CLEAN_SAMPLES,
                         f'{model}/{prompt}: incorrect clean sample size.')
                _require(baseline_id not in clean['predictions'],
                         f'{model}/{prompt}: clean alternatives contain the baseline ID.')
                _require(all(str(token_id) in data['token_lookup'][model]
                             for token_id in clean['predictions']),
                         f'{model}/{prompt}: clean token ID missing from lookup.')

        final_count = sum(
            row['layer_idx'] == data['models'][row['model_name']]['total_layers']-1
            for row in conditions
        )
        _require(final_count == EXPECTED_FINAL_CONDITIONS,
                 f'Expected {EXPECTED_FINAL_CONDITIONS} final-layer conditions.')
    except (KeyError, TypeError, ZeroDivisionError) as error:
        raise ValueError(f'Missing or invalid export field: {error}') from error
