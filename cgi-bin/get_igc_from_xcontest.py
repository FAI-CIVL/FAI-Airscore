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


def get_xc_parameters(task_id, test = 0):
    """Get site info and date from database """
    from datetime import datetime

    site_id = 0
    takeoff_id = 0
    datestr = None
    query = """  SELECT
                    R.xccSiteID,
                    R.XccToID,
                    T.tasDate
                FROM
                    tblTaskWaypoint TW
                JOIN tblTask T USING(tasPk)
                JOIN tblRegionWaypoint R USING(rwpPk)
                WHERE
                    T.tasPk = %s AND TW.tawType = 'launch'"""
    params = [task_id]
    with Database() as db:
        q = db.fetchone(query, params)
        if q is not None:
            site_id = q['xccSiteID']
            takeoff_id = q['XccToID']
            date = q['tasDate']
            logging.info("site_id:%s takeoff_id:%s date:%s", site_id, takeoff_id, date)
            datestr = date.strftime('%Y-%m-%d') #convert from datetime to string
        else:
            print('Error: no site found for the task')
    return(site_id, takeoff_id, datestr)

# def get_server_parameters(test = 0):
#     import yaml, os
#
#     abspath = os.path.abspath(__file__)
#     dname = os.path.dirname(abspath)
#     os.chdir(dname)
#     with open('xcontest.yaml', 'rb') as f:
#             """use safe_load instead load"""
#             config = yaml.safe_load(f)
#
#     login_name = config['xc']['User']  # mysql db user
#     password = config['xc']['Pass']  # mysql db password
#     server = config['xc']['Server'] # mysql host name

def get_zip(site_id, takeoff_id, date, login_name, password, zip_destination, zip_name, test = 0):
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

    ##extract files
    # with zipfile.ZipFile(zip_destination+zip_name) as zf:
    #     zf.extractall(zip_destination)

# def import_tracks(mytracks, task, f):
#     """Import tracks in db"""
#     message = ''
#     result = ''
#     for track in mytracks:
#         """adding track to db"""
#         import_track(track, test)
#         """checking track against task"""
#         verify_track(track, task, f)
#
#     if test == 1:
#         """TEST MODE"""
#         print (message)
#
#     return result

def main():
    from trackUtils import extract_tracks, get_tracks, assign_and_import_tracks
    from tempfile import TemporaryDirectory
    import Defines

    """Main module"""
    test = 0
    result = ''
    """check parameter is good."""
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        """Get tasPk"""
        task_id = 0 + int(sys.argv[1])
        if len(sys.argv) > 2:
            """Test Mode"""
            print('Running in TEST MODE')
            test = 1

        """Get Task object"""
        task = Task.read_task(task_id)
        if task.ShortRouteDistance == 0:
            print('task not optimised.. optimising')
            task.calculate_optimised_task_length()

        if task.comPk > 0:
            """get zipfile from XContest server"""
            site_id, takeoff_id, date = get_xc_parameters(task_id, test)
            login_name = Defines.XC_LOGIN
            password = Defines.XC_password
            zip_name = 'igc_from_xc.zip'

            formula =  read_formula(task.comPk)
            f = For.get_formula_lib(formula)

            """create a temp dire for zip file"""
            with TemporaryDirectory() as zip_destination:
                get_zip(site_id, takeoff_id, date, login_name, password, zip_destination, zip_name, test = 0)
                """create a temporary directory for tracks"""
                zipfile = zip_destination + '/' + zip_name
                with TemporaryDirectory() as tracksdir:
                    error = extract_tracks(zipfile, tracksdir, test)
                    if not error:
                        """find valid tracks"""
                        tracks = get_tracks(tracksdir, test)
                        if tracks is not None:
                            """associate tracks to pilots and import"""
                            assign_and_import_tracks(tracks, task, xcontest=True, test=0)
                        else:
                            result = ("There is no valid track in zipfile {} \n".format(zipfile))
                    else:
                        result = ("An error occured while dealing with file {} \n".format(zipfile))
        else:
            result = ("error: task ID {} does NOT belong to any Competition \n".format(task.tasPk))

    else:
        print('error: Use: python3 get_igc_from_xcontest.py [taskPk] [opt. test]')

    print (result)

if __name__ == "__main__":
    main()
