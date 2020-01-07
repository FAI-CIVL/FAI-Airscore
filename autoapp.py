# -*- coding: utf-8 -*-
"""Create an application instance."""
from airscore.app import create_app
from flask_wtf.csrf import CsrfProtect


app = create_app()
CsrfProtect(app)
