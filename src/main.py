from prefect import flow, task
from .flows import initialize_database, parse_modified_files

@flow(log_prints=True)
def run_pipeline():
    """
    Run the file pipeline
    """
    initialize_database.initialize_database()
    parse_modified_files.parse_modified_files()

if __name__ == "__main__":
    run_pipeline()
    