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

@flow(log_prints=True)
def parse_modified_files():
    """
    Find, parse and inject all modified files paths of all new or modified files within the library
    """
    filepaths = list_all_supported_filepaths(os.environ["LIBRARY_PATH"], SUPPORTED_FILE_EXTENSIONS)
    
    with SqlAlchemyConnector.load("Database") as connector:
        connector.execute(
            "CREATE TABLE IF NOT EXISTS files (path varchar, hash varchar);"
        )
    
    for filepath in filepaths:
        hash = calculate_file_hash(filepath)
        print(os.path.getmtime(filepath))
        print(filepath)

if __name__ == "__main__":
    parse_modified_files()