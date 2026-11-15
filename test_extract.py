
from src.extract import get_file_path
from config.settings import TAXI_TYPES, MONTHS

print("Testing extraction configuration...")

total_files = 0

for taxi_type in TAXI_TYPES:
    for month in MONTHS:

        file_path = get_file_path(taxi_type, month)

        print(file_path.name)

        total_files += 1

print("\nTotal files required:", total_files)

assert total_files == 24

print("Extraction configuration test passed!")
