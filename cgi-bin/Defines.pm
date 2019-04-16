#!/usr/bin/perl -w
#
# Some defines
#
use File::Basename;
use Cwd 'abs_path';


*BINDIR = \'/web/dev/airscore/cgi-bin/';
#*BINDIR = \dirname(abs_path($0)) . '/';
#*BINDIR = \ dirname(__FILE__);
*FILEDIR = \'/web/dev/airscore/tracks/';
*DATABASE = \'airscore_dev';
*MYSQLHOST = \'mysql.legapiloti.dreamhosters.com';
*MYSQLUSER = \'airscore_db';
*MYSQLPASSWORD = \'Tantobuchi01';

1;
