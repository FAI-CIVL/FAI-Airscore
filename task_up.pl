#!/usr/bin/perl

#
# Task is updated - work out what to do.
# 
# Geoff Wong 2007
#

require DBD::mysql;

use POSIX qw(ceil floor);
use Math::Trig;
use Data::Dumper;
use TrackLib qw(:all);

my $dbh;

sub round 
{
    my ($number) = @_;
    return int($number + .5);
}
#
# Find the task totals and update ..
#   tasTotalDistanceFlown, tasPilotsLaunched, tasPilotsTotal
#   tasPilotsGoal, tasPilotsLaunched, 
#
sub task_update
{
    my ($tasPk) = @_;
    my $wpts;
    my $dist;
    my ($totdist,$srdist);
    my $i = 0;
    my $num;
    my (%s1, %s2);

    $totdist = 0.0;
    $srdist = 0.0;
    $task = read_task($tasPk);
    $wpts = $task->{'waypoints'};

    # Ok work out non-optimal distance for now
    # FIX: work out shortest route!
    $num = scalar @$wpts;
    #print "task $tasPk with $num waypoints\n";
    for ($i = 0; $i < $num-1; $i++)
    {
        #print "From ", $wpts->[$i]->{'name'}, "\n";
        $totdist = $totdist + distance($wpts->[$i], $wpts->[$i+1]);

        $s1{'lat'} = $wpts->[$i]->{'short_lat'};
        $s1{'long'} = $wpts->[$i]->{'short_long'};
        $s2{'lat'} = $wpts->[$i+1]->{'short_lat'};
        $s2{'long'} = $wpts->[$i+1]->{'short_long'};
        $srdist = $srdist + distance(\%s1, \%s2);
    }

    # Store it in tblTask
    $sth = $dbh->prepare("update tblTask set tasDistance=$totdist, tasShortRouteDistance=$srdist where tasPk=$tasPk");
    $sth->execute();

    return $totdist;
}

sub track_update
{
    my ($tasPk, $opt) = @_;
    my @tracks;
    my $flag;

    # Now check for pre-submitted tracks ..
    $sth = $dbh->prepare("select traPk from tblComTaskTrack where tasPk=$tasPk");
    $sth->execute();
    $tracks = ();
    $flag = 0;
    while  ($ref = $sth->fetchrow_hashref()) 
    {
        push @tracks, $ref->{'traPk'};
    }

    # Re-optimising pre-submitted tracks against the task
    if ($opt ne '')
    {
        for my $tpk (@tracks)
        {
            print "Re-optimise pre-submitted track: $tpk\n";
            $out = '';
            $retv = 0;
            $out = `${BIN_PATH}optimise_flight.pl $tpk $tasPk $opt`;
            print $out;
        }
    }

    # Now verify the pre-submitted tracks against the task
    for my $tpk (@tracks)
    {
        print "Verifying pre-submitted track: $tpk\n";
        $retv = 0;
        $out = `${BIN_PATH}track_verify_sr.pl $tpk $tasPk`;
        print $out;
        $flag = 1;
    }

    return $flag;
}

#
# Main program here ..
#

my $dist;
my $task;
my $quality;
my $pth;
my $out;

$dbh = db_connect();

$task = $ARGV[0];
$opt = $ARGV[1];

# Work out all the task totals to make it easier later
$dist = task_update($task);
#if (system($BIN_PATH . "short_route.pl $task") == -1)
$pth = $BIN_PATH . 'short_route.pl';
$out = `$pth $task`;
print $out;

if (track_update($task, $opt) == 1)
{
    # tracks re-verified - now rescore.
    $pth = $BIN_PATH . 'task_score.pl';
    $out = `$pth $task`;
    #print $out;
}

#print "Task dist=$dist\n";


