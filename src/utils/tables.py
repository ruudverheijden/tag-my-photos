from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, ForeignKey, Boolean, LargeBinary, Float

meta = MetaData()
    
files = Table(
    'files', meta, 
    Column('id', Integer, primary_key = True), 
    Column('path', String, unique=True, nullable=False), 
    Column('hash', String(length=64), nullable=False),
    Column('last_updated', DateTime, nullable=False),
    Column('contains_face', Boolean)
)

faces = Table(
    'faces', meta, 
    Column('id', Integer, primary_key = True), 
    Column('file_id', ForeignKey('files.id'), nullable=False),
    Column('person_id', ForeignKey('persons.id')),
    Column('thumbnail_path', String),
    Column('embedding', LargeBinary, nullable=False),
    Column('confidence', Float, nullable=False),
    Column('facial_area_top', Integer, nullable=False),
    Column('facial_area_left', Integer, nullable=False),
    Column('facial_area_width', Integer, nullable=False),
    Column('facial_area_height', Integer, nullable=False)
)

persons = Table(
    'persons', meta, 
    Column('id', Integer, primary_key = True), 
    Column('name', String)
)