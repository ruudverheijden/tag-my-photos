"""Defines all routes related to clusters"""
import os

from flask import Blueprint, render_template
from sqlalchemy import create_engine, select
from src.utils.tables import clusters as clusters_table, faces as faces_table

blueprint = Blueprint('clusters', __name__, url_prefix='/clusters')

@blueprint.route("/")
def index():
    """
    Show an overview of all clusters in the database
    """
    db_engine = create_engine("sqlite:///" + os.environ["DATABASE_PATH"])
    with db_engine.connect() as conn:
        # Fetch all clusters and related faces
        query_clusters = (
            select(
                clusters_table.c.cluster_id,
                clusters_table.c.face_id,
                faces_table.c.file_id,
                faces_table.c.thumbnail_filename
            ).join(
                faces_table, clusters_table.c.face_id == faces_table.c.id
            ).order_by(clusters_table.c.cluster_id)
        )
        result_clusters = conn.execute(query_clusters)

        # Create a dictionary to group rows by cluster_id
        data_clusters = dict()

        # Iterate over the rows and append them to the appropriate group
        for row in result_clusters:
            # Use setdefault to initialize the list if the key does not exist
            data_clusters.setdefault(str(row.cluster_id), []).append({
                "face_id": row.face_id,
                "file_id": row.file_id,
                "thumbnail_path": "/files/thumbnails/" + row.thumbnail_filename
            })
        print(data_clusters)
        conn.close()
    return render_template(
        "clusters_overview.html", clusters=data_clusters
    )
