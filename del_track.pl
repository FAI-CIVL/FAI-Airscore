#!/usr/bin/perl
#
# pilot# igc task
#
require DBD::mysql;

#use Data::Dumper;
use TrackLib qw(:all);
use Defines qw(:all);
#use strict;

my $traPk;

if (scalar(@ARGV) < 1)
{
    print "del_track.pl <traPk#>\n";
    exit(1);
}

$traPk = 0 + $ARGV[0];
$dbh = db_connect();

if ($traPk < 1)
{
    print "del_track.pl <traPk#>\n";
    exit(1);
}


$dbh->do("delete from tblTaskResult where traPk=$traPk");

$dbh->do("delete from tblTrack where traPk=$traPk");

$dbh->do("delete from tblTrackLog where traPk=$traPk");

$dbh->do("delete from tblWaypoint where traPk=$traPk");

$dbh->do("delete from tblBucket where traPk=$traPk");

$dbh->do("delete from tblTrackMarker where traPk=$traPk");

$dbh->do("delete from tblComTaskTrack where traPk=$traPk");

#$query = "delete from tblComTaskTrack where traPk=$id$comcl";

print "Deleted track $traPk\n";

