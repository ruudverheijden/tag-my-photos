from prefect import flow, task
from dotenv import load_dotenv
import os

load_dotenv()  # Inject environment variables from .env during development
        
@flow()
def cleanup():
    """
    Remove all generated files and data
    """
    os.remove(os.environ["DATABASE_PATH"])
    os.remove(os.environ["EMBEDDINGS_INDEX_PATH"])
    
if __name__ == "__main__":
    cleanup()

