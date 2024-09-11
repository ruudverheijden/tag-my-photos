"""Defines all routes related to faces"""
import os

from flask import Blueprint, render_template, request
from sqlalchemy import create_engine, select
from src.utils.tables import faces as faces_table, persons as persons_table

blueprint = Blueprint("faces", __name__, url_prefix='/faces')

@blueprint.route("/")
def index():
    """
    Show an overview of all faces in the database
    """
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    with db_engine.connect() as conn:
        # Fetch all faces without a person_id
        query_faces = (
            select(
                faces_table.c.id,
                faces_table.c.thumbnail_filename,
                faces_table.c.person_id,
                faces_table.c.person_id_suggested,
                faces_table.c.file_id,
            )
            .where(faces_table.c.person_id.is_(None))
            .order_by(faces_table.c.person_id_suggested.desc())
        )
        result_faces = conn.execute(query_faces)

        data_faces = [
            {
                "thumbnail_path": "/files/thumbnails/" + row.thumbnail_filename
                if row.thumbnail_filename
                else None,
                "id": row.id,
                "person_id": row.person_id,
                "person_id_suggested": row.person_id_suggested,
                "file_id": row.file_id,
            }
            for row in result_faces
        ]

        # Fetch all persons
        query_persons = select(persons_table.c.id, persons_table.c.name)
        result_persons = conn.execute(query_persons)
        data_persons = [{"id": row.id, "name": row.name} for row in result_persons]
        conn.close()
    return render_template(
        "faces_overview.html", faces=data_faces, persons=data_persons
    )


@blueprint.route("/<int:face_id>", methods=["POST"])
def update_face(face_id):
    """
    Update an existing face record with a new person_id
    """
    data = request.json

    if not request.is_json:
        return "Invalid request, must be JSON", 415

    if (
        data["person_id"]
        and isinstance(data["person_id"], int)
        and face_id
        and isinstance(face_id, int)
    ):
        db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
        with db_engine.connect() as conn:
            # Update the face record with the new person_id
            update = (
                faces_table.update()
                .where(faces_table.c.id == face_id)
                .values(person_id=data["person_id"])
            )
            result = conn.execute(update)
            conn.commit()
            conn.close()

            if result.rowcount > 0:
                return "Face record updated successfully", 200

            return "Failed to update face record", 500

    return "Invalid request, missing (int)'person_id' and/or (int)'face_id' fields", 400
