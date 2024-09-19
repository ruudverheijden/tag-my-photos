"""Write person tags back to the original source files in the photo library"""

import os

from dotenv import load_dotenv
from prefect import flow, task
from sqlalchemy import create_engine, select, outerjoin
from exiftool import ExifToolHelper

from src.utils.tables import files as files_table, persons as persons_table, faces as faces_table

load_dotenv()  # Inject environment variables from .env during development


@flow()
def write_tags():
    """
    Find tagged persons in the database and write them as XMP tags to the original source files
    """
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    
    with db_engine.connect() as conn:
        query = select(
            files_table.c.path,
            persons_table.c.name
        ).select_from(
            outerjoin(
                outerjoin(files_table, faces_table, files_table.c.id == faces_table.c.file_id),
                persons_table, faces_table.c.person_id == persons_table.c.id
            )
        ).where(faces_table.c.person_id.isnot(None))
        
        results = conn.execute(query)

        for result in results:
            print(result)


if __name__ == "__main__":
    write_tags()
