"""Flow to generate face embeddings for all new or modified files within the database"""

import os

import faiss
import numpy as np
from deepface import DeepFace
from dotenv import load_dotenv
from prefect import flow, task
from sqlalchemy import create_engine, insert, select, update

from ..utils.tables import faces as faces_table
from ..utils.tables import files as files_table

load_dotenv()  # Inject environment variables from .env during development

FACE_RECOGNITION_MODEL = "Facenet"  # See Deepface documentation for all options
FACE_DETECTION_MODEL = "retinaface"  # See Deepface documentation for all options


@task()
def generate_embeddings_from_file(
    filepath: str, face_recognition_model: str, face_detection_model: str
):
    """
    Generate embeddings of a file using the Deepface library
    """
    return DeepFace.represent(
        img_path=filepath,
        enforce_detection=False,
        model_name=face_recognition_model,
        detector_backend=face_detection_model,
    )


@flow()
def generate_embeddings():
    """
    Generate face embeddings for all new or modified files within the database
    """
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    index = faiss.read_index(os.environ["EMBEDDINGS_INDEX_PATH"])

    with db_engine.connect() as conn:
        statement = select(files_table).where(files_table.c.contains_face is None)
        for row in conn.execute(statement):
            faces = generate_embeddings_from_file(
                row.path, FACE_RECOGNITION_MODEL, FACE_DETECTION_MODEL
            )

            face_found = len(faces) > 0

            # Update that we found at least one face in the file
            update_file_statement = (
                update(files_table)
                .where(files_table.c.id == row.id)
                .values(contains_face=True)
            )
            conn.execute(update_file_statement)
            conn.commit()

            if face_found:
                for face in faces:
                    # Store face metadata in the SQL database
                    insert_face_statement = insert(faces_table).values(
                        file_id=row.id,
                        confidence=face["face_confidence"],
                        embedding=np.array([face["embedding"]])
                        .astype(np.float32)
                        .tobytes(),
                        facial_area_left=face["facial_area"]["x"],
                        facial_area_top=face["facial_area"]["y"],
                        facial_area_width=face["facial_area"]["w"],
                        facial_area_height=face["facial_area"]["h"],
                    )
                    result = conn.execute(insert_face_statement)
                    conn.commit()

                    # Store face embedding in Faiss
                    embedding = np.array([face["embedding"]]).astype(np.float32)
                    index.add_with_ids(embedding, [result.inserted_primary_key[0]])

    # Store index to disk
    faiss.write_index(index, os.environ["EMBEDDINGS_INDEX_PATH"])


if __name__ == "__main__":
    generate_embeddings()
