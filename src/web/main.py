"""Runs the Flask based web application"""

from flask import Flask

from .routes.faces import blueprint as faces_bp
from .routes.clusters import blueprint as clusters_bp
from .routes.files import blueprint as files_bp
from .routes.persons import blueprint as persons_bp
from .routes.flows import blueprint as flows_bp

app = Flask(__name__)

# Register the blueprints
app.register_blueprint(faces_bp)
app.register_blueprint(clusters_bp)
app.register_blueprint(files_bp)
app.register_blueprint(persons_bp)
app.register_blueprint(flows_bp)

if __name__ == "__main__":
    app.run(debug=True)
