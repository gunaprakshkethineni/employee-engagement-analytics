"""
Run the whole analysis from raw data to charts.

    python run_all.py

Each stage reads what the previous stage wrote, so the pipeline can also be
run one file at a time while working on a single phase. Regenerating the
synthetic data is optional and off by default, because it overwrites
data/raw/ - pass --regenerate to rebuild it from the seed.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import config
import step_00_profile
import step_01_clean
import step_02_constructs
import step_03_anova
import step_04_regression
import step_05_ros
import step_06_figures
import step_07_exports


def main():
    parser = argparse.ArgumentParser(description="Employee engagement analysis pipeline")
    parser.add_argument("--regenerate", action="store_true",
                        help="rebuild the synthetic survey before analysing it")
    arguments = parser.parse_args()

    started = time.time()
    print("=" * 70)
    print(f"EMPLOYEE ENGAGEMENT AND PERFORMANCE ANALYTICS - {config.DATA_LABEL}")
    print("=" * 70)

    if arguments.regenerate or not config.RAW_SURVEY_FILE.exists():
        import generate_synthetic_data
        generate_synthetic_data.main()

    step_00_profile.main()
    step_01_clean.main()
    step_02_constructs.main()
    step_03_anova.main()
    step_04_regression.main()
    step_05_ros.main()
    step_06_figures.main()
    step_07_exports.main()

    print("=" * 70)
    print(f"Pipeline finished in {time.time() - started:.1f}s. "
          f"See results/ ({len(list(config.RESULTS_DIR.glob('*')))} files).")
    print("=" * 70)


if __name__ == "__main__":
    main()
