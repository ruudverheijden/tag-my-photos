from prefect import flow
from . import generate_thumbnails, initialize_database, parse_modified_files, generate_embeddings

@flow(log_prints=True)
def run_pipeline():
    """
    Run the file pipeline
    """
    initialize_database.initialize_database()
    parse_modified_files.parse_modified_files()
    generate_embeddings.generate_embeddings()
    generate_thumbnails.generate_thumbnails()

if __name__ == "__main__":
    run_pipeline()
    