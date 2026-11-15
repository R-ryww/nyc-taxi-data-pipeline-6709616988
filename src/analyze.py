
import logging

import duckdb

from config.settings import (
    CURATED_DATA_DIR,
    ANALYSIS_OUTPUT_DIR
)

logger = logging.getLogger(__name__)


def analyze_taxi_usage():
    """วิเคราะห์จำนวน trips แยกตาม taxi type"""

    con = duckdb.connect()

    try:
        curated_file = (
            CURATED_DATA_DIR / "nyc_taxi_2024_h1.parquet"
        )

        if not curated_file.exists():
            raise FileNotFoundError(
                "Curated dataset not found. Run transform.py first."
            )

        curated_path = str(curated_file).replace("'", "''")

        # นับจำนวน records และคำนวณสัดส่วน
        query = f"""
            WITH taxi_counts AS (
                SELECT
                    taxi_type,
                    COUNT(*) AS total_trips
                FROM read_parquet('{curated_path}')
                GROUP BY taxi_type
            )
            SELECT
                taxi_type,
                total_trips,
                ROUND(
                    total_trips * 100.0
                    / SUM(total_trips) OVER (),
                    2
                ) AS percentage,
                RANK() OVER (
                    ORDER BY total_trips DESC
                ) AS usage_rank
            FROM taxi_counts
            ORDER BY total_trips DESC
        """

        result = con.execute(query).df()

        # แสดงผลการวิเคราะห์
        print("\nNYC TAXI USAGE ANALYSIS")
        print("Period: January - June 2024")
        print("-" * 60)

        print(result.to_string(index=False))

        winner = result.iloc[0]

        print("\nMOST USED TAXI TYPE")
        print(f"Taxi type: {winner['taxi_type']}")
        print(f"Total trips: {winner['total_trips']:,}")
        print(f"Share: {winner['percentage']}%")

        # บันทึกผลเป็น CSV
        output_file = (
            ANALYSIS_OUTPUT_DIR / "taxi_usage_analysis.csv"
        )

        result.to_csv(output_file, index=False)

        print("\nAnalysis saved to:", output_file)

        logger.info("Taxi usage analysis completed")

    finally:
        con.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    analyze_taxi_usage()
