"""Defines all routes related to files"""
import os

from flask import Blueprint, render_template, send_from_directory
from sqlalchemy import create_engine, select
from src.utils.tables import files as files_table

blueprint = Blueprint("files", __name__, url_prefix='/files')

@blueprint.route("/<int:file_id>")
def get_file(file_id):
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
            "file.html", file_path="/files/thumbnails/" + row.thumbnail_filename
        )


@blueprint.route("/thumbnails/<path:filename>")
def thumbnail(filename):
    """
    Serve a thumbnail from the thumbnail folder
    """
    return send_from_directory(
        os.path.join("../../", os.environ["THUMBNAILS_PATH"]), filename
    )


