from prefect import flow, task
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env during development

SUPPORTED_FILE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.heic']

@task()
def list_all_supported_filepaths() -> list[str]:
    """
    List all files with a supported extension by walking
    through all subdirectories in the library path and
    return their path and last modified timestamp
    """
    paths = []
    # Walk through all files in all subdirectories
    for root, dirs, files in os.walk(os.environ["LIBRARY_PATH"]):
        # Exclude hidden files and directories
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']
        
        for file in files:
            path = os.path.join(root, file)
            
            # Only add files with supported file extensions
            if os.path.splitext(file)[1].lower() in SUPPORTED_FILE_EXTENSIONS:
                paths.append(path)
    return files


@flow(log_prints=True)
def find_modified_files():
    """
    Find paths of all new or modified files within the library
    """
    filepaths = list_all_supported_filepaths()
    
    for filepath in filepaths:
        print(os.path.getmtime(filepath))
        print(filepath)

if __name__ == "__main__":
    find_modified_files()