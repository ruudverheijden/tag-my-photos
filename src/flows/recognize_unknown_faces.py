"""Recognize unknown faces based on the embeddings in the Faiss index"""

import os
import uuid
from collections import Counter

import faiss
import numpy as np
from dotenv import load_dotenv
from prefect import flow
from sqlalchemy import create_engine, select

from ..utils.tables import faces as faces_table, clusters as clusters_table

load_dotenv()  # Inject environment variables from .env during development

# Number of nearest neighbors to search for in the Faiss index
K_NEAREST_NEIGHBORS = 5
# Percentage of the minimum distance to consider faces as similar
SIMILAR_FACES_RELATIVE_TO_MIN_DISTANCE = 0.10
# Maximum number of similar faces to consider, higher numbers leads to more db queries
MAX_SIMILAR_FACES = 3
# Threshold of the maximum distance value for clustering unknown faces together as being the likely the same person, a higher value will result is more false positives, while a lower value clusters less unknown faces
ASSUME_SAME_PERSON_THRESHOLD = 10


def find_nearest_neighbors(
    embedding: list[float], index: faiss.Index
) -> tuple[list[float], list[int]]:
    """
    Find the k nearest neighbors of the given embedding in the Faiss index
    """
    # Search for the nearest neighbor in the Faiss index
    distances, indices = index.search(np.array([embedding]), K_NEAREST_NEIGHBORS)

    # Remove indices with distance 0, which is the searched face itself
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

    return distances, indices


def find_best_matching_known_person(ids: list, conn) -> int | None:
    """
    Find the best matching known person in the db
    Matching a person that's already confirmed is the best guess we can make
    """
    # Get person_id for all close faces
    statement = select(faces_table.c.person_id).where(
        faces_table.c.id.in_(ids.tolist())
    )

    found_persons = []

    for row_face in conn.execute(statement):
        found_persons.append(row_face.person_id)

    # Count the duplicate values
    duplicate_counts = Counter(found_persons)

    # Sort the duplicate counts in descending order
    sorted_counts = sorted(duplicate_counts.items(), key=lambda x: x[1], reverse=True)

    # Best matching person is the one with the highest count
    best_match_id, best_match_count = sorted_counts[0]

    # Only suggest when at least half of the found matches are the same person
    if best_match_count >= int(len(found_persons) / 2) and best_match_id is not None:
        return best_match_id

    return None


def cluster_unknown_persons(
    face_id: int, indices: list[int], distances: list[float], conn
):
    """
    If we find a face to match closely with some other unknown faces, we assume it's the same person
    and therefor cluster it together with other unknown faces.
    """
    irrelevant_neighbors = np.where(distances > ASSUME_SAME_PERSON_THRESHOLD)
    indices = np.delete(indices, irrelevant_neighbors)
    similar_faces = [face_id] + indices.tolist()

    if len(indices) <= 0:
        return

    print(
        f"Try to cluster unknown person {face_id} and it's probably same face neighbors: {indices}"
    )

    # Look for the face itself or it's close neighbors in the clusters table
    statement_face = select(clusters_table.c.cluster_id).where(
        clusters_table.c.face_id.in_(similar_faces)
    )

    cluster = conn.execute(statement_face).fetchone()

    cluster_id = None

    # Create a new cluster if neither the face_id nor it's close neighbors are in any existing cluster yet
    if cluster and cluster.cluster_id:
        cluster_id = cluster.cluster_id
    else:
        cluster_id = uuid.uuid4()

    values = []
    for face in similar_faces:
        values.append({"face_id": face, "cluster_id": cluster_id})
    insert_statement = clusters_table.insert().values(values)
    conn.execute(insert_statement)
    conn.commit()


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

            distances, indices = find_nearest_neighbors(embedding, index)

            print(
                f"Nearest Neighbors of {row.id} are {indices} with distances {distances}"
            )

            best_match_id = find_best_matching_known_person(indices, conn)

            # Save the best matching person in the database
            if best_match_id is not None:
                print(f"Best matching person: {best_match_id}")

                # Update the face with the best matching person
                update_statement = (
                    faces_table.update()
                    .where(faces_table.c.id == row.id)
                    .values(person_id_suggested=best_match_id)
                )
                conn.execute(update_statement)
                conn.commit()
            else:
                # Try to cluster with other unknown persons
                cluster_unknown_persons(row.id, indices, distances, conn)


if __name__ == "__main__":
    recognize_unknown_faces()
