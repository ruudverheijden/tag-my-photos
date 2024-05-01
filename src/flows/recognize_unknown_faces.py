"""Recognize unknown faces based on the embeddings in the Faiss index"""

import os

import faiss
import numpy as np
from dotenv import load_dotenv
from prefect import flow
from sqlalchemy import create_engine, select

from ..utils.tables import faces as faces_table

load_dotenv()  # Inject environment variables from .env during development


@flow()
def recognize_unknown_faces():
    """
    Recognize unknown faces based on the embeddings in the Faiss index
    """
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    index = faiss.read_index(os.environ["EMBEDDINGS_INDEX_PATH"])

    with db_engine.connect() as conn:
        statement = select(faces_table).where(faces_table.c.person_id.is_(None))
        for row in conn.execute(statement):
            # Load the face embedding from the database
            # embedding = faiss.vector_to_array(row.embedding).reshape(1, -1)
            embedding = np.frombuffer(row.embedding, dtype=np.float32)

            # Search for the nearest neighbor in the Faiss index
            distances, indices = index.search(np.array([embedding]), 5)
            print(row.id)
            print(distances, indices)

            # If the distance is below a certain threshold, we consider the face as recognized
            # if distances[0][0] < 0.5:
            #     # Update the face with the recognized person
            #     # update_face_statement = faces_table.update().where(faces_table.c.id == row.id).values(person_id=indices[0][0])
            #     # conn.execute(update_face_statement)
            #     # conn.commit()

            #     print(f"Recognized face {row.id} as person {indices[0][0]}")
            # else:
            #     print(f"Could not recognize face {row.id}")


if __name__ == "__main__":
    recognize_unknown_faces()
