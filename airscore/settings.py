# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set
environment variables.
"""
from environs import Env
import Defines
env = Env()
env.read_env()

# SYSTEM CONFIG
ENV = env.str("FLASK_ENV", default="production")
DEBUG = ENV == "development"
SQLALCHEMY_DATABASE_URI = env.str("DATABASE_URI")
SECRET_KEY = env.str("SECRET_KEY")
SECURITY_PASSWORD_SALT = env.str("SECURITY_PASSWORD_SALT")
SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT")
BCRYPT_LOG_ROUNDS = env.int("BCRYPT_LOG_ROUNDS", default=13)
DEBUG_TB_ENABLED = DEBUG
DEBUG_TB_INTERCEPT_REDIRECTS = False
CACHE_TYPE = "redis"  # Can be "memcached", "redis", etc.
SQLALCHEMY_TRACK_MODIFICATIONS = False
REDIS_URL = env.str("REDIS_URL") or 'redis://'
REDIS_CONTAINER = env.str("REDIS_CONTAINER")
WEB_SERVER_CONTAINER = env.str("WEB_SERVER_CONTAINER")
FLASK_CONTAINER = env.str("FLASK_CONTAINER")
FLASK_PORT = env.str("FLASK_PORT")
RQ_QUEUE = env.str("RQ_QUEUE")
MAIL_SERVER = env.str('MAIL_SERVER')
MAIL_PORT = env.int('MAIL_PORT') or 25
MAIL_USE_TLS = env.bool('MAIL_USE_TLS') or False
MAIL_USE_SSL = env.bool('MAIL_USE_SSL') or False
MAIL_USERNAME = env.str('MAIL_USERNAME')
MAIL_PASSWORD = env.str('MAIL_PASSWORD')
ADMINS = env.str('ADMINS')

# APPLICATION FEATURES CONFIG
ADMIN_DB = Defines.ADMIN_DB
ADMIN_SELF_REG = Defines.ADMIN_SELF_REG
PILOT_DB = Defines.PILOT_DB
PILOT_DB_WRITE = Defines.PILOT_DB_WRITE
WAYPOINT_AIRSPACE_FILE_LIBRARY = Defines.WAYPOINT_AIRSPACE_FILE_LIBRARY
TELEGRAM = Defines.TELEGRAM
LADDERS = Defines.LADDERS
