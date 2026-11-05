"""Command-line orchestration; importing this module does not run analysis."""

import argparse
from pathlib import Path
import zipfile

from .analysis import analyse_dataset
from .data_io import load_export, load_word_kind_aid
from .reporting import print_summary, write_outputs


def main(argv=None) -> int:
    """Load inputs, run pure analysis, and write outputs only on explicit use."""
    project_dir = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description='Reproduce the archived Task 4 analysis offline, without a GPU.'
    )
    parser.add_argument('input_zip', nargs='?', type=Path,
                        default=project_dir/'data'/'task_4_data.zip')
    parser.add_argument('output_dir', nargs='?', type=Path, default=Path('results'))
    parser.add_argument('--word-kind-aid', type=Path,
                        default=project_dir/'task_4_word_kind_aid.json',
                        help='Frozen lexical/uncertain word-kind aid JSON.')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress condition summaries.')
    args = parser.parse_args(argv)

    try:
        data, source_hash = load_export(args.input_zip)
        words, aid_bytes, aid_hash = load_word_kind_aid(args.word_kind_aid)
        package = analyse_dataset(data, source_hash, aid_hash, words)
        write_outputs(data, package, args.output_dir, aid_bytes)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(2, f'Analysis failed: {error}\n')

    if not args.quiet:
        print_summary(package)
    print(f'Analysis saved in: {args.output_dir.resolve()}')
    return 0
