
from config.settings import (
    PROJECT_ROOT,
    RAW_DATA_DIR,
    CURATED_DATA_DIR,
    TAXI_TYPES,
    MONTHS
)

print("Project root:", PROJECT_ROOT)
print("Raw data directory:", RAW_DATA_DIR)
print("Curated data directory:", CURATED_DATA_DIR)

print("Taxi types:", TAXI_TYPES)
print("Number of months:", len(MONTHS))

print("\nConfiguration loaded successfully!")
