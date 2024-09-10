"""Runs the Flask based web application"""

import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, send_from_directory
from sqlalchemy import create_engine, select, outerjoin

from ..utils.tables import faces as faces_table
from ..utils.tables import files as files_table
from ..utils.tables import persons as persons_table
from ..utils.tables import clusters as clusters_table

load_dotenv()  # Inject environment variables from .env during development

app = Flask(__name__)


@app.route("/")
def index():
    """
    Overview page
    """
    return render_template("base.html")


@app.route("/faces")
def faces():
    """
    Show an overview of all faces in the database
    """
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    with db_engine.connect() as conn:
        # Fetch all faces
        # TODO: add pagination
        query_faces = (
            select(
                faces_table.c.id,
                faces_table.c.thumbnail_filename,
                faces_table.c.person_id,
                faces_table.c.person_id_suggested,
                faces_table.c.file_id,
            )
            .where(faces_table.c.person_id.is_(None)).order_by(faces_table.c.person_id_suggested.desc())
        )
        result_faces = conn.execute(query_faces)
        
        data_faces = [
            {
                "thumbnail_path": "/thumbnail/" + row.thumbnail_filename if row.thumbnail_filename else None,
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

@app.route("/clusters")
def clusters():
    """
    Show an overview of all clusters in the database
    """
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    with db_engine.connect() as conn:
        # Fetch all clusters
        # TODO: add pagination
        query_clusters = (
            select(
                clusters_table.c.id,
                clusters_table.c.cluster_id,
                clusters_table.c.face_id,
                faces_table.c.file_id,
                faces_table.c.thumbnail_filename
            ).join(
                faces_table, clusters_table.c.face_id == faces_table.c.id
            ).order_by(clusters_table.c.cluster_id)
        )
        result_clusters = conn.execute(query_clusters)
        
        data_clusters = [
            {
                "id": row.id,
                "cluster_id": row.cluster_id,
                "face_id": row.face_id,
                "file_id": row.file_id,
                "thumbnail_path": "/thumbnail/" + row.thumbnail_filename
            }
            for row in result_clusters
        ]
        print(data_clusters)
        conn.close()
    return render_template(
        "clusters_overview.html", clusters=data_clusters
    )

@app.route("/thumbnail/<path:filename>")
def thumbnail(filename):
    """
    Serve a thumbnail from the thumbnail folder
    """
    return send_from_directory(
        os.path.join("../../", os.environ["THUMBNAILS_PATH"]), filename
    )


@app.route("/file/<int:file_id>")
def file(file_id):
    """
    Show the photo from the files table based on the id
    """
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    with db_engine.connect() as conn:
        query = select(files_table.c.thumbnail_filename).where(
            files_table.c.id == file_id
        )
        result = conn.execute(query)
        row = result.fetchone()
        conn.close()

    if row is None:
        return "File not found", 404
    else:
        return render_template(
            "file.html", file_path="/thumbnail/" + row.thumbnail_filename
        )


@app.route("/persons")
def persons():
    """
    Persons overview page
    """
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    with db_engine.connect() as conn:
        # Select 1 face per person
        first_faces = select(
            faces_table.c.person_id,
            faces_table.c.thumbnail_filename
        ).where(faces_table.c.person_id.isnot(None)
        ).group_by(faces_table.c.person_id
        ).distinct(
        ).subquery()

        # Join persons_table with the first_faces subquery and exclude 'Ignored' which has ID 0
        query_persons = select(
            persons_table.c.id,
            persons_table.c.name,
            first_faces.c.thumbnail_filename
        ).select_from(
            outerjoin(persons_table, first_faces, persons_table.c.id == first_faces.c.person_id)
        ).where(persons_table.c.id > 0)

        result_persons = conn.execute(query_persons)
        data_persons = [{"id": row.id, "name": row.name, "thumbnail_path": "/thumbnail/" + row.thumbnail_filename} for row in result_persons]
        conn.close()
        
    return render_template("persons_overview.html", persons=data_persons)


@app.route("/person", methods=["POST"])
def add_person():
    """
    Add a new person to the database if it does not exist yet
    """
    data = request.json

    if not request.is_json:
        return "Invalid request, must be JSON", 415

    if data["name"]:
        db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
        with db_engine.connect() as conn:
            # Check if the person already exists
            query_person = select(persons_table).where(
                persons_table.c.name.collate("NOCASE") == data["name"].lower()
            )
            if conn.execute(query_person).fetchone():
                conn.close()
                return "Person already exists", 409

            # Otherwise, insert new person into the database
            insert_person = persons_table.insert().values(name=data["name"])
            result = conn.execute(insert_person)
            conn.commit()
            conn.close()

            if result.is_insert:
                return {"id": result.inserted_primary_key[0]}, 201

            return "Failed to insert person", 500

    return "Invalid request, missing 'name' field", 400


@app.route("/face/<int:face_id>", methods=["POST"])
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
