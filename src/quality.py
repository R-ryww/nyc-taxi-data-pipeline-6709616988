
import csv
import logging

import duckdb

from config.settings import (
    RAW_DATA_DIR,
    CURATED_DATA_DIR,
    QUALITY_REPORT_DIR,
    TAXI_TYPES,
    MONTHS,
    PICKUP_COLUMNS,
    ANALYSIS_START,
    ANALYSIS_END
)

logger = logging.getLogger(__name__)


def get_raw_files(taxi_type):
    """รวบรวม path ของไฟล์ Parquet ทั้ง 6 เดือน"""

    files = []

    for month in MONTHS:
        file_path = (
            RAW_DATA_DIR
            / f"{taxi_type}_tripdata_2024-{month:02d}.parquet"
        )

        if file_path.exists():
            files.append(str(file_path))

    return files


def check_quality():
    """ตรวจสอบคุณภาพข้อมูล Raw และเปรียบเทียบกับ Curated"""

    con = duckdb.connect()

    try:
        curated_file = CURATED_DATA_DIR / "nyc_taxi_2024_h1.parquet"

        if not curated_file.exists():
            raise FileNotFoundError(
                "Curated dataset not found. Run transform.py first."
            )

        curated_path = str(curated_file).replace("'", "''")

        # อ่านจำนวน records ใน Curated แยกตาม taxi type
        curated_counts = dict(
            con.execute(f"""
                SELECT taxi_type, COUNT(*)
                FROM read_parquet('{curated_path}')
                GROUP BY taxi_type
            """).fetchall()
        )

        report_rows = []

        for taxi_type in TAXI_TYPES:
            files = get_raw_files(taxi_type)
            pickup_column = PICKUP_COLUMNS[taxi_type]

            if not files:
                logger.warning("No raw files found for %s", taxi_type)
                continue

            # เตรียมรายการไฟล์สำหรับ DuckDB
            file_list = ", ".join(
                "'" + path.replace("'", "''") + "'"
                for path in files
            )

            # ตรวจสอบจำนวนข้อมูลและคุณภาพ timestamp
            query = f"""
                SELECT
                    COUNT(*) AS total_records,

                    COUNT(*) FILTER (
                        WHERE "{pickup_column}" IS NULL
                    ) AS missing_pickup,

                    COUNT(*) FILTER (
                        WHERE "{pickup_column}" IS NOT NULL
                          AND TRY_CAST(
                              "{pickup_column}" AS TIMESTAMP
                          ) IS NULL
                    ) AS invalid_pickup,

                    COUNT(*) FILTER (
                        WHERE TRY_CAST(
                            "{pickup_column}" AS TIMESTAMP
                        ) < TIMESTAMP '{ANALYSIS_START}'
                           OR TRY_CAST(
                            "{pickup_column}" AS TIMESTAMP
                        ) >= TIMESTAMP '{ANALYSIS_END}'
                    ) AS out_of_period,

                    COUNT(*) FILTER (
                        WHERE TRY_CAST(
                            "{pickup_column}" AS TIMESTAMP
                        ) >= TIMESTAMP '{ANALYSIS_START}'
                          AND TRY_CAST(
                            "{pickup_column}" AS TIMESTAMP
                        ) < TIMESTAMP '{ANALYSIS_END}'
                    ) AS valid_records

                FROM read_parquet(
                    [{file_list}],
                    union_by_name = true
                )
            """

            result = con.execute(query).fetchone()

            (
                total_records,
                missing_pickup,
                invalid_pickup,
                out_of_period,
                valid_records
            ) = result

            curated_records = curated_counts.get(taxi_type, 0)

            # เปรียบเทียบจำนวน valid records กับ Curated
            status = (
                "PASS"
                if valid_records == curated_records
                else "CHECK"
            )

            report_rows.append({
                "taxi_type": taxi_type,
                "total_records": total_records,
                "missing_pickup": missing_pickup,
                "invalid_pickup": invalid_pickup,
                "out_of_period": out_of_period,
                "valid_records": valid_records,
                "curated_records": curated_records,
                "status": status
            })

        # บันทึกรายงานเป็น CSV
        report_file = (
            QUALITY_REPORT_DIR / "data_quality_report.csv"
        )

        fieldnames = [
            "taxi_type",
            "total_records",
            "missing_pickup",
            "invalid_pickup",
            "out_of_period",
            "valid_records",
            "curated_records",
            "status"
        ]

        with open(
            report_file,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )
            writer.writeheader()
            writer.writerows(report_rows)

        # แสดงผลบน Terminal
        print("\nDATA QUALITY REPORT")
        print("-" * 75)

        for row in report_rows:
            print(f"\nTaxi type: {row['taxi_type']}")
            print(f"  Total records:    {row['total_records']:,}")
            print(f"  Missing pickup:   {row['missing_pickup']:,}")
            print(f"  Invalid pickup:   {row['invalid_pickup']:,}")
            print(f"  Out of period:    {row['out_of_period']:,}")
            print(f"  Valid records:    {row['valid_records']:,}")
            print(f"  Curated records:  {row['curated_records']:,}")
            print(f"  Status:           {row['status']}")

        print("\nReport saved to:", report_file)

        if any(row["status"] != "PASS" for row in report_rows):
            print("\nWARNING: Some record counts need investigation.")
        else:
            print("\nAll quality checks passed!")

    finally:
        con.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    check_quality()
