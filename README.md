# Airscore - python port

A fork of Geoff Wongs airscore (https://github.com/geoffwong/airscore).

Please see his readme.

Backend scripts ported to python 3.6

At the moment these scripts are run via PHP execute which is largely the original PHP from Geoff's project as of 2017.

### Installation:

The easiest way is to use the docker files located here: (https://github.com/kuaka/airscore_docker)

TODO: provide latest DB build script


### Main scripts:

#### Library files
- track.py - Contains Track class definition. Reads IGC files using igc_lib library and creates a Track object.
- flight_result.py - Contains Flight_result class definition. This evaluates a Track against a Task. Calculates start time, distance flown, lead co-efficient, goal time etc.
- route.py - contains low level functions for distance calculations
- result.py - contains Task_result class and Comp_result class
- trackUtils.py - Module for operations on tracks. importing, assigning to pilots etc
- calcUtils.py - Date abd time calcs
- task.py - contains Task class get_task_json and write_task_json - json files for task map
- region.py - Region object Definition (waypoint management)
- compUtils.py - Module for operations on comp / task / formulas
- trackDB.py - Read a formula from DB
- formula.py - contains Formula class, reads formula from definition file in folder formulas (pwc, gap etc)
- myconn.py - Database class for DB connection
- mapUtils.py - bounding box for map
- design_map.py - Creates leaflet/folium map from track GeoJSON and Task Definition JSON
- kml.py - KML track files reader
- fsdb.py - FSDB Object - used to read and create fsdb files (FSComp)
------------------------
- igc_lib.py - IGC parsing and validation. Also thermal detection and analysis. Project is [here](https://github.com/xiadz/igc_lib) should eventually be installed via pip or similar. (MIT License)
------------------------
#### environment variables
- Defines.py - Reads defines.yaml file
- defines.yaml - environment variables, DB connection info, folder structure, logins etc
- logger.py - log file setup

#### executable scripts
    these can be run from the command line and are run via PHP in web interface. Will be replaced/absorbed into Flask
- email_pilots.py - Send a reminder email to pilots who have not uploaded a track. Not currently used.
- bulk_igc_reader.py - Reads in a zip file full of .igc files
- score_task.py - Script to score a task.
- track_reader.py - Reads a track file
- bulk_pilot_import.py - Reads in a CSV membership list
- get_igc_from_xcontest.py - pulls down tracks from Xcontest (needs xcontest login)
- set_pilot_status.py - Script to set a pilot ABS, Min.Dist. or DNF.
- update_task.py - Script to calculate task distances, optimised and non optimised and write to the DB
- create_task_result.py - Script to create a task result JSON file, and create the row in database
- import_xctrack_task.py - Scrpit to import task def from xctrack file
- task_full_rescore_test.py - Reprocess all igc files and rescore a task. unfinished WIP
- del_result.py - Delete Task / Comp Result JSON file and all references in result tables
- del_track.py - Delete track and all references in other tables
- update_result_status.py - Update Task / Comp Result status in JSON file and in database

## License
Apart from igc_lib which has a MIT license and bootstrap all rest of the code is provided under the GPL License version 2 described in the file "Copying".

If this is not present please download from www.gnu.org.
