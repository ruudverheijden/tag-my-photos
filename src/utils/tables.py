from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, ForeignKey

meta = MetaData()
    
files = Table(
    'files', meta, 
    Column('id', Integer, primary_key = True), 
    Column('path', String), 
    Column('hash', String(length=64)),
    Column('last_updated', DateTime)
)

faces = Table(
    'faces', meta, 
    Column('id', Integer, primary_key = True), 
    Column('file_id', ForeignKey('files.id'), nullable=False),
    Column('person_id', ForeignKey('persons.id')),
)

persons = Table(
    'persons', meta, 
    Column('id', Integer, primary_key = True), 
    Column('name', String),
    Column('person_id', ForeignKey('persons.id'), nullable=True),
)