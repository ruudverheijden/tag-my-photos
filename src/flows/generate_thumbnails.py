from prefect import flow, task
from sqlalchemy import create_engine, select
from dotenv import load_dotenv
from PIL import Image
import os
from ..utils.tables import files as files_table, faces as faces_table

load_dotenv()  # Inject environment variables from .env during development

MAX_FACE_THUMBNAIL_SIZE = (500, 500)
MAX_FILE_THUMBNAIL_SIZE = (1000, 1000)

@task()
def generate_thumbnail(thumbnail_dir: str, file_path: str, file_postfix: str, crop: list[int, int, int, int] = None) -> str:
    """
    Create a thumbnail of the face area of an image    
    """
    # Open image in RGB mode
    with Image.open(file_path) as image:
        
        # If a face crop is provided, crop the image to the face area
        if crop is not None:
            face_left, face_top, face_width, face_height = crop
            output_image = image.crop((face_left, face_top, face_left + face_width, face_top + face_height))
            output_image.thumbnail(MAX_FACE_THUMBNAIL_SIZE)
        # Otherwise we create a thumbnail of the whole image
        else:
            output_image = image.copy()
            output_image.thumbnail(MAX_FILE_THUMBNAIL_SIZE)

        file_name = os.path.basename(file_path)
        filename_base, file_extension = os.path.splitext(file_name.lower())
        thumbnail_filename = filename_base + str(file_postfix) + file_extension
        target_path = os.path.join(thumbnail_dir, thumbnail_filename)

        output_image.save(target_path)

        return thumbnail_filename


def create_thumbnails_folder_if_needed(path: str):
    """
    Create the thumbnails folder if it does not exist yet
    """
    if not os.path.exists(path):
        os.makedirs(path)


def generate_face_thumbnails(db_engine: create_engine):
    """
    Generate thumbnails for all faces in the database that do not have a thumbnail yet
    """
    with db_engine.connect() as conn:
        statement = select(
            files_table.c.id.label('file_id'),
            files_table.c.path,
            faces_table.c.id.label('face_id'),
            faces_table.c.facial_area_left,
            faces_table.c.facial_area_top,
            faces_table.c.facial_area_width,
            faces_table.c.facial_area_height
        ).select_from(files_table).join(faces_table).where(
            faces_table.c.thumbnail_filename.is_(None)
        )
        for row in conn.execute(statement):
            thumbnail_filename = generate_thumbnail(
                os.environ["THUMBNAILS_PATH"],
                row.path,
                f"-{row.file_id}-{row.face_id}",
                [row.facial_area_left, row.facial_area_top, row.facial_area_width, row.facial_area_height]
            )
            
            update_statement = faces_table.update().where(faces_table.c.id == row.face_id).values(thumbnail_filename=thumbnail_filename)
            conn.execute(update_statement)
            conn.commit()
            

def generate_file_thumbnails(db_engine: create_engine):
    """
    Generate thumbnails for all files in the database that do not have a thumbnail yet
    """
    
    with db_engine.connect() as conn:
        statement = select(
            files_table.c.id,
            files_table.c.path
        ).where(
            files_table.c.thumbnail_filename.is_(None)
        )
        for row in conn.execute(statement):
            thumbnail_filename = generate_thumbnail(
                os.environ["THUMBNAILS_PATH"],
                row.path,
                f"-{row.id}"
            )
            
            update_statement = files_table.update().where(files_table.c.id == row.id).values(thumbnail_filename=thumbnail_filename)
            conn.execute(update_statement)
            conn.commit()

@flow()
def generate_thumbnails():
    db_engine = create_engine('sqlite:///' + os.environ["DATABASE_PATH"])
    
    create_thumbnails_folder_if_needed(os.environ["THUMBNAILS_PATH"])
    generate_face_thumbnails(db_engine)
    generate_file_thumbnails(db_engine)

if __name__ == "__main__":
    generate_thumbnails()