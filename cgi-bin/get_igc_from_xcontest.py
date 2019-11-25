'''
needs to be run with python3.
i.e.
python3 get_igc_from_xcontest.py <tasPk>

By Stuart Mackintosh, Antonio Golfari, 2019
'''
import sys, logging
from task import Task
from myconn import Database
import formula as For
from trackDB import read_formula
import time
import requests


def get_xc_parameters(task_id):
    """Get site info and date from database """
    from db_tables import TaskXContestWptView as XC
    from datetime import datetime

    site_id = 0
    takeoff_id = 0
    datestr = None

    with Database() as db:
        q = db.session.query(XC).get(task_id)
    if q is not None:
        site_id = q.xccSiteID
        takeoff_id = q.xccToID
        date = q.tasDate

        logging.info("site_id:%s takeoff_id:%s date:%s", site_id, takeoff_id, date)
        datestr = date.strftime('%Y-%m-%d') #convert from datetime to string
    else:
        print('Error: no site found for the task')
    return(site_id, takeoff_id, datestr)

def get_zip(site_id, takeoff_id, date, login_name, password, zip_destination, zip_name):
    """Get the zip of igc files from xcontest."""
    import lxml.html

    #determine if we have takeoff id or only site id. preferable to use more specific takeoff id.
    if takeoff_id:
        location_id = takeoff_id
        site_launch = 'launch'
    else:
        location_id = site_id
        site_launch = 'site'
    #setup web stuff
    form={}
    s=requests.session()
    form['login[username]'] = login_name
    form['login[password]'] = password

    #login om main page
    response = s.post('https://www.xcontest.org/world/en/', data=form)

    #send request for tracks
    time.sleep(4)
    response = s.get('https://www.xcontest.org/util/igc.archive.comp.php?date=%s&%s=%s'% (date, site_launch, location_id))

    if "No error" in response.text:
        logging.info("logged into xcontest and igc.archive.comp.php running with no error")
        print("logged into xcontest and igc.archive.comp.php running with no error. <br />")
    else:
        logging.error("igc.archive.comp.php not returing as expected")
        print("Error igc.archive.comp.php not returing as expected. See xcontest.log for details. <br />")
        logging.error("web page output:\n %s",response.text)
    webpage=lxml.html.fromstring(response.content)
    zfile=requests.get(webpage.xpath('//a/@href')[0])

    #save the file
    with open(zip_destination+'/'+zip_name,'wb') as f:
        f.write(zfile.content)

def main(args):
    from trackUtils import extract_tracks, get_tracks, assign_and_import_tracks
    from tempfile import TemporaryDirectory
    import Defines

    """Main module"""
    result = ''
    task_id = 0 + int(args[0])

    """Get Task object"""
    task = Task.read(task_id)
    if task.opt_dist == 0:
        print('task not optimised.. optimising')
        task.calculate_optimised_task_length()

    if task.comp_id > 0:
        """get zipfile from XContest server"""
        site_id, takeoff_id, date = get_xc_parameters(task_id)
        login_name = Defines.XC_LOGIN
        password = Defines.XC_password
        zip_name = 'igc_from_xc.zip'

        """create a temp dire for zip file"""
        with TemporaryDirectory() as zip_destination:
            get_zip(site_id, takeoff_id, date, login_name, password, zip_destination, zip_name)
            """create a temporary directory for tracks"""
            zipfile = zip_destination + '/' + zip_name
            with TemporaryDirectory() as tracksdir:
                error = extract_tracks(zipfile, tracksdir)
                if not error:
                    """find valid tracks"""
                    tracks = get_tracks(tracksdir)
                    if tracks is not None:
                        """associate tracks to pilots and import"""
                        assign_and_import_tracks(tracks, task, xcontest=True)
                    else:
                        result = (f"There is no valid track in zipfile {zipfile} \n")
                else:
                    result = (f"An error occured while dealing with file {zipfile} \n")
    else:
        result = (f"error: task ID {task.id} does NOT belong to any Competition \n")

    print (result)

if __name__ == "__main__":
    import sys

    '''check parameter is good'''
    if not (sys.argv[1] and sys.argv[1].isdigit() and int(sys.argv[1]) > 0):
        print("number of arguments != 1 and/or task_id not a number")
        print("usage: python3 get_igc_from_xcontest.py [taskPk]'")
        exit()

    main(sys.argv[1:])
