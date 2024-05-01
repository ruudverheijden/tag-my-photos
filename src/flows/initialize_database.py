"""Flow to initialize the local SQLite database and Faiss embeddings index"""

import os

import faiss
from dotenv import load_dotenv
from prefect import flow
from sqlalchemy import Engine, create_engine, insert

from ..utils.tables import meta
from ..utils.tables import persons as persons_table

load_dotenv()  # Inject environment variables from .env during development

EMBEDDING_DIMENSION = 128  # = Facenet embedding size


def create_tables(db_engine: Engine) -> None:
    """
    Create all tables for the local SQLite database that are defined centrally
    """
    meta.create_all(db_engine)


def create_embeddings_index(dimension: int) -> None:
    """
    Create a vector embeddings index based on Faiss and store it to disk
    """
    # Create a new index
    index = faiss.IndexFlatL2(dimension)
    index_with_ids = faiss.IndexIDMap(index)
    faiss.write_index(index_with_ids, os.environ["EMBEDDINGS_INDEX_PATH"])


def insert_initial_data(db_engine: Engine) -> None:
    """
    Insert initial data into the database
    """
    with db_engine.connect() as conn:
        # Insert 'Ignored' person which will be linked to all faces
        # we don't want to link to a specific person
        query = insert(persons_table).values(id=0, name="Ignored")
        conn.execute(query)
        conn.close()


@flow()
def initialize_database():
    """
    Flow to initialize the local SQLite database, Faiss embeddings index and insert initial data
    """
    # Create SQLite database
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    create_tables(db_engine)

    # Create Faiss embeddings index
    create_embeddings_index(EMBEDDING_DIMENSION)

    # Insert initial data
    insert_initial_data(db_engine)


if __name__ == "__main__":
    initialize_database()
