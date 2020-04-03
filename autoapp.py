# -*- coding: utf-8 -*-
"""Create an application instance."""
from airscore.app import create_app #, socketio
from flask_wtf.csrf import CSRFProtect


app = create_app()

CSRFProtect(app)

# socketio.run(CSRFProtect(app))