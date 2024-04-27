from flask_bootstrap import Bootstrap5
from flask import Flask, render_template, send_from_directory
from sqlalchemy import create_engine, select
from dotenv import load_dotenv
import os
from ..utils.tables import files as files_table, faces as faces_table

load_dotenv()  # Inject environment variables from .env during development

app = Flask(__name__)

bootstrap = Bootstrap5(app)

@app.route("/")
def index():
    return render_template('base.html')

@app.route("/faces")
def faces():
    """
    Show an overview of all faces in the database
    """
    db_engine = create_engine('sqlite:///' + os.environ["DATABASE_PATH"])
    with db_engine.connect() as conn:
        query = select(
            faces_table.c.id.label("face_id"),
            faces_table.c.thumbnail_filename,
            files_table.c.id.label("file_id")).join(
                files_table,
                faces_table.c.file_id == files_table.c.id
            )
        result = conn.execute(query)
        thumbnails = [{
            'thumbnail_path': "/thumbnail/" + row.thumbnail_filename,
            'face_id': row.face_id,
            'file_id': row.file_id
            } for row in result]
        conn.close()
    return render_template('faces_overview.html', thumbnails=thumbnails)

@app.route("/thumbnail/<path:filename>")
def thumbnail(filename):
    """
    Serve a thumbnail from the thumbnail folder
    """
    return send_from_directory(os.path.join("../../", os.environ["THUMBNAILS_PATH"]), filename)

@app.route("/file/<int:id>")
def file(id):
    """
    Show the photo from the files table based on the id
    """
    db_engine = create_engine('sqlite:///' + os.environ["DATABASE_PATH"])
    with db_engine.connect() as conn:
        query = select(files_table.c.thumbnail_filename).where(files_table.c.id == id)
        result = conn.execute(query)
        row = result.fetchone()
        conn.close()
    return render_template('file.html', file_path="/thumbnail/" + row.thumbnail_filename)