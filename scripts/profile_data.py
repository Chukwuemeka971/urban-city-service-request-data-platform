import polars as pl
from pathlib import Path

from src.utils.logger import get_logger


# --------------------------------------------------
# Project paths
# --------------------------------------------------

location = Path(__file__).resolve().parent
project_root = location.parent

LOCAL_FILE_PATH = (
    project_root
    / "data"
    / "urban_service_requests.csv"
)


# --------------------------------------------------
# Logger
# --------------------------------------------------

logger = get_logger(__name__)


# --------------------------------------------------
# Data profiling
# --------------------------------------------------

def profile_data():

    logger.info("Starting data profiling")

    # --------------------------------------------------
    # Validate source file
    # --------------------------------------------------

    if not LOCAL_FILE_PATH.exists():
        raise FileNotFoundError(
            f"File not found: {LOCAL_FILE_PATH}"
        )

    # --------------------------------------------------
    # Read dataset
    # --------------------------------------------------

    df = pl.read_csv(LOCAL_FILE_PATH)

    logger.info(
        "Dataset loaded successfully"
    )

    # --------------------------------------------------
    # Basic dataset information
    # --------------------------------------------------

    logger.info(
        "Rows: %s",
        df.height
    )

    logger.info(
        "Columns: %s",
        df.width
    )

    # --------------------------------------------------
    # Column names
    # --------------------------------------------------

    logger.info("Column names:")

    for column in df.columns:
        logger.info("  - %s", column)

    # --------------------------------------------------
    # Schema
    # --------------------------------------------------

    logger.info("Dataset schema:")

    logger.info(
        "%s",
        df.schema
    )

    # --------------------------------------------------
    # Missing values
    # --------------------------------------------------

    logger.info("Missing values by column:")

    missing_values = (
        df.null_count()
        .transpose(
            include_header=True,
            header_name="column",
            column_names=["null_count"]
        )
        .sort(
            "null_count",
            descending=True
        )
    )

    logger.info(
        "\n%s",
        missing_values
    )

        # --------------------------------------------------
    # Completely null columns
    # --------------------------------------------------

    completely_null_columns = [
        column
        for column in df.columns
        if df[column].null_count() == df.height
    ]

    logger.info(
        "Completely null columns (%s):",
        len(completely_null_columns)
    )

    for column in completely_null_columns:
        logger.info(
            "  - %s",
            column
        )

    # --------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------

    duplicate_rows = (
        df.height
        - df.unique().height
    )

    logger.info(
        "Duplicate full rows: %s",
        duplicate_rows
    )

    # --------------------------------------------------
    # Duplicate Unique Keys
    # --------------------------------------------------

    if "Unique Key" in df.columns:

        duplicate_keys = (
            df
            .group_by("Unique Key")
            .agg(
                pl.len().alias("count")
            )
            .filter(
                pl.col("count") > 1
            )
        )

        logger.info(
            "Duplicate Unique Keys: %s",
            duplicate_keys.height
        )

    # --------------------------------------------------
    # Status analysis
    # --------------------------------------------------

    if "Status" in df.columns:

        status_counts = (
            df
            .group_by("Status")
            .agg(
                pl.len().alias("record_count")
            )
            .sort(
                "record_count",
                descending=True
            )
        )

        logger.info(
            "Status distribution:\n%s",
            status_counts
        )

    # --------------------------------------------------
    # Status vs Closed Date
    # --------------------------------------------------

    if {
        "Status",
        "Closed Date"
    }.issubset(df.columns):

        status_closed_date = (
            df
            .group_by("Status")
            .agg([
                pl.len().alias("total_records"),

                pl.col("Closed Date")
                .is_null()
                .sum()
                .alias("closed_date_nulls"),

                pl.col("Closed Date")
                .is_not_null()
                .sum()
                .alias("closed_date_present")
            ])
            .sort(
                "total_records",
                descending=True
            )
        )

        logger.info(
            "Status vs Closed Date:\n%s",
            status_closed_date
        )

    # --------------------------------------------------
    # Geographic validation
    # --------------------------------------------------

    if {
        "Latitude",
        "Longitude"
    }.issubset(df.columns):

        invalid_coordinates = (
            df
            .filter(
                (
                    pl.col("Latitude").is_not_null()
                    & (
                        (pl.col("Latitude") < -90)
                        | (pl.col("Latitude") > 90)
                    )
                )
                |
                (
                    pl.col("Longitude").is_not_null()
                    & (
                        (pl.col("Longitude") < -180)
                        | (pl.col("Longitude") > 180)
                    )
                )
            )
        )

        logger.info(
            "Invalid geographic coordinates: %s",
            invalid_coordinates.height
        )

    # --------------------------------------------------
    # Important categorical columns
    # --------------------------------------------------

    categorical_columns = [
        "Agency",
        "Status",
        "Borough",
        "City",
        "Problem (formerly Complaint Type)",
        "Location Type",
        "Open Data Channel Type",
    ]

    for column in categorical_columns:

        if column in df.columns:

            unique_count = (
                df
                .select(
                    pl.col(column)
                    .n_unique()
                    .alias("unique_values")
                )
                .item()
            )

            logger.info(
                "%s - unique values: %s",
                column,
                unique_count
            )

    # --------------------------------------------------
    # Sample records
    # --------------------------------------------------

    logger.info(
        "First 5 records:\n%s",
        df.head(5)
    )

    # --------------------------------------------------
    # Profiling complete
    # --------------------------------------------------

    logger.info(
        "Data profiling completed successfully"
    )


# --------------------------------------------------
# Script entry point
# --------------------------------------------------

if __name__ == "__main__":
    profile_data()