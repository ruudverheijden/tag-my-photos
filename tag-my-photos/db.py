import sqlite3

import click
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    # Run SQL script to initiate the database
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

# Create CLI command to initialize the database
@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')
    
    
def init_app(app):
    """Register database functions with the app,. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db) # Closes DB when cleaning up after returning the response
    app.cli.add_command(init_db_command)