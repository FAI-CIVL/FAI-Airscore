"""
needs to be run with python3.
i.e.
from xcontest.py import get_tracks

By Stuart Mackintosh, Antonio Golfari, 2019
"""
# TODO probably better add all sources to a sources folder? Create a sources package?

import logging
import time
from pathlib import Path

import requests
from db.conn import db_session

# in XContest format is:
# DE VIVO.ALESSANDRO.alexpab.2019-12-19.13-22-49.IGC
# surname.firstname.xcontest_id.YYYY-mm-dd.hh-mm-ss.IGC
filename_formats = ['name.name.live.other-other-other.other-other-other']


def get_pilot_from_list(filename, pilots):
    """check filename against a list of Pilot Obj.
    Looks for different information in filename

    filename:   STR file name
    pilots:     LIST Participants Obj.
    """
    # in XContest format is:
    # DE VIVO.ALESSANDRO.alexpab.2019-12-19.13-22-49.IGC
    # GALLO.LUCIANO.luciano.gallo.2020-07-18.11-22-07.IGC
    # GIULIANI.MATTEO.MG93.2020-07-18.11-27-01.IGC
    # surname.firstname.xcontest_id.YYYY-mm-dd.hh-mm-ss.IGC

    print(f'XContest get pilot function')
    string = Path(filename).stem
    fields = string.split('.')
    xcontest_id = '.'.join(fields[2:-2])
    name = ' '.join([str(fields[1]).lower(), str(fields[0]).lower()])
    print(f'Filename: {string}, xcontest_id: {xcontest_id}')
    for idx, pilot in enumerate(pilots):
        if pilot.xcontest_id and pilot.xcontest_id.lower() == xcontest_id.lower():
            '''found a pilot'''
            print(f'Found: Name {pilot.name.title()}, xcontest_id: {xcontest_id}')
            if not pilot.name.lower() in name:
                print(f'WARNING: Name {pilot.name.title()} does not match with filename {string}')
            return pilot
    return None


def get_xc_parameters(task_id):
    """Get site info and date from database """
    # TODO I suspect the logic on xc_site will be broken if we use waypoint file instead of table
    # Should we use TblTaskWaypoint instead or manually or by adding xc_to id to launch name or description?
    from db.tables import TblRegionWaypoint as R
    from db.tables import TblTask as T
    from db.tables import TblTaskWaypoint as W

    site_id = 0
    takeoff_id = 0
    datestr = None

    with db_session() as db:
        q = (
            db.query(R.xccSiteID, R.xccToID, T.date)
            .join(W, W.rwp_id == R.rwp_id)
            .join(T, T.task_id == W.task_id)
            .filter(W.task_id == task_id, W.type == 'launch')
            .one_or_none()
        )
        # date = T.get_by_id(task_id).date
        if q is not None:
            site_id = q.xccSiteID
            takeoff_id = q.xccToID
            date = q.date
            logging.info("site_id:%s takeoff_id:%s date:%s", site_id, takeoff_id, date)
            datestr = date.strftime('%Y-%m-%d')  # convert from datetime to string
        else:
            print('Error: no site found for the task')

    return site_id, takeoff_id, datestr


def get_zip(site_id, takeoff_id, date, login_name, password, zip_file):
    """Get the zip of igc files from xcontest."""
    import lxml.html

    # determine if we have takeoff id or only site id. preferable to use more specific takeoff id.
    if takeoff_id:
        location_id = takeoff_id
        site_launch = 'launch'
    else:
        location_id = site_id
        site_launch = 'site'
    # setup web stuff
    form = {}
    s = requests.session()
    form['login[username]'] = login_name
    form['login[password]'] = password

    # login om main page
    response = s.post('https://www.xcontest.org/world/en/', data=form)

    # send request for tracks
    time.sleep(4)
    # date = '2020-07-11'
    url = f'https://www.xcontest.org/util/igc.archive.comp.php?date={date}&{site_launch}={location_id}'
    print(url)
    response = s.get(url)

    if "No error" in response.text:
        logging.info("logged into xcontest and igc.archive.comp.php running with no error")
        print("logged into xcontest and igc.archive.comp.php running with no error. <br />")
    else:
        logging.error("igc.archive.comp.php not returning as expected")
        print("Error igc.archive.comp.php not returning as expected. See xcontest.log for details. <br />")
        logging.error("web page output:\n %s", response.text)
    webpage = lxml.html.fromstring(response.content)
    # print([el for el in webpage])
    try:
        zfile = requests.get(webpage.xpath('//a/@href')[0])
        # save the file
        with open(zip_file, 'wb') as f:
            f.write(zfile.content)
    except requests.exceptions.MissingSchema:
        print(f'Error: Seems like there are no tracks yet for location on {date}')


def get_zipfile(task_id):
    """"""
    import Defines

    temp_folder = Defines.TEMPFILES

    """get zipfile from XContest server"""
    site_id, takeoff_id, date = get_xc_parameters(task_id)
    if not site_id:
        return None

    login_name = Defines.XC_LOGIN
    password = Defines.XC_password
    zip_name = f'xcontest-{task_id}.zip'
    zipfile = Path(temp_folder, zip_name)
    get_zip(site_id, takeoff_id, date, login_name, password, zipfile)

    return zipfile
