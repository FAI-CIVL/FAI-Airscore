# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template
from flask_login import login_required
import frontendUtils

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")


@blueprint.route("/")
@login_required
def members():
    """List members."""
    return render_template("users/members.html")


@blueprint.route('/get_admin_comps', methods=['GET', 'POST'])
def get_admin_comps():
    return frontendUtils.get_comps()


@blueprint.route('/comp_admin', methods=['GET', 'POST'])
def comp_admin():
    return render_template('users/comp_admin.html')