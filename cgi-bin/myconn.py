"""
Module for mySQL connection using sqlalchemy
Use:    from myconn import Database

Antonio Golfari - 2019
"""

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapper, class_mapper, relationship
import Defines as d

'''basic connection'''
user    = d.MYSQLUSER
passwd  = d.MYSQLPASSWORD
host    = d.MYSQLHOST
dbase   = d.DATABASE

connectionString    = f'mysql+pymysql://{user}:{passwd}@{host}/{dbase}?charset=utf8mb4'
Base                = declarative_base()
metadata            = Base.metadata

class Database(object):
    """SQLAlchemy database connection"""
    def __init__(self, connection_string=connectionString):
        self.connection_string  = connection_string
        self.session            = None
    def __enter__(self):
        engine  = create_engine(self.connection_string)
        Session = sessionmaker()
        self.session = Session(bind=engine)
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def populate_obj(self, obj, result):
        ''' Associate query result with class object attributes, using same name
            Input:
                obj     - OBJ: object with attributes to populate with query result
                result  - OBJ: query result (should be one row)'''

        '''check if result has one row'''
        if type(result) == list: result = result[0]
        for x in obj.__dict__.keys():
            if hasattr(result,x): setattr(obj, x, getattr(result,x))

    # def as_dict(self, obj):
    #     ''' as we have still a lot of procedures written for dicts created from
    #         old MySQL queries
    #         Returns a dict if obj is a single row, or a list of dicts if obj is a list
    #     '''
    #     from sqlalchemy import inspect
    #     if type(obj) is list:
    #         return [    {c.key: getattr(el, c.key)
    #                     for c in inspect(el).mapper.column_attrs}
    #                 for el in obj]
    #     else:
    #         return {c.key: getattr(obj, c.key)
    #             for c in inspect(obj).mapper.column_attrs}

    def as_dict(self, obj):
        ''' as we have still a lot of procedures written for dicts created from
            old MySQL queries
            Returns a dict if obj is a single row, or a list of dicts if obj is a list
        '''
        from sqlalchemy import inspect
        if type(obj) is list:
            return [object_to_dict(el) for el in obj]
        else:
            return object_to_dict(obj)

def get_row(row):
    from collections import OrderedDict
    result = OrderedDict()
    for key in row.__mapper__.c.keys():
        if getattr(row, key) is not None:
            result[key] = str(getattr(row, key))
        else:
            result[key] = getattr(row, key)
    return result

def get_row_2(row):
    from sqlalchemy import inspect
    return {c.key: getattr(row, c.key)
             for c in inspect(row).mapper.column_attrs}

def model_to_dict(obj, visited_children=None, back_relationships=None):
    if visited_children is None:
        visited_children = set()
    if back_relationships is None:
        back_relationships = set()
    serialized_data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
    relationships = class_mapper(obj.__class__).relationships
    visitable_relationships = [(name, rel) for name, rel in relationships.items() if name not in back_relationships]
    for name, relation in visitable_relationships:
        if relation.backref:
            back_relationships.add(relation.backref)
        relationship_children = getattr(obj, name)
        if relationship_children is not None:
            if relation.uselist:
                children = []
                for child in [c for c in relationship_children if c not in visited_children]:
                    visited_children.add(child)
                    children.append(model_to_dict(child, visited_children, back_relationships))
                serialized_data[name] = children
            else:
                serialized_data[name] = model_to_dict(relationship_children, visited_children, back_relationships)
    return serialized_data

def object_to_dict(obj, found=None):
    from datetime import datetime
    if found is None:
        found = set()
    mapper = class_mapper(obj.__class__)
    columns = [column.key for column in mapper.columns]
    get_key_value = lambda c: (c, getattr(obj, c).isoformat()) if isinstance(getattr(obj, c), datetime) else (c, getattr(obj, c))
    out = dict(map(get_key_value, columns))
    for name, relation in mapper.relationships.items():
        if relation not in found:
            found.add(relation)
            related_obj = getattr(obj, name)
            if related_obj is not None:
                if relation.uselist:
                    out[name] = [object_to_dict(child, found) for child in related_obj]
                else:
                    out[name] = object_to_dict(related_obj, found)
    return out
