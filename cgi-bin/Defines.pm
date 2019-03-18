#!/usr/bin/perl -w
#
# Some defines
#
use File::Basename;
use Cwd 'abs_path';


*BINDIR = \'/web/stag/airscore/cgi-bin/';
#*BINDIR = \dirname(abs_path($0)) . '/';
#*BINDIR = \ dirname(__FILE__);
*FILEDIR = \'/web/stag/airscore/tracks/';
*DATABASE = \'airscore_stag';
*MYSQLHOST = \'mysql.legapiloti.dreamhosters.com';
*MYSQLUSER = \'airscore_db';
*MYSQLPASSWORD = \'Tantobuchi01';

1;
