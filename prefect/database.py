from prefect import flow, task
from prefect_sqlalchemy import SqlAlchemyConnector, ConnectionComponents, SyncDriver
from dotenv import load_dotenv
import os

load_dotenv()  # Inject environment variables from .env during development

DATABASE_PATH = os.path.join(os.environ["LIBRARY_PATH"], "tag-my-photos.db")
PREFECT_DATABASE_BLOCK_NAME = "Database"

@task()
def store_database_connector(block_name: str) -> None:
    """
    Store database connector to a Prefect Block
    """
    connector = SqlAlchemyConnector(
        connection_info=ConnectionComponents(
            driver=SyncDriver.SQLITE_PYSQLITE,
            database=DATABASE_PATH
        )
    )
    
    connector.save(block_name)

@task()
def create_tables(block_name: str) -> None:
    """
    Create all tables for the database if they don't exist yet
    """
    with SqlAlchemyConnector.load(block_name) as connector:
        connector.execute(
            "CREATE TABLE IF NOT EXISTS files (path varchar, hash varchar);"
        )
        
@flow()
def initialize_database():
    store_database_connector(PREFECT_DATABASE_BLOCK_NAME)
    create_tables(PREFECT_DATABASE_BLOCK_NAME)