
# NYC Taxi Data Pipeline — Data Flow

## Pipeline Architecture

```mermaid
flowchart TD
    A["NYC TLC Trip Record Data"] --> B["Extract: Download 24 Parquet Files"]
    B --> C["Validate Parquet Files"]
    C --> D[("Raw Data<br/>data/raw/")]

    D --> E["Transform with DuckDB"]
    E --> F["Normalize Pickup Datetime"]
    F --> G["Filter Jan–Jun 2024"]
    G --> H[("Curated Dataset<br/>nyc_taxi_2024_h1.parquet")]

    D --> I["Data Quality Checks"]
    H --> I
    I --> J["Quality Report<br/>data_quality_report.csv"]

    H --> K["Usage Analysis"]
    K --> L["Analysis Output<br/>taxi_usage_analysis.csv"]

    B --> M["Pipeline Logs"]
    E --> M
    I --> M
    K --> M
```

## Pipeline Components

1. **Extract**
   - Downloads monthly Parquet files from NYC TLC.
   - Validates downloaded files before saving them.
   - Reuses existing valid files to avoid unnecessary downloads.

2. **Transform**
   - Uses DuckDB to process large Parquet datasets.
   - Standardizes pickup datetime columns.
   - Filters records to the January–June 2024 period.
   - Saves the curated dataset as Parquet.

3. **Data Quality**
   - Checks missing and invalid pickup timestamps.
   - Checks records outside the analysis period.
   - Compares valid raw record counts with curated record counts.
   - Saves results as a CSV report.

4. **Analysis**
   - Counts records for each taxi type.
   - Calculates each taxi type's percentage of total records.
   - Ranks taxi types by usage.

5. **Logging**
   - Records pipeline execution steps and status.
   - Records successful completion or failure.
