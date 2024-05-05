"""Recognize unknown faces based on the embeddings in the Faiss index"""

import os
from collections import Counter

import faiss
import numpy as np
from dotenv import load_dotenv
from prefect import flow
from sqlalchemy import create_engine, select

from ..utils.tables import faces as faces_table

load_dotenv()  # Inject environment variables from .env during development

# Number of nearest neighbors to search for in the Faiss index
K_NEAREST_NEIGHBORS = 5
# Percentage of the minimum distance to consider faces as similar
SIMILAR_FACES_RELATIVE_TO_MIN_DISTANCE = 0.10
# Maximum number of similar faces to consider, higher numbers leads to more db queries
MAX_SIMILAR_FACES = 3


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
            embedding = np.frombuffer(row.embedding, dtype=np.float32)

            # Search for the nearest neighbor in the Faiss index
            distances, indices = index.search(
                np.array([embedding]), K_NEAREST_NEIGHBORS
            )

            # Remove indices with distance 0, which is the face itself
            distance_zero = np.where(distances == 0)
            indices = np.delete(indices, distance_zero)
            distances = np.delete(distances, distance_zero)

            # Remove indices that have a distance that's more that xx% higher than the
            # minimum distance as they are probably not relevant
            distance_threshold = np.where(
                distances > distances[0] * (1 + SIMILAR_FACES_RELATIVE_TO_MIN_DISTANCE)
            )
            indices = np.delete(indices, distance_threshold)
            distances = np.delete(distances, distance_threshold)

            # Limit the number of similar faces to consider
            indices = indices[:MAX_SIMILAR_FACES]
            distances = distances[:MAX_SIMILAR_FACES]

            print(f"Nearest Neighbours of {row.id} are {indices} with distances {distances}")

            # Get person_id for all close faces
            statement_face = select(faces_table.c.person_id).where(
                faces_table.c.id.in_(indices.tolist())
            )

            found_persons = []

            for row_face in conn.execute(statement_face):
                found_persons.append(row_face.person_id)

            # Count the duplicate values in found_persons
            duplicate_counts = Counter(found_persons)

            # Sort the duplicate counts in descending order
            sorted_counts = sorted(
                duplicate_counts.items(), key=lambda x: x[1], reverse=True
            )

            # Best matching person is the one with the highest count
            best_match_id, best_match_count = sorted_counts[0]

            # Only suggest when at least half of the found matches are the same person
            if (
                best_match_count >= int(len(found_persons) / 2)
                and best_match_id is not None
            ):
                print(
                    f"Best matching person: {best_match_id} with {best_match_count} close faces"
                )
                # Update the face with the best matching person
                update_statement = (
                    faces_table.update()
                    .where(faces_table.c.id == row.id)
                    .values(person_id_suggested=best_match_id)
                )
                conn.execute(update_statement)
                conn.commit()


if __name__ == "__main__":
    recognize_unknown_faces()
