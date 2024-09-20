"""Write person tags back to the original source files in the photo library"""

import os

from dotenv import load_dotenv
from prefect import flow, task
from sqlalchemy import create_engine, select, outerjoin
from exiftool import ExifToolHelper
from collections import defaultdict

from src.utils.tables import files as files_table, persons as persons_table, faces as faces_table

load_dotenv()  # Inject environment variables from .env during development


@flow()
def write_tags():
    """
    Find tagged persons in the database and write them in the XMP Subject to the original source files
    """
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    
    with db_engine.connect() as conn:
        # Find all files with confirmed tagged persons
        query = select(
            files_table.c.path,
            persons_table.c.name
        ).select_from(
            outerjoin(
            outerjoin(files_table, faces_table, files_table.c.id == faces_table.c.file_id),
            persons_table, faces_table.c.person_id == persons_table.c.id
            )
        ).where(faces_table.c.person_id.isnot(None), faces_table.c.person_id != 0)
        
        results = conn.execute(query)

        # Group names by file path
        tags_by_file = defaultdict(list)
        for result in results:
            file_path, person_name = result
            tags_by_file[file_path].append(person_name)

        # Write tags to files
        with ExifToolHelper() as et:
            for file_path, names in tags_by_file.items():
                et.set_tags(
                    [file_path],
                    tags={"Subject": names}
                )
                print(f"Writting to {file_path} XMP Subject Tag = {', '.join(names)}")


if __name__ == "__main__":
    write_tags()
