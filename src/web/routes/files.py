"""Defines all routes related to files"""
import os

from flask import Blueprint, render_template, send_from_directory
from sqlalchemy import create_engine, select, outerjoin
from src.utils.tables import files as files_table, faces as faces_table

blueprint = Blueprint("files", __name__, url_prefix='/files')

@blueprint.route("/<int:file_id>")
def get_file(file_id):
    """
    Show the photo from the files table based on the id
    """
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    with db_engine.connect() as conn:
        query_file = select(
            files_table.c.id,
            files_table.c.path,
            files_table.c.thumbnail_filename,
            files_table.c.last_updated,
            files_table.c.contains_face
        ).where(files_table.c.id == file_id)
        
        query_faces = select(
            faces_table.c.id,
            faces_table.c.facial_area_top,
            faces_table.c.facial_area_left,
            faces_table.c.facial_area_width,
            faces_table.c.facial_area_height
        ).where(faces_table.c.file_id == file_id)

        result_file = conn.execute(query_file).fetchone()
        result_faces = conn.execute(query_faces)
        data_faces = [{
            "id": row.id,
            "facial_area_top": row.facial_area_top,
            "facial_area_left": row.facial_area_left,
            "facial_area_width": row.facial_area_width,
            "facial_area_height": row.facial_area_height
        } for row in result_faces]
        conn.close()

    if result_file is None:
        return "File not found", 404
    else:
        return render_template(
            "file.html",
            file_id = result_file.id,
            file_path = result_file.path,
            thumbnail_path = "/files/thumbnails/" + result_file.thumbnail_filename,
            last_updated = result_file.last_updated,
            faces = data_faces
        )


@blueprint.route("/thumbnails/<path:filename>")
def thumbnail(filename):
    """
    Serve a thumbnail from the thumbnail folder
    """
    return send_from_directory(
        os.path.join("../../", os.environ["THUMBNAILS_PATH"]), filename
    )


