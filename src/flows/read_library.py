from prefect import flow, task
from sqlalchemy import create_engine, Engine, insert
from dotenv import load_dotenv
from datetime import datetime
import os
import hashlib
from ..utils.tables import files as files_table

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
    Calculate the SHA-256 hash of a file block by block to support large files
    """
    BLOCK_SIZE = 65536 # The size of each read from the file
    
    file_hash = hashlib.sha256() # Create the hash object
    with open(filepath, 'rb') as f:
        fb = f.read(BLOCK_SIZE)
        while len(fb) > 0:
            file_hash.update(fb) # Update the hash
            fb = f.read(BLOCK_SIZE) # Read the next block from the file
    
    return file_hash.hexdigest() # Return the hexadecimal digest of the hash

@task()
def store_metadata(db_engine: Engine, filepath: str, hash: str, last_updated: float) -> str:
    """
    Store the file metadata in the database
    """
    with db_engine.connect() as conn:
        result = conn.execute(
            insert(files_table).values(path=filepath, hash=hash, last_updated=last_updated)
            )
        conn.commit()

@flow(log_prints=True)
def parse_modified_files():
    """
    Find, parse and inject all modified files paths of all new or modified files within the library
    """
    filepaths = list_all_supported_filepaths(os.environ["LIBRARY_PATH"], SUPPORTED_FILE_EXTENSIONS)
    
    db_engine = create_engine('sqlite:///' + os.environ["DATABASE_PATH"], echo=True)
    
    for filepath in filepaths:
        store_metadata(db_engine, filepath, calculate_file_hash(filepath), datetime.fromtimestamp(os.path.getmtime(filepath)))

if __name__ == "__main__":
    parse_modified_files()