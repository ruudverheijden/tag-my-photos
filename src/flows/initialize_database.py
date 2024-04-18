from prefect import flow, task
from sqlalchemy import create_engine, Engine, MetaData, Table, Column, Integer, String, DateTime, ForeignKey
from dotenv import load_dotenv
import os
import faiss

load_dotenv()  # Inject environment variables from .env during development

EMBEDDING_DIMENSION = 128 # = Facenet embedding size

@task()
def create_tables(db_engine: Engine) -> None:
    """
    Create all tables for the local SQLite database that are defined centrally
    """
    from ..utils.tables import meta
    
    meta.create_all(db_engine)
    

@task()
def create_embeddings_index(dimension: int) -> None:
    """
    Create a vector embeddings index based on Faiss and store it to disk
    """
    # Create a new index
    index = faiss.IndexFlatL2(dimension)
    indexWithIds = faiss.IndexIDMap(index)
    faiss.write_index(indexWithIds, os.environ["EMBEDDINGS_INDEX_PATH"])
    
        
@flow()
def initialize_database():
    # Create SQLite database
    db_engine = create_engine('sqlite:///' + os.environ["DATABASE_PATH"])
    create_tables(db_engine)
    
    # Create Faiss embeddings index
    create_embeddings_index(EMBEDDING_DIMENSION)
    
if __name__ == "__main__":
    initialize_database()

