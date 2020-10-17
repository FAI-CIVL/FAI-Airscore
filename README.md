# FAI Airscore

This was originally a fork of Geoff Wong's Airscore (https://github.com/geoffwong/airscore).
It has been ported to python 3.7, it's structure has been completely redesigned and many additional features added.

Web middle layer & front end has been ported to flask/jquery using flask cookie cutter template.

### Features:
GAP based Paragliding and Hang Gliding scoring from IGC files.
- Formulas are defined in script files which makes implementing new variants easy. (current formulas are GAP 2016-2020 and PWC 2016, 17, 19)
- Scorekeeper access to setup competitions and score tasks.
- Competition scoring with task scores and overall scores publishable to public area of website.
- Airspace infringement detection and penalty application
- Interactive tracklog and task maps
- Ability to have an in house database of pilots, waypoints and airspaces for re-use in multiple competitions
- Live leaderboard and scoring from live tracking servers. (e.g. Flymaster)

The GAP rules have changed over the years. Here are the features that
airscore includes or not.

* Scoring Method
    - [ ] GAP
        - [ ] GAP2000
        - [ ] GAP2002
        - [ ] OzGAP2005
        - [ ] GAP2007
        - [ ] GAP2008
        - [ ] GAP2011
        - [ ] GAP2013
        - [ ] GAP2014
        - [ ] GAP2015
        - [ ] GAP2016
        - [ ] GAP2018
        - [ ] GAP2020
    - [ ] PWC (GAP variant)
        - [ ] PWC2007
        - [ ] PWC2008
        - [ ] PWC2009
        - [ ] PWC2011
        - [ ] PWC2012
        - [ ] PWC2013
        - [ ] PWC2014
        - [ ] PWC2015
        - [ ] PWC2016
        - [ ] PWC2017
        - [ ] GAP2019
    - [ ] Linear distance
    - [ ] Time-based scoring (TBS)
* Earth Model
    - [ ] FAI sphere
    - [ ] WGS84 ellipsoid
* Distance Method
    - [ ] Pythagorus on a UTM plane
    - [ ] Haversines on the sphere
    - [ ] Vincenty on the ellipsoid
    - [ ] Andoyer on the ellipsoid
* Type of Task
    - [ ] Race
    - [ ] Elapsed time
    - [ ] Open distance (can be declared but not yet scored)
* Shape of Zone
    - [ ] Cylinder
    - [ ] Inverted cone (can be defined but treated as a cylinder)
* Shape of Goal
    - [ ] Circle
    - [ ] Line
* Final Glide Decelerator
    - [ ] Conical end of speed section (CESS)
    - [ ] Arrival altitude time bonus (AATB)
* Source of Altitude
    - [ ] GPS
    - [ ] Pressure (QNH)
* Validities
    - [ ] Task (day quality)
    - [ ] Launch
    - [ ] Distance
    - [ ] Time
    - [ ] Stop
* Points
    - [ ] Linear distance (reach)
    - [ ] Distance difficulty (effort)
    - [ ] Arrival position
    - [ ] Arrival time
    - [ ] Time (speed)
    - [ ] Leading
    - [ ] Departure
* Leading Area as a Function of Time and Distance Tweaks
    - [ ] Use distance; a = t * d
    - [ ] Use distance squared; a = t * d^2
    - [ ] Use PWCA weighting; a = w(t, d)
* Parameter Tweaks
    - [ ] Day quality override
    - [ ] 1000 points for winner if no pilot made goal
    - [ ] 1000 points for winner before day quality applied
    - [ ] Double leading points weight
    - [ ] Proportional leading points weight if no pilot made goal
    - [ ] Adjustable stopped task bonus glide ratio (fixed at 4:1 for PG and 5:1 for HG)
* Special Cases
    - [ ] End of the speed section but not goal
    - [ ] Early start
    - [ ] Stopped tasks
* Stopped Tasks
    - [ ] Stopped task time as announcement minus score back
    - [ ] Requirements checking, goal or duration
    - [ ] Score time window
    - [ ] Time points for pilots at or after the end of the speed section
    - [ ] Distance points with altitude bonus
* Penalties
    - [ ] Absolute
    - [ ] Fractional
    - [ ] Jump-the-gun factor
    - [ ] Jump-the-gun maximum
* Task Ranking
    - [ ] Overall
    - [ ] Female
    - [ ] Country
* Competition Ranking
    - [ ] Overall
    - [ ] Female
    - [ ] Country
    - [ ] Ties
    - [ ] Fixed Total Validity

### Installation:

#### Database setup
Airscore uses a Mysql database. The database is not included in the docker containers. You will need to setup or use a hosted mysql server.
Once you have the DB server, use the file airscore.sql to create the table and views. Database credentials should be saved in the .env file (see below)

#### Environment and configuration variables
defines.yaml.example and .env.example should be renamed or copied wihout ".example" to create the two config files.
- defines.yaml - folder structure and Airscore configuration - there are several options
- .env contains environment variables used in the docker compose files, database and email server credentials.

## Docker Quickstart

This app should be run completely using `Docker` and `docker-compose`. **Using Docker is recommended, as it guarantees the application is run using compatible versions of Python and Node**.

There are three main services:

To run the development version of the app

```bash
docker-compose -f docker-compose-dev.yml up
```

To run the production version of the app

```bash
docker-compose up

```

The production version uses several containers running together:
- The flask app
- A worker container for background tasks
- Redis (for cache and background processing queue)
- Nginx

A docker volume `node-modules` is created to store NPM packages and is reused across the dev and prod versions of the application. For the purposes of DB testing with `sqlite`, the file `dev.db` is mounted to all containers. This volume mount should be removed from `docker-compose.yml` if a production DB server is used.

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
docker-compose -f docker-compose-dev.yml run --rm manage test
flask test # If running locally without Docker
```

To run the linter, run

```bash
docker-compose -f docker-compose-dev.yml run --rm manage lint
flask lint # If running locally without Docker
```

The `lint` command will attempt to fix any linting/style errors in the code. If you only want to know if the code will pass CI and do not wish for the linter to make changes, add the `--check` argument.

## License
Apart from igc_lib which has a MIT license and bootstrap all rest of the code is provided under the GPL License version 2 described in the file "Copying".

If this is not present please download from www.gnu.org.