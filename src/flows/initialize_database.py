from prefect import flow, task
from sqlalchemy import create_engine, Engine, MetaData, Table, Column, Integer, String, DateTime, ForeignKey
from dotenv import load_dotenv
import os
import sys

load_dotenv()  # Inject environment variables from .env during development

@task()
def create_tables(db_engine: Engine) -> None:
    """
    Create all tables for the local SQLite database that are defined centrally
    """
    from ..utils.tables import meta
    
    meta.create_all(db_engine)
        
@flow()
def initialize_database():
    db_engine = create_engine('sqlite:///' + os.environ["DATABASE_PATH"])
    create_tables(db_engine)
    
if __name__ == "__main__":
    initialize_database()

