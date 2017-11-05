Adapting Airscore for use in the Italian League.
# airScore


A bunch of scripts and php pages to handle IGC files and store them into a mysql database, determine track distance, 
do paragliding GAP RACE scoring, OLC-style scoring, etc. It also presents tracks on Google Maps for further viewing.

The basic philosophy is to provide the scoring tools as a set of simple executable (perl scripts)
that can be wrapped with any GUI. At this stage I've only provided a basic PHP/Google Maps  interface. 

The database schema maybe found in xcdb.sql.

### Copyright

With the exception of the following code:

einsert.js (http://econym.googlepages.com - copyright Mike Williams)
elabel.js  (http://econym.googlepages.com - copyright Mike Williams)
Simple.pm (http://search.cpan.org/~grantm/XML-Simple-2.20/lib/XML/Simple.pm 
    - copyright Grant McLean distributed under GPL License version 2)

All rest of the code is provided under the GPL License version 2 
described in the file "Copying".

If this is not present please download from www.gnu.org.

Geoff Wong, 2007-2016
geoff.wong@gmail.com


## Installation

Helps to be experienced with Apache configurations and Mysql.

* Edit the "Makefile":
    - set the mysql password you want to use for airscore
    - set your CGI bin directory
    - set your HTDOCS location (for the php files)
* 'make database' if it's your first installation
* Type 'make'
* Ensure Apache is configured with mod-php, perl should be available too
* Test that the login page work .../airscore/login.php (user: admin, pass: admin)


Other packages needed:

* php5
* mysql
* perl
* libxml-simple-perl

### Web Security

* Enable exec() functionality for php.
* Enable CGI (*pl *php) from the main installation directory for Apache

## Script Notes

What do the perl scripts do:

* add_track.pl - adds an IGC track to the database
* airgain_verify.pl - verify an 'airgain' task (collecting points in the region)
* airspace_check.pl - check airpsace for a task
* airspace_openair.pl - read in an Openair format airspace file 
* airspace_sua_reader.pl - read in a SUA format airspace file
* bulk_igc_reader.pl - read in a bunch of IGC files
* bulk_pilot_import.pl - import pilot information from a CSV file
* del_track.pl - delete a track
* fsdb_export.pl - export to FS XML format (not fully functional)
* fsdb_import.pl - import a FS XML format file (not fully functional)
* handicap.pl - local handicap calculation
* igcreader.pl - read an IGC file
* igcr_nostrip.pl - read an IGC without doing a 'no-flying' strip
* optimise_flight.pl - do an OLC optimisation on a flight
* short_route.pl - compute the shortest-route through a task
* task_score.pl - score a task
* task_up.pl - re-verify all tracks assocaited with a task, and re-score it
* team_score.pl - team scoring stuff
* track_verify_sr.pl - verify an indivudal track against a task

