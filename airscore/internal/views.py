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


@blueprint.route('/_progress_livetrack', methods=['POST'])
@csrf_protect.exempt
def progress_livetrack():
    import frontendUtils


    data = request.json
    taskid = data.get('taskid')
    job_id = data.get('job_id')
    username = data.get('username')
    interval = data.get('interval')
    delay = data.get('delay')
    error = None
    status = None
    job = frontendUtils.schedule_livetracking(taskid, job_id, username, interval, delay)
    if job:
        status = job.get_status()
        if not job.is_failed:
            # frontendUtils.call_livetracking_scheduling_endpoint(taskid, job_id, username)
            return jsonify(success=True, job_id=job.id, error=error, status=status)
        else:
            error = job.exc_info.strip().split('\n')[-1]
            return jsonify(success=False, job_id=job.id, error=error, status=status)

    return jsonify(success=False, job_id=None, error=error, status=status)


@blueprint.route('/_stop_livetrack', methods=['POST'])
@csrf_protect.exempt
def stop_livetrack():
    import frontendUtils


    data = request.json
    taskid = data.get('taskid')
    username = data.get('username')
    resp = frontendUtils.stop_livetracking(taskid, username)

    return jsonify(success=resp)

