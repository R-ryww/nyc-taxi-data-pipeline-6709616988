import argparse
import csv
import logging
from datetime import datetime

from src.extract import extract_all
from src.transform import transform_all
from src.quality import check_quality
from src.analyze import analyze_taxi_usage

from config.settings import (
    QUALITY_REPORT_DIR,
    LOG_DIR
)


# บันทึกสถานะ Pipeline แยกจาก Log ของแต่ละขั้นตอน
logger = logging.getLogger("pipeline")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    file_handler = logging.FileHandler(
        LOG_DIR / "pipeline_runs.log",
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def run_pipeline(force_refresh=False):
    """เรียกใช้งานทุกขั้นตอนของ Data Pipeline"""

    start_time = datetime.now()

    logger.info("=" * 60)
    logger.info("PIPELINE STARTED")

    if force_refresh:
        logger.info("REFRESH MODE ENABLED")

    try:

        # STEP 1: EXTRACT
        logger.info("STEP 1: Extracting raw data...")

        extraction_results = extract_all(
            force_refresh=force_refresh
        )

        failed_files = [
            item for item in extraction_results
            if item.get("status") == "FAILED"
        ]

        if failed_files:
            raise RuntimeError(
                f"Extraction failed for {len(failed_files)} files"
            )

        logger.info("STEP 1: Extract completed")

        # STEP 2: TRANSFORM
        logger.info("STEP 2: Transforming data...")

        transform_all()

        logger.info("STEP 2: Transform completed")

        # STEP 3: QUALITY CHECK
        logger.info("STEP 3: Checking data quality...")

        check_quality()

        report_file = (
            QUALITY_REPORT_DIR / "data_quality_report.csv"
        )

        with open(
            report_file,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            quality_results = list(csv.DictReader(file))

        if not quality_results:
            raise RuntimeError("Data quality report is empty")

        failed_checks = [
            row for row in quality_results
            if row["status"] != "PASS"
        ]

        if failed_checks:
            raise RuntimeError(
                "Data quality checks did not pass"
            )

        logger.info("STEP 3: Quality checks passed")

        # STEP 4: ANALYSIS
        logger.info("STEP 4: Analyzing taxi usage...")

        analyze_taxi_usage()

        logger.info("STEP 4: Analysis completed")

        # PIPELINE SUCCESS
        duration = (
            datetime.now() - start_time
        ).total_seconds()

        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("Total duration: %.2f seconds", duration)

    except Exception:

        logger.exception("PIPELINE FAILED")
        raise

    finally:

        logger.info("PIPELINE RUN FINISHED")
        logger.info("=" * 60)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="NYC Taxi Data Pipeline"
    )

    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Download all raw data files again"
    )

    args = parser.parse_args()

    run_pipeline(force_refresh=args.refresh)
