# -*- coding: utf-8 -*-
"""Create an application instance."""
from airscore.app import create_app
from flask_wtf.csrf import CSRFProtect
from airscore.user.models import User

app = create_app()
CSRFProtect(app)
with app.app_context():
    app.config['admin_exists'] = User.admin_exists()

