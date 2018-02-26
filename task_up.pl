#!/usr/bin/perl -I/home/geoff/bin

#
# Task is updated - work out what to do.
# 
# Geoff Wong 2007
#

require DBD::mysql;

use POSIX qw(ceil floor);
#use Data::Dumper;
use warnings;

my $dbh;

#
# Find the task totals and update ..
#   tasTotalDistanceFlown, tasPilotsLaunched, tasPilotsTotal
#   tasPilotsGoal, tasPilotsLaunched, 
#
sub task_update
{
    my ($task) = @_;
    my $tasPk;
    my $comPk;
    my $wpts;
    my $dist;
    my ($totdist,$srdist,$ssdist);
    my $i = 0;
    my $essflag = 0;
    my $num;
    my (%s1, %s2);

    $totdist = 0.0;
    $srdist = 0.0;
    $ssdist = 0.0;
    $wpts = $task->{'waypoints'};
    $tasPk = $task->{'tasPk'};
    $comPk = $task->{'comPk'};

    # Ok work out non-optimal distance for now
    # FIX: work out shortest route!
    $num = scalar @$wpts;
    #print "task $tasPk with $num waypoints\n";
    for ($i = 0; $i < $num-1; $i++)
    {
        #print "From ", $wpts->[$i]->{'name'}, "\n";
        $totdist = $totdist + distance($wpts->[$i], $wpts->[$i+1]);
        if ($wpts->[$i]->{'type'} eq 'speed')
        {
            if ($wpts->[$i]->{'how'} eq 'exit' && $srdist == 0)
            {
                $ssdist = - $wpts->[$i]->{'radius'};
            }
            else
            {
                $ssdist = - $srdist;
            }
        }
        elsif ($wpts->[$i]->{'type'} eq 'endspeed')
        {
            $essflag = 1;
        }

        $s1{'lat'} = $wpts->[$i]->{'short_lat'};
        $s1{'long'} = $wpts->[$i]->{'short_long'};
        $s2{'lat'} = $wpts->[$i+1]->{'short_lat'};
        $s2{'long'} = $wpts->[$i+1]->{'short_long'};
        $srdist = $srdist + distance(\%s1, \%s2);
        if ($essflag == 0)
        {
            $ssdist = $ssdist + distance(\%s1, \%s2);
        }
    }

    # Store it in tblTask
    print("update tblTask set tasDistance=$totdist, tasShortRouteDistance=$srdist, tasSSDistance=$ssdist where tasPk=$tasPk");
    $sth = $dbh->prepare("update tblTask set tasDistance=$totdist, tasShortRouteDistance=$srdist, tasSSDistance=$ssdist where tasPk=$tasPk");
    $sth->execute();

    return $totdist;
}

sub track_update
{
    my ($task, $opt) = @_;
    my @tracks;
    my $flag;
    my $tasPk;
    my $comPk;

    $tasPk = $task->{'tasPk'};
    $comPk = $task->{'comPk'};
    # Now check for pre-submitted tracks ..
    $sth = $dbh->prepare("select traPk from tblComTaskTrack where tasPk=$tasPk");
    $sth->execute();
    @tracks = ();
    $flag = 0;
    while  ($ref = $sth->fetchrow_hashref()) 
    {
        push @tracks, $ref->{'traPk'};
    }

    # Re-optimising pre-submitted tracks against the task
    if( (defined $opt) and ($opt ne ''))
    {
        for my $tpk (@tracks)
        {
            print "Re-optimise pre-submitted track: $tpk\n";
            $out = '';
            $retv = 0;
            $out = `${BINDIR}optimise_flight.pl $tpk $comPk $tasPk $opt`;
            print $out;
        }
    }


    if ($task->{'type'} ne 'free-pin')
    {
        # Now verify the pre-submitted tracks against the task
        for my $tpk (@tracks)
        {
            print "Verifying pre-submitted track: $tpk\n";
            $retv = 0;
            $out = `${BINDIR}track_verify_sr.pl $tpk $tasPk`;
            print $out;
            $flag = 1;
        }
    }
    else
    {
        return 1;
    }

    return $flag;
}

#
# Main program here ..
#

my $dist;
my $tasPk;
my $task;
my $quality;
my $pth;
my $out;


if (scalar @ARGV < 1)
{
    print "task_up.pl <tasPk> [olc-pts]\n";
    exit 1;
}

$tasPk = $ARGV[0];

# Drop a mutex/lock - only do one at a time
if (-e "/var/lock/task_$tasPk")
{
    print "Task $tasPk already updating\n";
    exit 1;
}
`touch /var/lock/task_$tasPk`;

# Work out all the task totals to make it easier later
$dbh = db_connect();
$task = read_task($tasPk);
if (scalar @ARGV == 2)
{
    $opt = $ARGV[1];
}
else
{
    if (($task->{'type'} eq 'free') or ($task->{'type'} eq 'free-pin'))
    {
        $opt = "0";
    }
    elsif ($task->{'type'} eq 'olc')
    {
        $opt = "3";
    }
}

$dist = task_update($task);
#if (system($BINDIR . "short_route.pl $tasPk") == -1)
$pth = $BINDIR . 'short_route.pl';
$out = `$pth $tasPk`;
print $out;

if (track_update($task, $opt) == 1)
{
    # tracks re-verified - now rescore.
    $pth = $BINDIR . 'task_score.pl';
    $out = `$pth $tasPk`;
    #print $out;
}

`rm -f /var/lock/task_$tasPk`;

print "Task dist=$dist\n";


