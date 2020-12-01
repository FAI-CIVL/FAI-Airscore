# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import logging
import sys

from flask import Flask, render_template
from airscore import commands, public, user, internal
from airscore.extensions import (
    bcrypt,
    cache,
    csrf_protect,
    db,
    debug_toolbar,
    flask_static_digest,
    login_manager,
    migrate,
    mail,
)

from pathlib import Path
from redis import Redis
import rq
from flask_sse import sse
from airscore.user.models import User


def create_app(config_object="airscore.settings"):
    """Create application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split(".")[0])  # , debug=True)
    app.config.from_object(config_object)
    app.config.update(SESSION_COOKIE_SAMESITE='Lax')
    # app.config["REDIS_URL"] = app.config["REDIS_URL"]
    app.redis = Redis(host=app.config["REDIS_CONTAINER"], port=6379)
    app.task_queue = rq.Queue(app.config["RQ_QUEUE"], connection=app.redis)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    configure_logger(app)
    if app.config["SQLALCHEMY_DATABASE_URI"] != 'test':  # don't query the DB when unit testing
        with app.app_context():
            app.config['admin_exists'] = User.admin_exists()
        create_app_folders()
    return app


def register_extensions(app):
    """Register Flask extensions."""
    bcrypt.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    csrf_protect.init_app(app)
    login_manager.init_app(app)
    debug_toolbar.init_app(app)
    migrate.init_app(app, db)
    flask_static_digest.init_app(app)
    mail.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(user.views.blueprint)
    app.register_blueprint(internal.views.blueprint)
    app.register_blueprint(sse, url_prefix='/stream')
    return None


def register_errorhandlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, "code", 500)
        return render_template(f"{error_code}.html"), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {"db": db, "User": user.models.User}

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)


def configure_logger(app):
    """Configure loggers."""
    handler = logging.StreamHandler(sys.stdout)
    if not app.logger.handlers:
        app.logger.addHandler(handler)


def create_app_folders():
    """Created folders if not existing"""
    import Defines

    for app_dir in [Defines.TRACKDIR,
                    Defines.LOGDIR,
                    Defines.RESULTDIR,
                    Defines.MAPOBJDIR,
                    Defines.AIRSPACEDIR,
                    Defines.AIRSPACEMAPDIR,
                    Defines.AIRSPACECHECKDIR,
                    Defines.WAYPOINTDIR,
                    Defines.LIVETRACKDIR,
                    Defines.IGCPARSINGCONFIG,
                    Defines.TEMPFILES]:
        if not Path(app_dir).is_dir():
            Path(app_dir).mkdir(mode=0o755, parents=True)
