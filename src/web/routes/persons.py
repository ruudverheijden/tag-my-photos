"""Defines all routes related to persons"""
import os

from flask import Blueprint, render_template, request
from sqlalchemy import create_engine, select, outerjoin
from src.utils.tables import faces as faces_table, persons as persons_table

blueprint = Blueprint('persons', __name__, url_prefix='/persons')

@blueprint.route("/")
def index():
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
        data_persons = [{
            "id": row.id,
            "name": row.name,
            "thumbnail_path": "/files/thumbnails/" + row.thumbnail_filename
        } for row in result_persons]
        conn.close()

    return render_template("persons_overview.html", persons=data_persons)

@blueprint.route("/<int:person_id>")
def get_person(person_id):
    """
    Person page with all photos of this person
    """
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    with db_engine.connect() as conn:
        query_faces = select(
            faces_table.c.id,
            faces_table.c.file_id,
            faces_table.c.thumbnail_filename,
            faces_table.c.facial_area_top,
            faces_table.c.facial_area_left,
            faces_table.c.facial_area_width,
            faces_table.c.facial_area_height,
        ).where(faces_table.c.person_id == person_id)
        
        query_persons = select(
            persons_table.c.name
        ).where(persons_table.c.id == person_id)

        result_faces = conn.execute(query_faces)
        result_persons = conn.execute(query_persons).fetchone()
        
        data_faces = [{
            "id": row.id,
            "file_id": row.file_id,
            "thumbnail_path": "/files/thumbnails/" + row.thumbnail_filename,
            "facial_area_top": row.facial_area_top,
            "facial_area_left": row.facial_area_left,
            "facial_area_width": row.facial_area_width,
            "facial_area_height": row.facial_area_height
        } for row in result_faces]
        conn.close()

    return render_template("person.html", name=result_persons.name, faces=data_faces)


@blueprint.route("/", methods=["POST"])
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
