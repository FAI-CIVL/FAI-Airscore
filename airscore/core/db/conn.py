"""
Module for mySQL connection using sqlalchemy
Use:    from db.conn import db_session

Airscore
Antonio Golfari, Stuart Mackintosh - 2020
"""

from contextlib import contextmanager

from Defines import DATABASE, MYSQLHOST, MYSQLPASSWORD, MYSQLUSER
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.scoping import scoped_session

'''basic connection'''
host = MYSQLHOST
dbase = DATABASE
user = MYSQLUSER
passwd = MYSQLPASSWORD

connectionString = f'mysql+pymysql://{user}:{passwd}@{host}/{dbase}?charset=utf8mb4'
# engine = create_engine(connectionString,
#                        pool_pre_ping=True,
#                        echo=True)       # pool_pre_ping could be deleted if MySQL is stable
engine = create_engine(connectionString, pool_pre_ping=True, convert_unicode=True)

Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


@contextmanager
def db_session():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    print(f'with session id: {id(session)}')
    try:
        yield session
        session.commit()
    except SQLAlchemyError:
        print('SQLAlchemy Error')
        session.rollback()
        raise
    except IntegrityError as e:
        print('Integrity Error')
        session.rollback()
        raise
    except Exception:
        print('Exception Error')
        session.rollback()
        raise
    except NoResultFound:
        print('No Result Found for Query')
        session.rollback()
        raise
    finally:
        # session.expunge_all()
        # session.close()
        ''''''
