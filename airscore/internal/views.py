# -*- coding: utf-8 -*-
"""Internal views. for comms from worker container"""

from flask import (
    Blueprint,
    request,
    jsonify
)
from airscore.extensions import csrf_protect
from flask_sse import sse
import redis

cache = redis.Redis(host='redis', port=6379)
blueprint = Blueprint("internal", __name__, url_prefix="/internal", static_folder="../static")


@blueprint.route('/see_message', methods=['POST'])
@csrf_protect.exempt
def see_message():
    # ip = request.remote_addr
    data = request.json
    message = data['body']
    sse.publish(message, channel=data['channel'], type=data['type'], retry=30)
    # print(f"published message: {data['body']} id:{data['body']['id']} ip{ip} {data['type']=} {data['channel']=}")
    resp = jsonify(success=True)
    return resp


