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
        query = select(faces_table.c.id, faces_table.c.thumbnail_filename)
        result = conn.execute(query)
        thumbnails = [{'thumbnail_path': "/thumbnails/" + row[1], 'id': row[0]} for row in result]
        conn.close()
    return render_template('faces_overview.html', thumbnails=thumbnails)

@app.route("/thumbnails/<path:filename>")
def serve_thumbnail(filename):
    """
    Serve a thumbnail from the thumbnail folder
    """
    return send_from_directory(os.path.join("../../", os.environ["THUMBNAILS_PATH"]), filename)