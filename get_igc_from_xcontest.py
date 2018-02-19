'''Dependancies I had to install on AWS server:
sudo apt install python-pip
pip install mysqlclient
sudo apt-get install python3-lxml

needs to be run with python3.
i.e. 
python3 get_igc_from_xcontest.py <tasPk>
'''

import requests
import lxml.html
import time
import logging
import zipfile
import MySQLdb
import subprocess
import os
import sys
import shutil


def get_missing_tracks_list(task_id, DB_User, DB_Password, DB):
    """Get pilot details (pilots in task without tracks) 
    returns a dictionary of pilXcontestUser:pilPK."""

    db = MySQLdb.connect(user=DB_User, passwd=DB_Password, db=DB)
    c = db.cursor()

    c.execute("SELECT pilXcontestUser, p.pilHGFA FROM tblPilot p "
              "join tblCompPilot b on p.pilPk = b.pilPk left outer join "
              "(SELECT comPk, tasPk, c.traPk, pilPk FROM tblComTaskTrack c "
              "join tblTrack t on c.traPk = t.traPk where tasPk= %s) as a "
              "on b.pilPk = a.pilPK and b.comPk = a.comPk "
              "where pilXcontestUser is NOT null and a.traPk is null",
              (task_id,))

    pilot_list = dict((xc, pilpk) for xc, pilpk in c.fetchall())
    return pilot_list


def get_xc_parameters(task_id, DB_User, DB_Password, DB):
    """Get site info and date from database """

    db = MySQLdb.connect(user=DB_User, passwd=DB_Password, db=DB)
    c = db.cursor()

    c.execute("SELECT rwpXcSite_id, rwpXcTakeoff_id, tasDate FROM "
              "tblTaskWaypoint JOIN tblTask ON tblTaskWaypoint.tasPk = "
              "tblTask.tasPk JOIN tblRegionWaypoint ON "
              "tblRegionWaypoint.rwpPk = tblTaskWaypoint.rwpPk WHERE "
              "tblTask.tasPk =%s AND tawType = 'start'", (task_id,))

    site_id, takeoff_id, date = c.fetchone()
    logging.info("site_id:%s takeoff_id:%s date:%s", site_id, takeoff_id, date)
    datestr = date.strftime('%Y-%m-%d')  # convert from datetime to string
    return(site_id, takeoff_id, datestr)


def get_zip(site_id, takeoff_id, date, login_name, password, zip_destination, zip_name):
    """Get the zip of igc files from xcontest."""

    # determine if we have takeoff id or only site id. preferable to use more
    # specific takeoff id.
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
    response = s.get('https://www.xcontest.org/util/igc.archive.comp.php?date=%s&%s=%s' %
                     (date, site_launch, location_id))

    if "No error" in response.text:
        logging.info(
            "logged into xcontest and igc.archive.comp.php running with no error")
    else:
        logging.error("igc.archive.comp.php not returing as expected")
        logging.error("web page output:\n %s", response.text)
    webpage = lxml.html.fromstring(response.content)
    zfile = requests.get(webpage.xpath('//a/@href')[0])

    # save the file
    with open(zip_destination + zip_name, 'wb') as f:
        f.write(zfile.content)

    # extract files
    with zipfile.ZipFile(zip_destination + zip_name) as zf:
        zf.extractall(zip_destination)


def submit_tracks(task_id, zip_for_submit_name, script_dir):
    """Call the bulk_igc_reader.pl script"""
    pipe = subprocess.run(["perl", "bulk_igc_reader.pl", task_id,
                           zip_for_submit_name], stdout=subprocess.PIPE, cwd=script_dir)
    logging.info("bulk_igc_reader ran")
    logging.info(pipe)


def search_and_zip_files(directory, pilot_list, zip_directory, zip_for_submit_name):
    """Finds theigc files we want, if they are there, 
    changes their names and zips them ready for submission"""
    files_to_submit = []
    pilots_to_submit = []
    for pilot in pilot_list:
        for filename in os.listdir(directory):
            if filename.upper().endswith(".IGC"):
                # split up the filename into parts (dot "." is the separator)
                name_split = filename.split(".")
                # count the pieces
                name_elements = len(name_split)

                # delete first 2 elements (name, surname) and last 3 (date,
                # time, .igc) leaving just username. (even if username has a
                # dot in middle)
                del name_split[name_elements - 1]
                del name_split[name_elements - 2]
                del name_split[name_elements - 3]
                del name_split[1]
                del name_split[0]
                # join up username (if more than one element i.e. it had a dot
                # in it)
                name_split = ".".join(name_split)
                if pilot == name_split:
                    # rename file to hfga.igc
                    logging.info("found pilot: %s" % pilot)
                    newname = str(pilot_list[pilot]) + ".igc"
                    shutil.copy(directory + filename, zip_directory)
                    logging.info("copied %s to %s", directory +
                                 filename, zip_directory)
                    os.rename(zip_directory + filename,
                              zip_directory + newname)
                    files_to_submit.append(newname)
                    pilots_to_submit.append(pilot)
                    break

    # did we find anything?
    if len(files_to_submit) == 0:
        logging.info("No relevant tracks found.")
        return 0

    zip_files(zip_directory, files_to_submit,
              zip_directory, zip_for_submit_name)
    return pilots_to_submit


def zip_files(file_directory, filelist, zip_directory, zip_for_submit_name):
    """Zips up the files"""
    with zipfile.ZipFile(zip_directory + zip_for_submit_name, 'w') as myzip:
        for file in filelist:
            myzip.write(file_directory + file, file)


def delete_igc_zip(directory):
    """Deletes all zip and igc files from a directory"""
    for filename in os.listdir(directory):
        if filename.upper().endswith(".IGC") or filename.upper().endswith(".ZIP"):
            os.remove(directory + filename)


def main():
    """Main module. Takes tasPk as parameter"""
    DB_User = 'XXXXX'  # mysql db user
    DB_Password = 'XXXXX'  # mysql db password
    DB = 'xcdb'  # mysql db name
    login_name = 'XXXXX'  # xcontest login
    password = 'XXXXX'  # xcontest password
    task_id = 0
    xc_zip_destination = '/var/www/xcontest/'
    zip_name = 'igc-from_xc.zip'
    submit_zip_directory = '/var/www/xcontest/to_import/'
    zip_for_submit_name = 'submit.zip'
    script_dir = "/var/www/cgi-bin"

    logging.basicConfig(filename=xc_zip_destination + 'xcontest.log',
                        level=logging.INFO, format='%(asctime)s %(message)s')

    # check parameter is good.
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        task_id = sys.argv[1]
    else:
        logging.error("number of arguments != 1 and/or task_id not a number")
        print("number of arguments != 1 and/or task_id not a number")
        exit()

    # clean up from last time.. could do this at the end but perhaps good for
    # debugging
    delete_igc_zip(xc_zip_destination)
    delete_igc_zip(submit_zip_directory)

    pilot_list = get_missing_tracks_list(task_id, DB_User, DB_Password, DB)
    if len(pilot_list) == 0:
        logging.info("No pilots to get")
        exit()

    site_id, takeoff_id, date = get_xc_parameters(
        task_id, DB_User, DB_Password, DB)
    get_zip(site_id, takeoff_id, date, login_name,
            password, xc_zip_destination, zip_name)

    if search_and_zip_files(xc_zip_destination, pilot_list, submit_zip_directory, zip_for_submit_name):
        submit_tracks(task_id, submit_zip_directory +
                      zip_for_submit_name, script_dir)

if __name__ == "__main__":
    main()
