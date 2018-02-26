#!/usr/bin/perl -I/home/geoff/bin

#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2007
#

require DBD::mysql;
require Gap; # qw(:all);
require OzGap; # qw(:all);
require NoGap; # qw(:all);
require Nzl; # qw(:all);
require JTGap; # qw(:all);
require GGap; # qw(:all);
require RTGap; # qw(:all);
require PWC; # qw(:all);

use POSIX qw(ceil floor);
use strict;

# Add currect bin directory to @INC
use lib '/var/www/cgi-bin';
use TrackLib qw(:all);

#
# Main program here ..
#

my $taskt;
my $task;
my $tasPk;
my $formula;
my $quality;
my $scr;
my $sth;
my $sql;
my ($dist,$time,$launch,$stop);

$TrackLib::dbh = db_connect();

# Get the tasPk 
$tasPk = $ARGV[0];

# Read the task itself ..
$task = read_task($tasPk);

# Read the formula 
$formula = read_formula($task->{'comPk'});

print Dumper($formula);

# Now create the appropriate scoring object ...
if ($formula->{'class'} eq 'gap')
{
    print "GAP scoring\n";
    $scr = Gap->new();
}
elsif ($formula->{'class'} eq 'ozgap')
{
    print "OzGAP scoring\n";
    $scr = OzGap->new();
}
elsif ($formula->{'class'} eq 'nzl')
{
    print "NZL scoring\n";
    $scr = Nzl->new();
}
elsif ($formula->{'class'} eq 'nogap')
{
    print "NoGap scoring\n";
    $scr = NoGap->new();
}
elsif ($formula->{'class'} eq 'jtgap')
{
    print "JTGap scoring\n";
    $scr = JTGap->new();
}
elsif ($formula->{'class'} eq 'ggap')
{
    print "GGap scoring\n";
    $scr = GGap->new();
}
elsif ($formula->{'class'} eq 'rtgap')
{
    print "RTGap scoring\n";
    $scr = RTGap->new();
}
elsif ($formula->{'class'} eq 'pwc')
{
    print "PWC scoring\n";
    $scr = PWC->new();
}
else
{
    print "Unknown formula class ", $formula->{'class'}, "\n";
    exit 1;
}

# Work out all the task totals from task results, must return 
# at least the followint:
#    $taskt->{'pilots'}
#    $taskt->{'maxdist'}
#    $taskt->{'distance'}
#    $taskt->{'launched'} 
#    $taskt->{'goal'} 
#    $taskt->{'fastest'} 
#    $taskt->{'firstdepart'} 
#    $taskt->{'firstarrival'}
#    $taskt->{'mincoeff'}

$taskt = $scr->task_totals($TrackLib::dbh,$task,$formula);

# Store it in tblTask
$sql = "update tblTask set tasTotalDistanceFlown=" . $taskt->{'distance'} . 
			", tasTotDistOverMin=" . $taskt->{'distovermin'} . 
            ", tasPilotsTotal=" . $taskt->{'pilots'} . 
            ", tasPilotsLaunched=" . $taskt->{'launched'} . 
            ", tasPilotsGoal=" . $taskt->{'goal'} . 
            ", tasFastestTime=" . $taskt->{'fastest'} . 
            ", tasMaxDistance=" . $taskt->{'maxdist'} . 
       " where tasPk=$tasPk";

#print $sql;
$sth = $TrackLib::dbh->prepare($sql);
$sth->execute();

# Work out the quality factors (distance, time, launch)

($dist,$time,$launch, $stop) = $scr->day_quality($taskt, $formula);

# Check if task was stopped - No idea if this is done elsewhere, but without broke PWC.pm
if ( $task->{'sstopped'} > 0 )
{
	$quality = $dist * $time * $launch * $stop;
}
else
{
	$quality = $dist * $time * $launch;
}
print "-- TASK_SCORE -- distQ = $dist | timeQ = $time | launchQ = $launch | stopQ = $stop \n";
print "-- TASK_SCORE -- Day Quality = $quality \n";
if ($quality > 1.0)
{
    $quality = 1.0;
}
$sth = $TrackLib::dbh->prepare("UPDATE tblTask SET tasQuality='$quality', tasDistQuality='$dist', tasTimeQuality='$time', tasLaunchQuality='$launch', tasStopQuality='$stop' WHERE tasPk='$tasPk' ");
$sth->execute();
$taskt->{'quality'} = $quality;

if ($taskt->{'pilots'} > 0)
{
    # Now allocate points to pilots ..
    $scr->points_allocation($TrackLib::dbh,$task,$taskt,$formula);
}

