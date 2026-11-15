
import logging
from pathlib import Path

import requests
import pyarrow.parquet as pq

from config.settings import (
    BASE_URL,
    RAW_DATA_DIR,
    TAXI_TYPES,
    MONTHS
)

# ตั้งค่าการบันทึกสถานะการทำงาน
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            Path(__file__).resolve().parents[1] / "logs" / "pipeline.log",
            encoding="utf-8"
        )
    ]
)

logger = logging.getLogger(__name__)


def get_file_path(taxi_type, month):
    """สร้างชื่อและตำแหน่งไฟล์ตามประเภทรถและเดือน"""

    filename = f"{taxi_type}_tripdata_2024-{month:02d}.parquet"

    return RAW_DATA_DIR / filename


def validate_parquet(file_path):
    """ตรวจสอบว่าไฟล์เป็น Parquet ที่สามารถอ่าน metadata ได้"""

    try:
        parquet_file = pq.ParquetFile(file_path)

        # ตรวจสอบจำนวนแถวในไฟล์
        row_count = parquet_file.metadata.num_rows

        return True, row_count

    except Exception as error:
        logger.warning(
            "Invalid Parquet file: %s (%s)",
            file_path.name,
            error
        )
        return False, 0


def download_file(url, file_path):
    """ดาวน์โหลดไฟล์และตรวจสอบความสมบูรณ์ก่อนจัดเก็บ"""

    temp_path = file_path.with_suffix(".parquet.tmp")

    try:
        logger.info("Downloading: %s", file_path.name)

        with requests.get(
            url,
            stream=True,
            timeout=(30, 300)
        ) as response:

            response.raise_for_status()

            with open(temp_path, "wb") as file:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if chunk:
                        file.write(chunk)

        # ตรวจสอบไฟล์ก่อนเปลี่ยนเป็นไฟล์จริง
        is_valid, row_count = validate_parquet(temp_path)

        if not is_valid:
            raise ValueError("Downloaded file is not valid Parquet")

        # เปลี่ยนชื่อไฟล์เมื่อดาวน์โหลดและตรวจสอบผ่านแล้ว
        temp_path.replace(file_path)

        logger.info(
            "Download successful: %s | Rows: %s",
            file_path.name,
            f"{row_count:,}"
        )

        return True

    except Exception as error:

        logger.error(
            "Download failed: %s | Error: %s",
            file_path.name,
            error
        )

        # ลบไฟล์ชั่วคราวเมื่อเกิดข้อผิดพลาด
        if temp_path.exists():
            temp_path.unlink()

        return False


def extract_all():
    """ดาวน์โหลดข้อมูล NYC Taxi ทั้ง 24 ไฟล์"""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for taxi_type in TAXI_TYPES:

        for month in MONTHS:

            file_path = get_file_path(taxi_type, month)

            url = (
                f"{BASE_URL}/"
                f"{file_path.name}"
            )

            # ตรวจสอบว่าไฟล์มีอยู่แล้วและอ่านได้หรือไม่
            if file_path.exists():

                is_valid, row_count = validate_parquet(file_path)

                if is_valid:
                    logger.info(
                        "Already exists, skipping: %s | Rows: %s",
                        file_path.name,
                        f"{row_count:,}"
                    )

                    results.append({
                        "taxi_type": taxi_type,
                        "month": month,
                        "status": "SKIPPED",
                        "rows": row_count
                    })

                    continue

                logger.warning(
                    "Existing file is invalid. Downloading again: %s",
                    file_path.name
                )

                file_path.unlink()

            # ดาวน์โหลดไฟล์ใหม่
            success = download_file(url, file_path)

            if success:
                _, row_count = validate_parquet(file_path)

                results.append({
                    "taxi_type": taxi_type,
                    "month": month,
                    "status": "SUCCESS",
                    "rows": row_count
                })

            else:
                results.append({
                    "taxi_type": taxi_type,
                    "month": month,
                    "status": "FAILED",
                    "rows": 0
                })

    return results


if __name__ == "__main__":

    logger.info("=" * 50)
    logger.info("NYC TAXI DATA EXTRACTION STARTED")
    logger.info("=" * 50)

    results = extract_all()

    successful = sum(
        r["status"] in ["SUCCESS", "SKIPPED"]
        for r in results
    )

    failed = sum(
        r["status"] == "FAILED"
        for r in results
    )

    print("\n========== EXTRACTION SUMMARY ==========")
    print(f"Total files: {len(results)}")
    print(f"Successful / Existing: {successful}")
    print(f"Failed: {failed}")

    print("\nFile details:")

    for result in results:
        print(
            f"{result['taxi_type']:6} | "
            f"Month {result['month']:02d} | "
            f"{result['status']:8} | "
            f"Rows: {result['rows']:,}"
        )

    logger.info("NYC TAXI DATA EXTRACTION FINISHED")
