
import logging

import duckdb

from config.settings import (
    RAW_DATA_DIR,
    CURATED_DATA_DIR,
    TAXI_TYPES,
    MONTHS,
    PICKUP_COLUMNS,
    ANALYSIS_START,
    ANALYSIS_END
)

# ตั้งค่า logging
logger = logging.getLogger(__name__)


def get_raw_files(taxi_type):
    """ค้นหาไฟล์ Parquet ของ taxi type ที่กำหนด"""

    files = []

    for month in MONTHS:
        file_path = (
            RAW_DATA_DIR
            / f"{taxi_type}_tripdata_2024-{month:02d}.parquet"
        )

        if file_path.exists():
            files.append(str(file_path))

    return files


def transform_all():
    """รวมและแปลงข้อมูลแท็กซี่ทั้ง 4 ประเภท"""

    con = duckdb.connect()

    try:
        queries = []

        for taxi_type in TAXI_TYPES:
            files = get_raw_files(taxi_type)
            pickup_column = PICKUP_COLUMNS[taxi_type]

            if not files:
                logger.warning("No raw files found for %s", taxi_type)
                continue

            # สร้างรายการ path สำหรับ DuckDB
            file_list = ", ".join(
                "'" + path.replace("'", "''") + "'"
                for path in files
            )

            # แปลงข้อมูลให้อยู่ใน schema เดียวกัน
            query = f"""
                SELECT
                    '{taxi_type}' AS taxi_type,
                    TRY_CAST("{pickup_column}" AS TIMESTAMP)
                        AS pickup_datetime
                FROM read_parquet(
                    [{file_list}],
                    union_by_name = true
                )
            """

            queries.append(query)

            logger.info(
                "Prepared %s: %d files",
                taxi_type,
                len(files)
            )

        if not queries:
            raise RuntimeError("No data files available for transformation")

        # รวมข้อมูลจากทุก taxi type
        combined_query = "\nUNION ALL\n".join(queries)

        final_query = f"""
            SELECT
                taxi_type,
                pickup_datetime
            FROM (
                {combined_query}
            )
            WHERE pickup_datetime IS NOT NULL
              AND pickup_datetime >= TIMESTAMP '{ANALYSIS_START}'
              AND pickup_datetime < TIMESTAMP '{ANALYSIS_END}'
        """

        # บันทึกเป็น Curated Parquet
        output_file = CURATED_DATA_DIR / "nyc_taxi_2024_h1.parquet"

        con.execute(f"""
            COPY ({final_query})
            TO '{str(output_file).replace("'", "''")}'
            (FORMAT PARQUET, COMPRESSION ZSTD)
        """)

        # ตรวจสอบจำนวนข้อมูลที่บันทึก
        result = con.execute(f"""
            SELECT
                taxi_type,
                COUNT(*) AS total_records
            FROM read_parquet('{str(output_file).replace("'", "''")}')
            GROUP BY taxi_type
            ORDER BY taxi_type
        """).fetchall()

        logger.info("Transformation completed successfully")
        print("\nCurated data summary:")

        for taxi_type, count in result:
            print(f"{taxi_type}: {count:,} records")

        print(f"\nOutput saved to: {output_file}")

    finally:
        con.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("Starting transformation...")
    transform_all()
