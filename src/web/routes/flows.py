"""Defines all routes related to controlling flows"""
from flask import Blueprint, render_template

blueprint = Blueprint('flows', __name__, url_prefix='/flows')

@blueprint.route("/")
def index():
    """
    Overview page
    """
    return render_template("base.html")
