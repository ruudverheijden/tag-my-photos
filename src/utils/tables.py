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
    Column('confidence', Float, nullable=False)
)

persons = Table(
    'persons', meta, 
    Column('id', Integer, primary_key = True), 
    Column('name', String)
)