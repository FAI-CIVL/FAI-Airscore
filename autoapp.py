# -*- coding: utf-8 -*-
"""Create an application instance."""
from airscore.app import create_app
from flask_wtf.csrf import CSRFProtect


app = create_app()
CSRFProtect(app)
