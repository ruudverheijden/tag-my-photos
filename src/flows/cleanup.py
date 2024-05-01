"""Flow to cleanup all generated files to start from scratch"""

import os
import shutil

from dotenv import load_dotenv
from prefect import flow

load_dotenv()  # Inject environment variables from .env during development


@flow()
def cleanup():
    """
    Remove all generated files
    """
    if os.path.exists(os.environ["DATABASE_PATH"]):
        os.remove(os.environ["DATABASE_PATH"])

    if os.path.exists(os.environ["EMBEDDINGS_INDEX_PATH"]):
        os.remove(os.environ["EMBEDDINGS_INDEX_PATH"])

    if os.path.exists(os.environ["THUMBNAILS_PATH"]):
        shutil.rmtree(os.environ["THUMBNAILS_PATH"])


if __name__ == "__main__":
    cleanup()
