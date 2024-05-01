"""Runs the Flask based web application"""

import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, send_from_directory
from sqlalchemy import create_engine, select

from ..utils.tables import faces as faces_table
from ..utils.tables import files as files_table
from ..utils.tables import persons as persons_table

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
        query_faces = select(
            faces_table.c.id,
            faces_table.c.thumbnail_filename,
            faces_table.c.person_id,
            faces_table.c.file_id,
        )
        result_faces = conn.execute(query_faces)
        data_faces = [
            {
                "thumbnail_path": "/thumbnail/" + row.thumbnail_filename,
                "id": row.id,
                "person_id": row.person_id,
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


@app.route("/thumbnail/<path:filename>")
def thumbnail(filename):
    """
    Serve a thumbnail from the thumbnail folder
    """
    return send_from_directory(
        os.path.join("../../", os.environ["THUMBNAILS_PATH"]), filename
    )


@app.route("/file/<int:id>")
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
    return render_template("base.html")


@app.route("/person", methods=["POST"])
def add_person():
    """
    Add a new person to the database
    """
    name = request.form.get("name")
    if name:
        db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
        with db_engine.connect() as conn:
            # Insert new person into the database
            insert_person = persons_table.insert().values(name=name)
            conn.execute(insert_person)
            conn.close()
        return "Person created", 201
    else:
        return "Invalid request, missing 'name' field", 400
