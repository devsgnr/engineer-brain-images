"""Run the offline Task 4 analysis.

    python analyse_task4.py data/task_4_data.zip results
    python analyse_task4.py --help

The analysis implementation lives in task4/. No third-party packages or GPU
are required. Imports are side-effect free; analysis starts only via main().
"""

from task4.cli import main


if __name__ == '__main__':
    raise SystemExit(main())
