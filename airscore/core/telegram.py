"""
Use token to access the HTTP API:
Keep your token secure and store it safely, it can be used by anyone to control your bot.
For a description of the Bot API, see this page: https://core.telegram.org/bots/api
"""
import json

import requests
from calcUtils import c_round
from db.conn import db_session
from Defines import TELEGRAM_API, TELEGRAM_CHANNEL

# telegram url
url = f"https://api.telegram.org/bot{TELEGRAM_API}/"


def get_download_status(task_id: int):
    from calcUtils import sec_to_time
    from db.tables import TblParticipant as P
    from db.tables import TblTask as T
    from db.tables import TblTaskResult as R

    valid = []
    missing = []
    with db_session() as db:
        results = (
            db.query(P.ID, P.name, R.result_type, R.distance_flown, R.SSS_time, R.ESS_time, R.goal_time)
            .join(T, P.comp_id == T.comp_id)
            .outerjoin(R, (R.par_id == P.par_id) & (R.task_id == T.task_id))
            .filter(T.task_id == task_id)
            .all()
        )
        pilots = len(results)
        valid_results = [p for p in results if p.result_type not in ('abs', 'dnf', 'mindist', None)]
        for pilot in results:
            data = {'ID': pilot.ID, 'name': pilot.name}
            if pilot in valid_results:
                if pilot.ESS_time:
                    time = sec_to_time(pilot.ESS_time - pilot.SSS_time)
                    if pilot.result_type == 'goal':
                        result = f'GOAL {time}'
                    else:
                        result = f"ESS {c_round(pilot.distance_flown / 1000, 2)} Km (~{time}~)"
                else:
                    result = f"LO {c_round(pilot.distance_flown / 1000, 2)} Km"
                data['result'] = result
                valid.append(data)
            elif not pilot.result_type:
                missing.append(data)
    return pilots, valid, missing


def get_active_result(task_id: int) -> dict:
    """Reads competition from json result file
    takes com_id as argument"""
    from db.tables import TblResultFile as R

    with db_session() as db:
        file = db.query(R).filter_by(task_id=task_id, active=1).first()
        return file.as_dict() if file else {}


def get_info(task_id: int):
    from db.tables import TaskObjectView as T

    t = T.get_by_id(task_id)
    return t.as_dict()


def send_result_status(task_id: int, info: dict):
    import time

    from calcUtils import epoch_to_string

    pilots, valid, missing = get_download_status(task_id)
    print(pilots, valid, missing)
    result = get_active_result(task_id)
    if not (valid or result):
        print(f'Error, No result and no track downloaded')
        return False
    date = epoch_to_string(time.time()).replace('-', '\\-')
    if not info:
        info = get_info(task_id)
    comp_name = info['comp_name'].replace('.', '\\.').replace('(', '\\(').replace(')', '\\)').replace('-', '\\-')
    text = f"*{comp_name} \\| Task {info['task_num']}* \n"
    if result:
        '''we have a task result available'''
        status = result['status'].replace('.', '\\.').replace('(', '\\(').replace(')', '\\)').replace('-', '\\-')
        text += f'[*Results*](https://airscore.legapiloti.it/task_result/{task_id}) \n'
        #  TODO create parametric url (possible?)
        text += f'*Status: {status}* \n'
        text += f'_updated at {date} UTC:_ \n'
    else:
        '''we have tracks downloads available'''
        text += f'*Tracks Downloads* \n'
        total = pilots - len(missing)
        text += f'*{total} tracks / {pilots} pilots* \n'
        text += f'_updated at {date} UTC:_ \n'
        for p in sorted(valid, key=lambda x: x['name']):
            text += f"{p['name']}: {p['result']} \n".replace('.', '\\.').replace('(', '\\(').replace(')', '\\)')
    if missing:
        text += f'\\-\\-\\- \n'
        text += f'*Pilots without result \\({len(missing)}\\):* \n'
        for p in sorted(missing, key=lambda x: x['name']):
            text += f"{p['name']} \n"
    else:
        text += f'*All Pilots plotted\\.* \n'
    return send_mess(text)


def send_mess(text: str, chat: int = TELEGRAM_CHANNEL):
    if text:
        params = {'chat_id': chat, 'text': text, 'parse_mode': 'MarkdownV2'}
        response = requests.post(url + 'sendMessage', json=params)
        if not response.json()['ok']:
            print(f"Error: {response.json()['description']}")
        return response.json()['ok']


def bot_responder(data: json):
    chat_id = int(data['message']['chat_id'])
    msg = str(data['text']).strip('/').lower()
    if not msg:
        send_mess(text='Cannot understand', chat=chat_id)
    send_mess(text=f'Received: {msg}', chat=chat_id)
