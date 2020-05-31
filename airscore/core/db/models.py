from sqlalchemy.ext.declarative import declarative_base
from .conn import db_session, Session
Base = declarative_base()
metadata = Base.metadata

# db = Session()


class BaseModel(Base):
    __abstract__ = True

    def as_dict(self) -> dict:
        return dict({c.key: getattr(self, c.key) for c in self.__table__.columns})

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

    @classmethod
    def get_by_id(cls, value: int):
        with db_session() as db:
            print(f'model session id: {id(db)}')
            return db.query(cls).get(int(value))


    # def before_save(self, *args, **kwargs):
    #     pass
    #
    # def after_save(self, *args, **kwargs):
    #     pass
    #
    # def save(self, commit=True):
    #     self.before_save()
    #     db.add(self)
    #     if commit:
    #         try:
    #             db.commit()
    #         except Exception as e:
    #             db.rollback()
    #             raise e
    #
    #     self.after_save()
    #
    # def before_update(self, *args, **kwargs):
    #     pass
    #
    # def after_update(self, *args, **kwargs):
    #     pass
    #
    # def update(self, *args, **kwargs):
    #     self.before_update(*args, **kwargs)
    #     db.commit()
    #     self.after_update(*args, **kwargs)
    #
    # def delete(self, commit=True):
    #     db.delete(self)
    #     if commit:
    #         db.commit()

    # @classmethod
    # def before_bulk_create(cls, iterable, *args, **kwargs):
    #     pass
    #
    # @classmethod
    # def after_bulk_create(cls, model_objs, *args, **kwargs):
    #     pass
    #
    # @classmethod
    # def bulk_create(cls, iterable, *args, **kwargs):
    #     cls.before_bulk_create(iterable, *args, **kwargs)
    #     model_objs = []
    #     for data in iterable:
    #         if not isinstance(data, cls):
    #             data = cls(**data)
    #         model_objs.append(data)
    #
    #     db.bulk_save_objects(model_objs)
    #     if kwargs.get('commit', True) is True:
    #         db.commit()
    #     cls.after_bulk_create(model_objs, *args, **kwargs)
    #     return model_objs
    #
    #
    # @classmethod
    # def bulk_create_or_none(cls, iterable, *args, **kwargs):
    #     try:
    #         return cls.bulk_create(iterable, *args, **kwargs)
    #     except exc.IntegrityError as e:
    #         db.rollback()
    #         return None
