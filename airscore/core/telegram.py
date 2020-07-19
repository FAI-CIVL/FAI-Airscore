"""
Use token to access the HTTP API:
Keep your token secure and store it safely, it can be used by anyone to control your bot.
For a description of the Bot API, see this page: https://core.telegram.org/bots/api
"""
import requests
import json
from Defines import TELEGRAM_API, TELEGRAM_CHANNEL
from db.conn import db_session

# telegram url
url = f"https://api.telegram.org/bot{TELEGRAM_API}/"


def get_download_status(taskid: int):
    from db.tables import TblParticipant as P, TblTaskResult as R, TblTask as T
    from calcUtils import sec_to_time
    valid = []
    missing = []
    with db_session() as db:
        results = db.query(P.ID, P.name, R.result_type, R.distance_flown, R.SSS_time, R.ESS_time, R.goal_time)\
                    .outerjoin(R, R.par_id == P.par_id)\
                    .join(T, P.comp_id == T.comp_id)\
                    .filter(T.task_id == taskid).all()
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
                        result = f"ESS {round(pilot.distance_flown / 1000, 2)} Km (~{time}~)"
                else:
                    result = f"LO {round(pilot.distance_flown / 1000, 2)} Km"
                data['result'] = result
                valid.append(data)
            elif not pilot.result_type:
                missing.append(data)
    return pilots, valid, []


def send_download_status(task_id: int):
    import time
    from calcUtils import epoch_to_string
    pilots, valid, missing = get_download_status(task_id)
    if valid:
        date = epoch_to_string(time.time()).replace('-', '\\-')
        text = f'*Tracks Downloads* \n'
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
            text += f'[Results](https://airscore.legapiloti.it/task_result/{task_id}) will be available soon\\. \n'
            #  TODO create parametric url (possible?)
        return send_mess(text)


def send_mess(text: str, chat: int = TELEGRAM_CHANNEL):
    if text:
        params = {'chat_id': chat, 'text': text, 'parse_mode': 'MarkdownV2'}
        response = requests.post(url + 'sendMessage', json=params)
        return response.json()


def bot_responder(data: json):
    chat_id = int(data['message']['chat_id'])
    msg = str(data['text']).strip('/').lower()
    if not msg:
        send_mess(text='Cannot understand', chat=chat_id)
    send_mess(text=f'Received: {msg}', chat=chat_id)
