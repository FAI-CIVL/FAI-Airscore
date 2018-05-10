#!/usr/bin/perl -w
#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2007
#

require DBD::mysql;

require Gap; # qw(:all);
require PWC; # qw(:all);
require RTG; # qw(:all);

use POSIX qw(ceil floor);
use strict;

# Add currect bin directory to @INC
use File::Basename;
use lib '/home/untps52y/perl5/lib/perl5';
use lib dirname (__FILE__) . '/';
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
elsif ($formula->{'class'} eq 'pwc')
{
    print "PWC scoring\n";
    $scr = PWC->new();
}
elsif ($formula->{'class'} eq 'RTG')
{
    print "RTG scoring\n";
    $scr = RTG->new();
}

else
{
    print "Unknown formula class ", $formula->{'class'}, "\n";
    exit 1;
}

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
$task->{'sstopped'} //= 0;
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
$sth = $TrackLib::dbh->prepare("UPDATE 
									tblTask 
								SET 
									tasQuality = '$quality', 
									tasDistQuality = '$dist', 
									tasTimeQuality = '$time', 
									tasLaunchQuality = '$launch', 
									tasStopQuality = '$stop' 
								WHERE 
									tasPk = '$tasPk'");
$sth->execute();
$taskt->{'quality'} = $quality;

if ($taskt->{'pilots'} > 0)
{
    # Now allocate points to pilots ..
    $scr->points_allocation($TrackLib::dbh,$task,$taskt,$formula);
}
