"""
Use token to access the HTTP API:
Keep your token secure and store it safely, it can be used by anyone to control your bot.
For a description of the Bot API, see this page: https://core.telegram.org/bots/api
"""
import requests
from Defines import TELEGRAM_API, TELEGRAM_CHANNEL
from db.conn import db_session

# telegram url
url = f"https://api.telegram.org/bot{TELEGRAM_API}/"


def get_download_status(taskid: int):
    from db.tables import FlightResultView as F
    from calcUtils import sec_to_time
    all_data = []
    with db_session() as db:
        results = db.query(F).filter_by(task_id=taskid).all()
        for pilot in [p for p in results if p.result_type not in ('abs', 'dnf', 'mindist')]:
            data = {'ID': pilot.ID, 'name': pilot.name}
            if pilot.ESS_time:
                time = sec_to_time(pilot.ESS_time - pilot.SSS_time)
                if pilot.result_type == 'goal':
                    result = f'GOAL {time}'
                else:
                    result = f"ESS {round(pilot.distance_flown / 1000, 2)} Km (~{time}~)"
            else:
                result = f"LO {round(pilot.distance_flown / 1000, 2)} Km"
            data['result'] = result
            all_data.append(data)
    return all_data


def get_missing_pilots(task_id: int):
    from db.tables import UnscoredPilotView as U
    all_data = []
    with db_session() as db:
        results = db.query(U).filter_by(task_id=task_id).all()
        for p in results:
            all_data.append(dict(ID=p.ID, name=p.name))
    return all_data


def send_download_status(task_id: int):
    import time
    from calcUtils import epoch_to_string
    data = get_download_status(task_id)
    if data:
        date = epoch_to_string(time.time())
        text = f'*Tracks Downloads* \n'
        text += f'_updated at {date} UTC:_ \n'
        for p in sorted(data, key=lambda x: x['name']):
            text += f"{p['name']}: {p['result']} \n"
        text += f' - \n'
        missing = get_missing_pilots(task_id)
        if missing:
            text += f'*Pilots without result:* \n'
            for p in sorted(missing, key=lambda x: x['name']):
                text += f"{p['name']} \n"
        else:
            text += f'*All Pilots plotted.* \n'
            text += f'Results will be available soon. \n'
        '''format text'''
        text = text.replace('.', '\\.').replace('-', '\\-').replace('(', '\\(').replace(')', '\\)')
        return send_mess(text)


def send_mess(text):
    params = {'chat_id': TELEGRAM_CHANNEL, 'text': text, 'parse_mode': 'MarkdownV2'}
    response = requests.post(url + 'sendMessage', json=params)
    return response.json()
