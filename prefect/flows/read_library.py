from prefect import flow, task
from prefect_sqlalchemy import SqlAlchemyConnector
from dotenv import load_dotenv
import os
import hashlib

load_dotenv()  # Inject environment variables from .env during development

SUPPORTED_FILE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.heic']

@task()
def list_all_supported_filepaths(library_path: str, supported_extensions: list[str]) -> list[str]:
    """
    List all files of a supported extension by walking
    through all subdirectories in the library path and
    return their full path
    """
    paths = []
    # Walk through all files in all subdirectories
    for root, dirs, files in os.walk(library_path):
        # Exclude hidden files and directories
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']
        
        for file in files:
            path = os.path.join(root, file)
            
            # Only add files with supported file extensions
            if os.path.splitext(file)[1].lower() in supported_extensions:
                paths.append(path)
    return paths

@task()
def calculate_file_hash(filepath: str) -> str:
    """
    Calculate the SHA-256 hash of a file
    """
    with open(filepath, 'rb') as file:
        file_hash = hashlib.sha256(file.read()).hexdigest()
    return file_hash

@task()
def store_metadata(filepath: str, hash: str, last_updated: float) -> str:
    """
    Store the file metadata in the database
    """
    with SqlAlchemyConnector.load("database") as connector:
        connector.execute(
            "INSERT INTO files (path, hash, last_updated) VALUES (:path, :hash, :last_updated);",
            parameters={"path": filepath, "hash": hash, "last_updated": last_updated},
        )

@flow(log_prints=True)
def parse_modified_files():
    """
    Find, parse and inject all modified files paths of all new or modified files within the library
    """
    filepaths = list_all_supported_filepaths(os.environ["LIBRARY_PATH"], SUPPORTED_FILE_EXTENSIONS)
    
    for filepath in filepaths:
        store_metadata(filepath, calculate_file_hash(filepath), os.path.getmtime(filepath))
            
    with SqlAlchemyConnector.load("database") as connector:
        while True:
            # Repeated fetch* calls using the same operation will
            # skip re-executing and instead return the next set of results
            new_rows = connector.fetch_many("SELECT * FROM files")
            if len(new_rows) == 0:
                break
            print(new_rows)

if __name__ == "__main__":
    parse_modified_files()