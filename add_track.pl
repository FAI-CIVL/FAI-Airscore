#!/usr/bin/perl
#
# pilot# igc task
#
require DBD::mysql;

use Time::Local;
use Data::Dumper;

use TrackLib qw(:all);
#use strict;

my ($pil,$igc,$comPk);
my $tasPk;
my $traPk;
my $tasType;
my $comType;
my $pilPk;
my $dbh;
my $sql;
my $sth;
my $ref;
my $res;
my ($glider,$dhv);

$pil = $ARGV[0];
$igc = $ARGV[1];
$comPk = 0 + $ARGV[2];
$tasPk = 0 + $ARGV[3];


if (scalar(@ARGV) < 2)
{
    print "add_track.pl <hgfa#> <igcfile> <comPk> [tasPk]\n";
    exit(1);
}

$dbh = db_connect();

# Find the pilPk
if (0 + $pil > 0)
{
    $sql = "select * from tblPilot where pilHGFA='$pil' or pilCIVL='$pil'";
}
else
{
    # Guess on last name ...
    $sql = "select * from tblPilot where pilLastName='$pil' order by pilPk desc";
}
$sth = $dbh->prepare($sql);
$sth->execute();
if ($sth->rows() > 1)
{
    print "Pilot ambiguity for $pil, use pilot HGFA/FAI#\n";
    while  ($ref = $sth->fetchrow_hashref())
    {
        print $ref->{'pilHGFA'}, " ", $ref->{'pilFirstName'}, " ", $ref->{'pilLastName'}, " ", $ref->{'pilBirthdate'}, "\n";
    }
    exit(1);
}
if ($ref = $sth->fetchrow_hashref())
{   
    $pilPk = $ref->{'pilPk'};
}
else
{
    print "Unable to identify pilot: $pil\n";
    exit(1);
}


# get last track info
$sql = "select traGlider, traDHV from tblTrack where pilPk=$pilPk order by traPk desc";
$sth = $dbh->prepare($sql);
$sth->execute();
if  ($ref = $sth->fetchrow_hashref())
{
    $glider = $ref->{'traGlider'};
    $dhv = $ref->{'traDHV'};
}
else
{
    $glider = 'Unknown';
}


# Load the track 
$res = `${BIN_PATH}igcreader.pl $igc $pilPk`;

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

# FIX: Copy the track somewhere permanent?
# FIX: Update tblTrack to point to that

$sql = "update tblTrack set traGlider='$glider', traDHV='$dhv' where traPk=$traPk";
$dbh->do($sql);

# Try to find an associated task if not specified
if ($tasPk == 0)
{
    $sql = "select T.tasPk, T.tasTaskType, C.comType from tblTask T, tblTrack TL, tblCompetition C where C.comPk=T.comPk and T.comPk=$comPk and TL.traPk=$traPk and TL.traStart > date_sub(T.tasStartTime, interval C.comTimeOffset hour) and TL.traStart < date_sub(T.tasFinishTime, interval C.comTimeOffset hour)";
    $sth = $dbh->prepare($sql);
    $sth->execute();
    if  ($ref = $sth->fetchrow_hashref())
    {
        $tasPk = $ref->{'tasPk'};
        $tasType = $ref->{'tasTaskType'};
        $comType = $ref->{'comType'};
    }
}
else
{
    # For routes
    #print "Task pk: $tasPk\n";
    $sql = "select T.tasTaskType, C.comType from tblTask T, tblCompetition C where C.comPk=T.comPk and T.tasPk=$tasPk";
    $sth = $dbh->prepare($sql);
    $sth->execute();
    if  ($ref = $sth->fetchrow_hashref())
    {
        #print Dumper($ref);
        $tasType = $ref->{'tasTaskType'};
        $comType = $ref->{'comType'};
    }
    else
    {
        print "Unable to get task type\n";
    }
}


if ($tasPk > 0)
{
    print "Task type: $tasType\n";
    # insert into tblComTaskTrack
    $sql = "insert into tblComTaskTrack (comPk,tasPk,traPk) values ($comPk,$tasPk,$traPk)";
    #print "add track=$sql\n";
    $dbh->do($sql);

    if (($tasType eq 'free') or ($tasType eq 'olc'))
    {
        `${BIN_PATH}optimise_flight.pl $traPk $tasPk 0`;
        # also verify for optional points in 'free' task?
    }
    elsif ($tasType eq 'airgain')
    {
        `${BIN_PATH}optimise_flight.pl $traPk $tasPk 3`;
        `${BIN_PATH}airgain_verify.pl $traPk $comPk $tasPk`;
    }
    elsif ($tasType eq 'speedrun' or $tasType eq 'race' or $tasType eq 'speedrun-interval')
    {
        # Optional really ...
        `${BIN_PATH}optimise_flight.pl $traPk $tasPk 3`;
        print "${BIN_PATH}track_verify_sr.pl $traPk $tasPk\n";
        `${BIN_PATH}track_verify_sr.pl $traPk $tasPk`;
    }
    else
    {
        print "Unknown task $tasType\n";
    }
}
else
{
    $sql = "insert into tblComTaskTrack (comPk,traPk) values ($comPk,$traPk)";
    #print "add track=$sql\n";
    $dbh->do($sql);
    # Nothing else to do but verify ...
    # FIX: should optimise differently for different comp types
    if ($comType eq 'Free')
    {
        `${BIN_PATH}optimise_flight.pl $traPk 0 0`;
    }
    else
    {
        `${BIN_PATH}optimise_flight.pl $traPk`;
    }
}

# stored track pk
print "traPk=$traPk\n";

