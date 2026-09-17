import os
from pathlib import Path

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

from src.utils.logger import get_logger


logger = get_logger(__name__)

# --------------------------------------------------
# Project paths
# --------------------------------------------------

location = Path(__file__).resolve().parent
project_root = location.parent


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

load_dotenv(project_root / ".env")

# --------------------------------------------------
# Azure configuration
# --------------------------------------------------

ACCOUNT_KEY = os.getenv("ACCOUNT_KEY")
ACCOUNT_NAME = "urbancitystorage"
CONTAINER_NAME = "bronze"


# --------------------------------------------------
# Local file configuration
# --------------------------------------------------

LOCAL_FILE_PATH = (
    project_root
    / "data"
    / "urban_service_requests.csv"
)

BLOB_NAME = "urban_service_requests.csv"


# --------------------------------------------------
# Upload function
# --------------------------------------------------

def upload_data():

    if not ACCOUNT_KEY:
        raise ValueError("ACCOUNT_KEY is not set in .env")

    if not LOCAL_FILE_PATH.exists():
        raise FileNotFoundError(
            f"File not found: {LOCAL_FILE_PATH}"
        )

    try:
        logger.info(
            "Starting upload of %s",
            LOCAL_FILE_PATH.name
        )

        blob_service_client = BlobServiceClient(
            account_url=(
                f"https://{ACCOUNT_NAME}.blob.core.windows.net"
            ),
            credential=ACCOUNT_KEY
        )

        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME,
            blob=BLOB_NAME
        )

        with open(LOCAL_FILE_PATH, "rb") as data:
            blob_client.upload_blob(
                data,
                overwrite=True
            )

        logger.info(
            "Successfully uploaded %s to container '%s'",
            BLOB_NAME,
            CONTAINER_NAME
        )

    except Exception:
        logger.exception(
            "Failed to upload %s",
            LOCAL_FILE_PATH.name
        )
        raise


# --------------------------------------------------
# Script entry point
# --------------------------------------------------

if __name__ == "__main__":
    upload_data()