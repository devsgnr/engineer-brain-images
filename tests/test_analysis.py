"""Regression and independent count-statistics checks for the released study.

Run from the project directory with:
    python -m unittest discover -s tests -v

The reference fixture was captured before the refactor. Statistical checks use
integer combinatorics rather than repeating the implementation's log-space sum.
"""

import copy
import hashlib
import importlib
import json
import math
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from task4.analysis import analyse_dataset, summarize_predictions
from task4.annotation import annotate_token
from task4.data_io import load_export, load_word_kind_aid, validate_export
from task4.reporting import write_outputs
from task4.statistics import adjust_holm, fisher_greater, wilson


ROOT = Path(__file__).resolve().parents[1]


class ArchivedStudyTests(unittest.TestCase):
    """Check end-to-end behavior against the pre-refactor analysis."""

    @classmethod
    def setUpClass(cls):
        cls.data, cls.source_hash = load_export(ROOT/'data'/'task_4_data.zip')
        cls.words, cls.aid_bytes, cls.aid_hash = load_word_kind_aid(
            ROOT/'task_4_word_kind_aid.json'
        )
        cls.result = analyse_dataset(
            cls.data, cls.source_hash, cls.aid_hash, cls.words
        )
        cls.expected = json.loads(
            (ROOT/'tests'/'expected_results.json').read_text(encoding='utf-8')
        )

    def assert_nested_equal(self, actual, expected, path='result'):
        """Allow numerical roundoff, while keeping labels and counts exact."""
        if isinstance(expected, float):
            self.assertTrue(
                math.isclose(actual, expected, rel_tol=2e-9, abs_tol=1e-12),
                f'{path}: {actual} != {expected}',
            )
        elif isinstance(expected, dict):
            self.assertEqual(set(actual), set(expected), path)
            for key in expected:
                self.assert_nested_equal(actual[key], expected[key], f'{path}.{key}')
        elif isinstance(expected, list):
            self.assertEqual(len(actual), len(expected), path)
            for index, (item, reference) in enumerate(zip(actual, expected)):
                self.assert_nested_equal(item, reference, f'{path}[{index}]')
        else:
            self.assertEqual(actual, expected, path)

    def test_all_results_reproduce_the_previous_analysis(self):
        def without_tokens(row):
            return {key: value for key, value in row.items() if key != 'tokens'}

        actual = {
            key: self.result[key] for key in [
                'status', 'source_sha256', 'definitions', 'lexicons',
                'dictionary_word_kind_aid_sha256',
            ]
        }
        actual['annotations_sha256'] = hashlib.sha256(
            json.dumps(
                self.result['annotations'], sort_keys=True,
                ensure_ascii=False, separators=(',', ':'),
            ).encode()
        ).hexdigest()
        actual['null_results'] = {
            model: {prompt: without_tokens(row) for prompt, row in prompts.items()}
            for model, prompts in self.result['null_results'].items()
        }
        actual['conditions'] = [without_tokens(row) for row in self.result['conditions']]
        actual['pooled'] = [
            without_tokens(row)
            for row in self.result['final_layer_pooled_descriptive_only']
        ]
        self.assert_nested_equal(actual, self.expected)

    def test_all_fisher_values_against_exact_integer_counts(self):
        for row in self.result['conditions']:
            k, n = row['category_count'], row['changed']
            k0, n0 = row['null_category_count'], row['null_n']
            if not n:
                exact = 1.
            else:
                total, successes = n+n0, k+k0
                numerator = sum(
                    math.comb(successes, value)
                    * math.comb(total-successes, n-value)
                    for value in range(k, min(successes, n)+1)
                    if 0 <= n-value <= total-successes
                )
                exact = numerator/math.comb(total, n)
            self.assertTrue(math.isclose(
                row['fisher_greater_p'], exact, rel_tol=2e-9, abs_tol=1e-12
            ))

    def test_inconsistent_baseline_count_is_rejected(self):
        invalid = copy.deepcopy(self.data)
        invalid['conditions'][0]['baseline_count'] -= 1
        with self.assertRaisesRegex(ValueError, 'baseline count'):
            validate_export(invalid)

    def test_duplicate_condition_is_rejected(self):
        invalid = copy.deepcopy(self.data)
        invalid['conditions'][1] = copy.deepcopy(invalid['conditions'][0])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate_export(invalid)

    def test_clean_sample_containing_baseline_is_rejected(self):
        invalid = copy.deepcopy(self.data)
        invalid['clean_alternative_samples']['Gemma']['music']['predictions'][0] = (
            invalid['baselines']['Gemma']['music']['token_id']
        )
        with self.assertRaisesRegex(ValueError, 'contain the baseline'):
            validate_export(invalid)

    def annotate_text(self, model, prompt, text):
        token_id = next(
            token_id for token_id, info in self.data['token_lookup'][model].items()
            if info['text'] == text
        )
        return annotate_token(self.data, model, prompt, int(token_id), self.words)

    def test_prefix_is_not_expanded_to_an_instrument(self):
        annotation = self.annotate_text('Gemma', 'music', ' harmon')
        self.assertEqual(annotation['kind'], 'uncertain')
        self.assertFalse(annotation['category_match'])

    def test_complete_adjective_is_not_a_fragment(self):
        annotation = self.annotate_text('Gemma', 'music', ' electric')
        self.assertEqual(annotation['kind'], 'lexical')
        self.assertFalse(annotation['category_match'])

    def test_baseline_case_variant_is_separate_from_substitution(self):
        annotation = self.annotate_text('SmolLM2', 'parking', ' Car')
        self.assertEqual(annotation['kind'], 'surface_variant')
        self.assertFalse(annotation['category_match'])

    def test_article_is_lexical_despite_being_one_letter(self):
        annotation = self.annotate_text('Gemma', 'location', ' a')
        self.assertEqual(annotation['kind'], 'lexical')
        self.assertFalse(annotation['category_match'])

    def test_special_tokens_are_not_lexical_words(self):
        token_id = next(
            token_id for token_id, info in self.data['token_lookup']['Gemma'].items()
            if info['special']
        )
        annotation = annotate_token(self.data, 'Gemma', 'music', int(token_id), self.words)
        self.assertEqual(annotation['kind'], 'special')
        self.assertFalse(annotation['category_match'])

    def test_output_files_are_written_only_when_requested(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'reports'
            write_outputs(self.data, self.result, output, self.aid_bytes)
            self.assertEqual(
                {path.name for path in output.iterdir()},
                {
                    'task_4_offline_analysis.json', 'task_4_offline_report.md',
                    'task_4_annotation_review.md', 'task_4_word_kind_aid.json',
                },
            )
            self.assertEqual(
                json.loads((output/'task_4_offline_analysis.json').read_text()),
                self.result,
            )


class StatisticalEdgeTests(unittest.TestCase):
    def test_wilson_boundaries_and_empty_sample(self):
        self.assertIsNone(wilson(0, 0))
        self.assertAlmostEqual(wilson(0, 100)[0], 0.)
        self.assertAlmostEqual(wilson(0, 100)[1], 0.0369934982, places=9)
        self.assertAlmostEqual(wilson(100, 100)[0], 1-wilson(0, 100)[1])
        self.assertAlmostEqual(wilson(100, 100)[1], 1.)

    def test_holm_adjusts_the_whole_family(self):
        rows = [{'raw': value} for value in [0.01, 0.04, 0.03]]
        adjust_holm(rows, 'raw', 'adjusted')
        self.assertEqual([row['adjusted'] for row in rows], [0.03, 0.06, 0.06])

    def test_no_changed_predictions_has_no_conditional_rate(self):
        result = summarize_predictions([7]*100, 7, {})
        self.assertEqual(result['changed'], 0)
        self.assertIsNone(result['category_rate_changed'])
        self.assertIsNone(result['category_rate_changed_wilson95'])
        self.assertEqual(fisher_greater(0, 0, 300, 1000), 1.)

    def test_imports_do_not_read_exports_or_write_files(self):
        import task4.cli
        with patch('pathlib.Path.read_bytes') as read, \
             patch('pathlib.Path.write_bytes') as write_bytes, \
             patch('pathlib.Path.write_text') as write_text, \
             patch('pathlib.Path.mkdir') as mkdir:
            importlib.reload(task4.cli)
            runpy.run_path(str(ROOT/'analyse_task4.py'), run_name='import_test')
            read.assert_not_called()
            write_bytes.assert_not_called()
            write_text.assert_not_called()
            mkdir.assert_not_called()


if __name__ == '__main__':
    unittest.main()
