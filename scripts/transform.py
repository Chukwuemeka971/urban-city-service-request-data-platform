import os
from pathlib import Path

import polars as pl
from dotenv import load_dotenv

from src.utils.logger import get_logger


# --------------------------------------------------
# Project paths
# --------------------------------------------------

LOCATION = Path(__file__).resolve().parent
PROJECT_ROOT = LOCATION.parent


# --------------------------------------------------
# Environment variables
# --------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env")


# --------------------------------------------------
# Logger
# --------------------------------------------------

logger = get_logger(__name__)


# --------------------------------------------------
# Azure configuration
# --------------------------------------------------

ACCOUNT_NAME = "urbancitystorage"
ACCOUNT_KEY = os.getenv("ACCOUNT_KEY")

BRONZE_CONTAINER = "bronze"
SILVER_CONTAINER = "silver"

SOURCE_URI = (
    f"az://{BRONZE_CONTAINER}/urban_service_requests.csv"
)

TARGET_URI = (
    f"az://{SILVER_CONTAINER}/urban_service_requests.parquet"
)


# --------------------------------------------------
# Azure storage options
# --------------------------------------------------

STORAGE_OPTIONS = {
    "account_name": ACCOUNT_NAME,
    "account_key": ACCOUNT_KEY,
}


# --------------------------------------------------
# Silver column mapping
# --------------------------------------------------

COLUMN_MAPPING = {
    "Unique Key": "request_id",
    "Created Date": "created_date",
    "Closed Date": "closed_date",
    "Agency": "agency",
    "Problem (formerly Complaint Type)": "problem",
    "Problem Detail (formerly Descriptor)": "problem_detail",
    "Location Type": "location_type",
    "Incident Address": "incident_address",
    "City": "city",
    "Borough": "borough",
    "Status": "status",
    "Latitude": "latitude",
    "Longitude": "longitude",
}


# --------------------------------------------------
# Valid status values
# --------------------------------------------------

VALID_STATUSES = {
    "Open",
    "In Progress",
    "Closed",
}


# --------------------------------------------------
# Validate source columns
# --------------------------------------------------

def validate_source_columns(df: pl.DataFrame) -> None:
    """Check that all required source columns exist."""

    missing_columns = [
        column
        for column in COLUMN_MAPPING
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required source columns: {missing_columns}"
        )

    logger.info(
        "Source column validation passed"
    )


# --------------------------------------------------
# Transform data
# --------------------------------------------------

def transform_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Transform a Bronze DataFrame into a Silver DataFrame.

    This function only transforms data.
    It does not read from or write to Azure.
    """

    logger.info(
        "Starting data transformation"
    )

    # --------------------------------------------------
    # Select and rename columns
    # --------------------------------------------------

    logger.info(
        "Selecting and renaming Silver columns"
    )

    df_refined = df.select(
        [
            pl.col(source).alias(target)
            for source, target in COLUMN_MAPPING.items()
        ]
    )

    # --------------------------------------------------
    # Convert date columns
    # --------------------------------------------------

    logger.info(
        "Converting date columns"
    )

    df_refined = df_refined.with_columns(
        [
            pl.col("created_date")
            .str.to_datetime(
                format="%m/%d/%Y %H:%M",
                strict=False
            ),

            pl.col("closed_date")
            .str.to_datetime(
                format="%m/%d/%Y %H:%M",
                strict=False
            ),
        ]
    )

    # --------------------------------------------------
    # Clean text columns
    # --------------------------------------------------

    logger.info(
        "Cleaning text columns"
    )

    text_columns = [
        "agency",
        "problem",
        "problem_detail",
        "location_type",
        "incident_address",
        "city",
        "borough",
        "status",
    ]

    df_refined = df_refined.with_columns(
        [
            pl.col(column)
            .str.strip_chars()
            for column in text_columns
        ]
    )

    # --------------------------------------------------
    # Standardise selected fields
    # --------------------------------------------------

    logger.info(
        "Standardising city and borough values"
    )

    df_refined = df_refined.with_columns(
        [
            pl.col("city").str.to_uppercase(),
            pl.col("borough").str.to_uppercase(),
        ]
    )

    logger.info(
        "Data transformation completed"
    )

    return df_refined


# --------------------------------------------------
# Validate transformed data
# --------------------------------------------------

def validate_transformed_data(
    df: pl.DataFrame,
    source_df: pl.DataFrame,
) -> None:
    """Validate the Silver DataFrame before loading."""

    logger.info(
        "Starting Silver data validation"
    )

    # --------------------------------------------------
    # Row count
    # --------------------------------------------------

    if df.height != source_df.height:
        raise ValueError(
            "Row count changed during transformation"
        )

    logger.info(
        "Row count validation passed: %s rows",
        df.height
    )

    # --------------------------------------------------
    # Column validation
    # --------------------------------------------------

    expected_columns = list(
        COLUMN_MAPPING.values()
    )

    if df.columns != expected_columns:
        raise ValueError(
            "Silver columns do not match expected schema"
        )

    logger.info(
        "Silver schema validation passed"
    )

    # --------------------------------------------------
    # request_id validation
    # --------------------------------------------------

    null_request_ids = (
        df
        .select(
            pl.col("request_id")
            .is_null()
            .sum()
        )
        .item()
    )

    if null_request_ids > 0:
        raise ValueError(
            f"Found {null_request_ids} null request_id values"
        )

    duplicate_keys = (
        df
        .group_by("request_id")
        .agg(
            pl.len().alias("count")
        )
        .filter(
            pl.col("count") > 1
        )
    )

    if duplicate_keys.height > 0:
        raise ValueError(
            f"Duplicate request_id values found: "
            f"{duplicate_keys.height}"
        )

    logger.info(
        "request_id validation passed"
    )

    # --------------------------------------------------
    # Status validation
    # --------------------------------------------------

    invalid_statuses = (
        df
        .filter(
            pl.col("status").is_not_null()
            & ~pl.col("status").is_in(
                list(VALID_STATUSES)
            )
        )
    )

    if invalid_statuses.height > 0:
        raise ValueError(
            f"Invalid status values found: "
            f"{invalid_statuses.height}"
        )

    logger.info(
        "Status validation passed"
    )

    # --------------------------------------------------
    # Created date validation
    # --------------------------------------------------

    created_date_nulls = (
        df
        .select(
            pl.col("created_date")
            .is_null()
            .sum()
        )
        .item()
    )

    if created_date_nulls > 0:
        raise ValueError(
            f"Found {created_date_nulls} invalid "
            "created_date values"
        )

    logger.info(
        "Created date validation passed"
    )

    # --------------------------------------------------
    # Closed date consistency
    # --------------------------------------------------

    inconsistent_closed_dates = (
        df
        .filter(
            (
                (pl.col("status") == "Closed")
                & pl.col("closed_date").is_null()
            )
            |
            (
                (pl.col("status") != "Closed")
                & pl.col("closed_date").is_not_null()
            )
        )
    )

    if inconsistent_closed_dates.height > 0:
        raise ValueError(
            "Status and Closed Date are inconsistent: "
            f"{inconsistent_closed_dates.height} records"
        )

    logger.info(
        "Status / Closed Date validation passed"
    )

    # --------------------------------------------------
    # Geographic validation
    # --------------------------------------------------

    invalid_coordinates = df.filter(
        (
            pl.col("latitude").is_not_null()
            & (
                (pl.col("latitude") < -90)
                | (pl.col("latitude") > 90)
            )
        )
        |
        (
            pl.col("longitude").is_not_null()
            & (
                (pl.col("longitude") < -180)
                | (pl.col("longitude") > 180)
            )
        )
    )

    if invalid_coordinates.height > 0:
        raise ValueError(
            "Invalid geographic coordinates found: "
            f"{invalid_coordinates.height}"
        )

    logger.info(
        "Geographic validation passed"
    )

    # --------------------------------------------------
    # Validation complete
    # --------------------------------------------------

    logger.info(
        "All Silver data validation checks passed"
    )


# --------------------------------------------------
# Read Bronze data
# --------------------------------------------------

def read_bronze() -> pl.DataFrame:
    """Read raw CSV data from Azure Bronze."""

    logger.info(
        "Reading Bronze data from %s",
        SOURCE_URI
    )

    df = pl.read_csv(
        SOURCE_URI,
        storage_options=STORAGE_OPTIONS,
    )

    logger.info(
        "Bronze data loaded: %s rows, %s columns",
        df.height,
        df.width
    )

    return df


# --------------------------------------------------
# Write Silver data
# --------------------------------------------------

def write_silver(df: pl.DataFrame) -> None:
    """Write transformed data to Azure Silver as Parquet."""

    logger.info(
        "Writing Silver data to %s",
        TARGET_URI
    )

    df.write_parquet(
        TARGET_URI,
        storage_options=STORAGE_OPTIONS,
        compression="snappy",
    )

    logger.info(
        "Silver data successfully written"
    )


# --------------------------------------------------
# Main pipeline
# --------------------------------------------------

def transform() -> None:
    """Run the Bronze → Silver transformation pipeline."""

    logger.info(
        "Starting Bronze → Silver pipeline"
    )

    if not ACCOUNT_KEY:
        raise ValueError(
            "ACCOUNT_KEY is not set in .env"
        )

    try:
        # Read
        source_df = read_bronze()

        # Validate source
        validate_source_columns(source_df)

        # Transform
        silver_df = transform_data(source_df)

        # Validate Silver
        validate_transformed_data(
            silver_df,
            source_df,
        )

        # Write
        write_silver(silver_df)

        logger.info(
            "Bronze → Silver pipeline completed successfully"
        )

    except Exception:
        logger.exception(
            "Bronze → Silver pipeline failed"
        )
        raise


# --------------------------------------------------
# Script entry point
# --------------------------------------------------

if __name__ == "__main__":
    transform()