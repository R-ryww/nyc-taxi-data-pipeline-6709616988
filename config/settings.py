
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Data directories
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
CURATED_DATA_DIR = PROJECT_ROOT / "data" / "curated"

# Output directories
ANALYSIS_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "analysis"
QUALITY_REPORT_DIR = PROJECT_ROOT / "outputs" / "quality_reports"
LOG_DIR = PROJECT_ROOT / "logs"

# NYC TLC data source
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

# Taxi types
TAXI_TYPES = [
    "yellow",
    "green",
    "fhv",
    "fhvhv"
]

# Analysis period: January - June 2024
MONTHS = range(1, 7)

ANALYSIS_START = "2024-01-01 00:00:00"
ANALYSIS_END = "2024-07-01 00:00:00"

# Pickup datetime column for each taxi type
PICKUP_COLUMNS = {
    "yellow": "tpep_pickup_datetime",
    "green": "lpep_pickup_datetime",
    "fhv": "pickup_datetime",
    "fhvhv": "pickup_datetime"
}

# Create required directories
DIRECTORIES = [
    RAW_DATA_DIR,
    CURATED_DATA_DIR,
    ANALYSIS_OUTPUT_DIR,
    QUALITY_REPORT_DIR,
    LOG_DIR
]

for directory in DIRECTORIES:
    directory.mkdir(parents=True, exist_ok=True)
