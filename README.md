# Airscore - python port

A fork of Geoff Wongs airscore (https://github.com/geoffwong/airscore).

Please see his readme.

Backend scripts ported to python 3.6

Web middle layer & front end currently being ported to flask/jquery using flask cookie cutter. work in progress 


### Installation:

see docker quickstart below


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

## Docker Quickstart

This app can be run completely using `Docker` and `docker-compose`. **Using Docker is recommended, as it guarantees the application is run using compatible versions of Python and Node**.

There are three main services:

To run the development version of the app

```bash
docker-compose up flask-dev
```

To run the production version of the app

```bash
docker-compose up flask-prod
```

The list of `environment:` variables in the `docker-compose.yml` file takes precedence over any variables specified in `.env`.

To run any commands using the `Flask CLI`

```bash
docker-compose run --rm manage <<COMMAND>>
```

Therefore, to initialize a database you would run

```bash
docker-compose run --rm manage db init
docker-compose run --rm manage db migrate
docker-compose run --rm manage db upgrade
```

A docker volume `node-modules` is created to store NPM packages and is reused across the dev and prod versions of the application. For the purposes of DB testing with `sqlite`, the file `dev.db` is mounted to all containers. This volume mount should be removed from `docker-compose.yml` if a production DB server is used.

### Running locally

Run the following commands to bootstrap your environment if you are unable to run the application using Docker

```bash
cd airscore
pip install -r requirements/dev.txt
npm install
npm start  # run the webpack dev server and flask server using concurrently
```

You will see a pretty welcome screen.

#### Database Initialization (locally)

Once you have installed your DBMS, run the following to create your app's
database tables and perform the initial migration

```bash
flask db init
flask db migrate
flask db upgrade
```

## Deployment

When using Docker, reasonable production defaults are set in `docker-compose.yml`

```text
FLASK_ENV=production
FLASK_DEBUG=0
```

Therefore, starting the app in "production" mode is as simple as

```bash
docker-compose up flask-prod
```

If running without Docker

```bash
export FLASK_ENV=production
export FLASK_DEBUG=0
export DATABASE_URL="<YOUR DATABASE URL>"
npm run build   # build assets with webpack
flask run       # start the flask server
```

## Shell

To open the interactive shell, run

```bash
docker-compose run --rm manage db shell
flask shell # If running locally without Docker
```

By default, you will have access to the flask `app`.

## Running Tests/Linter

To run all tests, run

```bash
docker-compose run --rm manage test
flask test # If running locally without Docker
```

To run the linter, run

```bash
docker-compose run --rm manage lint
flask lint # If running locally without Docker
```

The `lint` command will attempt to fix any linting/style errors in the code. If you only want to know if the code will pass CI and do not wish for the linter to make changes, add the `--check` argument.

## Migrations

Whenever a database migration needs to be made. Run the following commands

```bash
docker-compose run --rm manage db migrate
flask db migrate # If running locally without Docker
```

This will generate a new migration script. Then run

```bash
docker-compose run --rm manage db upgrade
flask db upgrade # If running locally without Docker
```

To apply the migration.

For a full migration command reference, run `docker-compose run --rm manage db --help`.

If you will deploy your application remotely (e.g on Heroku) you should add the `migrations` folder to version control.
You can do this after `flask db migrate` by running the following commands

```bash
git add migrations/*
git commit -m "Add migrations"
```

Make sure folder `migrations/versions` is not empty.

## Asset Management

Files placed inside the `assets` directory and its subdirectories
(excluding `js` and `css`) will be copied by webpack's
`file-loader` into the `static/build` directory. In production, the plugin
`Flask-Static-Digest` zips the webpack content and tags them with a MD5 hash.
As a result, you must use the `static_url_for` function when including static content,
as it resolves the correct file name, including the MD5 hash.
For example

```html
<link rel="shortcut icon" href="{{static_url_for('static', filename='build/img/favicon.ico') }}">
```

If all of your static files are managed this way, then their filenames will change whenever their
contents do, and you can ask Flask to tell web browsers that they
should cache all your assets forever by including the following line
in ``.env``:

```text
SEND_FILE_MAX_AGE_DEFAULT=31556926  # one year
```
