#!/usr/bin/perl -w
#
# pilot# igc task
#
require DBD::mysql;

use Time::Local;
use Data::Dumper;

# Add currect bin directory to @INC
use File::Basename;
# use lib '/home/ubuntu/perl5/lib/perl5';
use lib dirname(__FILE__) . '/';
use TrackLib qw(:all);
#use strict;

my $traPk = 0;
my $traStart;
my $tasType;
my $comType;
my $dbh;
my $sql;
my $sth;
my $ref;
my $res;
my $ex;
my ($glider,$cert);
my ($comFrom, $comTo);

my $pilPk = 0;
my $igc = $ARGV[1];
my $comPk = 0;
my $tasPk = 0;

# if (scalar(@ARGV) < 2)
# {
#     print "add_track.pl <pilPk> <igcfile> <comPk> <tasPk>\n";
#     exit(1);
# }

$igc='/web/dev/airscore/tracks/2019/lega19_1/lega19_1_t1_20190309/antonio_golfari_20190329_150319_1.igc';
$pilPk = 66 ;

$dbh = db_connect();

# Load the track 
$res = `${BINDIR}igcreader.pl $igc $pilPk`;
$ex = $?;
print $res;
if ($ex > 0)
{
    print $res;
    exit(1);
}

# Parse for traPk ..
if ($res =~ m/traPk=(.*)/)
{
    $traPk = $1;
}

if (0+$traPk < 1)
{
    print "Unable to determine new track key: $res<br>\n";
    exit(1);
}

print 'track= '.$traPk;
