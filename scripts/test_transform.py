import polars as pl

from scripts.transform import (
    transform_data,
    validate_source_columns,
)


SOURCE_FILE = "data/urban_service_requests.csv"


def main():
    print("Loading Bronze data locally...")

    source_df = pl.read_csv(SOURCE_FILE)

    print(
        f"Bronze: {source_df.height} rows × "
        f"{source_df.width} columns"
    )

    # Validate source structure
    validate_source_columns(source_df)

    # Run the SAME transformation used by transform.py
    silver_df = transform_data(source_df)

    print("\n" + "=" * 60)
    print("SILVER PREVIEW")
    print("=" * 60)

    print(silver_df.head(10))

    print("\n" + "=" * 60)
    print("SILVER SCHEMA")
    print("=" * 60)

    print(silver_df.schema)

    print("\n" + "=" * 60)
    print("SILVER SHAPE")
    print("=" * 60)

    print(
        f"{silver_df.height} rows × "
        f"{silver_df.width} columns"
    )

    print("\n" + "=" * 60)
    print("SILVER NULL COUNTS")
    print("=" * 60)

    print(silver_df.null_count())

    print("\nTransformation preview completed.")


if __name__ == "__main__":
    main()