"""Settings module for test app."""

from environs import Env
import Defines
env = Env()
env.read_env()

ENV = "development"
TESTING = True
SQLALCHEMY_DATABASE_URI = "sqlite://"
SECRET_KEY = "not-so-secret-in-tests"
BCRYPT_LOG_ROUNDS = (
    4  # For faster tests; needs at least 4 to avoid "ValueError: Invalid rounds"
)
DEBUG_TB_ENABLED = False
CACHE_TYPE = "simple"  # Can be "memcached", "redis", etc.
SQLALCHEMY_TRACK_MODIFICATIONS = False
WTF_CSRF_ENABLED = False  # Allows form testing

REDIS_URL = env.str("REDIS_URL") or 'redis://'
REDIS_CONTAINER = env.str("REDIS_CONTAINER")
WEB_SERVER_CONTAINER = env.str("WEB_SERVER_CONTAINER")
FLASK_CONTAINER = env.str("FLASK_CONTAINER")
FLASK_PORT = env.str("FLASK_PORT")
RQ_QUEUE = env.str("RQ_QUEUE")
MAIL_SERVER = env.str('MAIL_SERVER')
MAIL_PORT = env.int('MAIL_PORT') or 25
MAIL_USE_TLS = env.str('MAIL_USE_TLS') is not None
MAIL_USERNAME = env.str('MAIL_USERNAME')
MAIL_PASSWORD = env.str('MAIL_PASSWORD')
ADMINS = env.str('ADMINS')
ADMIN_DB = Defines.ADMIN_DB
ADMIN_SELF_REG = Defines.ADMIN_SELF_REG