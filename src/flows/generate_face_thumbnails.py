from prefect import flow, task
from sqlalchemy import create_engine, select
from dotenv import load_dotenv
from PIL import Image
import os
from ..utils.tables import files as files_table, faces as faces_table

load_dotenv()  # Inject environment variables from .env during development

MAX_FACE_THUMBNAIL_SIZE = (500, 500)

@task()
def generate_thumbnail(thumbnail_dir: str, file_path: str, file_postfix: str, face_left: int, face_top: int, face_width: int, face_height: int) -> str:
    """
    Create a thumbnail of the face area of an image    
    """
    # Open image in RGB mode
    with Image.open(file_path) as image:
         
        # Crop image to face with maximum dimensions
        cropped_image = image.crop((face_left, face_top, face_left + face_width, face_top + face_height))
        cropped_image.thumbnail(MAX_FACE_THUMBNAIL_SIZE)

        file_name = os.path.basename(file_path)
        filename_base, file_extension = os.path.splitext(file_name.lower())
        thumbnail_filename = filename_base + str(file_postfix) + file_extension
        target_path = os.path.join(thumbnail_dir, thumbnail_filename)

        cropped_image.save(target_path)

        return thumbnail_filename

def create_thumbnails_folder_if_needed(path: str):
    """
    Create the thumbnails folder if it does not exist yet
    """
    if not os.path.exists(path):
        os.makedirs(path)

@flow()
def generate_face_thumbnails():
    """
    Generate thumbnails for all faces in the database that do not have a thumbnail yet
    """
    create_thumbnails_folder_if_needed(os.environ["THUMBNAILS_PATH"])
    
    db_engine = create_engine('sqlite:///' + os.environ["DATABASE_PATH"])
    
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
                row.facial_area_left,
                row.facial_area_top,
                row.facial_area_width,
                row.facial_area_height
            )
            
            update_statement = faces_table.update().where(faces_table.c.id == row.face_id).values(thumbnail_filename=thumbnail_filename)
            conn.execute(update_statement)
            conn.commit()

if __name__ == "__main__":
    generate_face_thumbnails()