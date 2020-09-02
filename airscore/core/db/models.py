from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.exc import DatabaseError
from .conn import Session

Base = declarative_base()
Base.query = Session.query_property()
metadata = Base.metadata
session = Session()


class BaseModel(Base):
    __abstract__ = True

    def as_dict(self) -> dict:
        return dict({c.key: getattr(self, c.key) for c in self.__table__.columns})

    @classmethod
    def get_by_id(cls, value: int):
        print(f'get_by_id session id: {id(session)}')
        return cls.query.get(int(value))

    @classmethod
    def get_all(cls, **kvargs):
        print(f'get_all session id: {id(session)}')
        return cls.query.filter_by(**kvargs).all()

    @classmethod
    def get_one(cls, **kvargs):
        print(f'get_one session id: {id(session)}')
        try:
            return cls.query.filter_by(**kvargs).one_or_none()
        except MultipleResultsFound:
            print(f"Error: Multiple results found")
            return None

    def from_obj(self, obj):
        """ populate a Table row object from an object
            Input:
                obj  - OBJ: object"""
        try:
            for x in self.__table__.columns.keys():
                if hasattr(obj, x):
                    setattr(self, x, getattr(obj, x))
            return self
        except TypeError as e:
            print(f'Error populating table row: obj is not iterable ({e})')

    def populate(self, obj: object) -> object:
        """ Associate query result with class object attributes, using same name
            Input:
                obj     - OBJ: object with attributes to populate with query result
                result  - OBJ: query result (should be one row)"""
        '''check if result has one row'''
        row = self[0] if isinstance(self, list) else self
        for x in obj.__dict__.keys():
            if hasattr(row, x):
                setattr(obj, x, getattr(row, x))
        return obj

    def before_save(self, *args, **kwargs):
        pass

    def after_save(self, *args, **kwargs):
        pass

    def save(self):
        self.before_save()
        print(f'save session id: {id(session)}')
        idx = session.add(self)
        self._commit()
        self.after_save()
        return idx

    def before_update(self, *args, **kwargs):
        pass

    def after_update(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        self.before_update(*args, **kwargs)
        print(f'update session id: {id(session)}')
        for key, value in kwargs.items():
            if key in self.__table__.columns.keys():
                setattr(self, key, value)
        self._commit()
        self.after_update(*args, **kwargs)

    def save_or_update(self):
        try:
            key = next((c.name for c in self.__table__.columns.values() if c.primary_key), None)
            idv = getattr(self, key)
            if idv and self.get_by_id(idv):
                self.update()
            else:
                idv = self.save()
            return idv
        except DatabaseError as e:
            print(f'Database error: rolling back... ({e})')
            return None

    def delete(self):
        print(f'delete session id: {id(session)}')
        session.delete(self)
        self._commit()

    @classmethod
    def delete_all(cls, **kvargs):
        print(f'delete all session id: {id(session)}')
        cls.query.filter_by(**kvargs).delete(synchronize_session=False)
        session.commit()

    @classmethod
    def before_bulk_save(cls, iterable, *args, **kwargs):
        pass

    @classmethod
    def after_bulk_save(cls, model_objs, *args, **kwargs):
        pass

    @classmethod
    def bulk_save(cls, iterable, *args, **kwargs):
        cls.before_bulk_save(iterable, *args, **kwargs)
        model_objs = []
        for data in iterable:
            if not isinstance(data, cls):
                data = cls(**data)
            model_objs.append(data)
        print(f'bulk_save session id: {id(session)}')
        try:
            session.bulk_save_objects(model_objs)
            session.flush()
        except DatabaseError as e:
            print(f'Database error: rolling back... ({e})')
            session.rollback()
        else:
            session.commit()
        cls.after_bulk_save(model_objs, *args, **kwargs)
        return model_objs

    @classmethod
    def bulk_save_or_none(cls, iterable, *args, **kwargs):
        try:
            return cls.bulk_save(iterable, *args, **kwargs)
        except DatabaseError:
            return None

    def _flush(self):
        try:
            session.flush()
        except DatabaseError as e:
            print(f'Database error: rolling back... ({e})')
            session.rollback()
            # raise

    def _commit(self):
        try:
            session.commit()
        except DatabaseError as e:
            print(f'Database error: rolling back... ({e})')
            session.rollback()
            # raise