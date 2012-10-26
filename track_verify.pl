#!/usr/bin/perl

#
# Verify a track against a task
# Used for Race competitions and Routes.
#
# Geoff Wong 2007
#

require DBD::mysql;

use Math::Trig;
use Data::Dumper;
use POSIX qw(ceil floor);
use TrackLib qw(:all);

sub validate_olc
{
    my ($flight, $task) = @_;
    my $traPk;
    my $tasPk;
    my %result;
    my $dist;
    my $out;
    
    $traPk = $flight->{'traPk'};
    $tasPk = $task->{'tasPk'};
    $out = `optimise_flight.pl $traPk $tasPk`;

    $sth = $dbh->prepare("select * from tblTrack where traPk=$traPk");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref())
    {
        $dist = $ref->{'traLength'};
    }

    $result{'start'} = $task->{'sstart'};
    $result{'goal'} = 0;
    $result{'startSS'} = $task->{'sstart'};
    $result{'endSS'} = $task->{'sstart'};
    $result{'distance'} = $dist;
    $result{'closest'} = 0;
    $result{'coeff'} = 0;
    $result{'waypoints_made'} = 0;

    return \%result;
}

# Name: validate_task
# Sequentially work through the track / waypoints 
# to find start / end / # of waypoints made / dist made / time if completed
# task spec:
#       type of task (free,elapsed,race,olc?)
#       start gate / start type / start time / [ waypoint ]* / 
#           end of SS / end of task (shape circle/semi circle)
#       % reduction on SS if made and not eot
#       use minimum task dist or centre of waypoints?
#   
# interpolate end times and making end sector
# FIX: Function is too big and should be broken down ...
#
sub validate_task
{
    my ($flight, $task) = @_;
    my $wpt;
    my $coord;
    my $closest;
    my $wcount;
    my ($awards,$awarded,$awtime);
    my $allpoints;
    my $waypoints;
    my $coords;
    my $dist;
    my ($reenter, $reflag);
    my ($closest, $closestwpt);
    my ($startss, $endss);
    my ($starttime, $goaltime);
    my ($wasinstart, $wasinSS);
    my %result;

    $closest = 9999999999;
    $wcount = 0;
    $starttime = 0;
    $startss = 0;
    $lastin = -1;
    $waypoints = $task->{'waypoints'};
    $coords = $flight->{'coords'};
    $awards = $flight->{'awards'};

    $allpoints = scalar @$waypoints;

    $wpt = $waypoints->[$wcount];
    $closestwpt = 0;
    $closestcoord = 0;

    # Stuff for leadout coeff calculation
    # against starttime (rather than first start time)
    my ($taskdist, $maxdist, $cwdist, $coeff);
    $taskdist = $task->{'distance'};
    $coeff = 0;
    $maxdist = 0;

    for $coord (@$coords)
    {
        # Check the task isn't finished ..
        if ($coord->{'time'} > $task->{'sfinish'})
        {
            print "Coordinate after task finish: ",
                $coord->{'time'}, " ", $task->{'sfinish'}, ".\n";
            last;
        }

        # Might re-enter start/speed section for elapsed time tasks 
        # Check if we did re-enter and set the task "back"
        if (defined($wasinstart) && $wasinstart == ($wcount-1))
        {
            $reenter = distance($coord, $waypoints->[$wasinstart]);
            if (($waypoints->[$wasinstart]->{'how'} eq 'exit' && $reenter < $waypoints->[$wasinstart]->{'radius'}) ||
                ($waypoints->[$wasinstart]->{'how'} eq 'entry' && $reenter > $waypoints->[$wasinstart]->{'radius'}))
            {
                print "re-entered start section\n";
                $wcount = $wasinstart;
                $wpt = $waypoints->[$wcount];
                $reflag = 1;
            }
        }
        if (defined($wasinSS) && $wasinSS == ($wcount-1))
        {
            $reenter = distance($coord, $waypoints->[$wasinSS]);
            if (($waypoints->[$wasinSS]->{'how'} eq 'exit' && $reenter < $waypoints->[$wasinSS]->{'radius'}) ||
                ($waypoints->[$wasinSS]->{'how'} eq 'entry' && $reenter > $waypoints->[$wasinSS]->{'radius'}))
            {
                print "re-entered speed section\n";
                $wcount = $wasinSS;
                $wpt = $waypoints->[$wcount];
                $reflag = 1;
            }
        }

        # Get the distance to next waypoint
        $dist = distance($coord, $wpt);

        # Work out leadout coeff if we've moved on
        if ($starttime > 0 && ($cwdist - $dist > $maxdist))
        {
            #print "startss=$startss coeff=$coeff, dist delta=", $cwdist-$dist-$maxdist, 
            #    " time delta=", $coord->{'time'} - $startss, 
            #    " coeff/taskdist=", $coeff/$taskdist, "\n";
            $coeff = $coeff + 
                ($cwdist-$dist-$maxdist)*($coord->{'time'}-$startss);
            $maxdist = $cwdist - $dist;
        }

        # Ok - work out if we're in cylinder
        if ($dist < $wpt->{'radius'} && ($wpt->{'type'} eq 'start'))
        {
            $wasinstart = $wcount;
        }
        if ($dist < $wpt->{'radius'} && ($wpt->{'type'} eq 'speed'))
        {
            $wasinSS = $wcount;
        }
        if ($dist < $wpt->{'radius'})
        {
            $lastin = $wcount;
        }

        $awarded = 0;
        if (defined($awards) && defined($awards->{$wpt->{'key'}}))
        {
            print "waypoint awarded\n";
            $awarded = 1;
            $awtime = $awards->{$wpt->{'key'}}->{'tadTime'};
        }

        # Find entry time for entry cylinder
        if ((($dist < $wpt->{'radius'}) || $awarded == 1)
            && ($wpt->{'how'} eq 'entry'))
        {
            print "made entry waypoint ", $wpt->{'number'}, "(", $wpt->{'type'}, ") radius ", $wpt->{'radius'}, "\n";

            # Do task timing stuff
            if (($wpt->{'type'} eq 'start') && ($starttime == 0 || $reflag == 1))
            {
                # get last start time ..
                # and in case they were to lazy to put in startss ...
                $starttime = 0 + $coord->{'time'};
                if (($task->{'type'} eq 'race') && ($starttime > $task->{'sstart'}))
                {
                    $starttime = 0 + $task->{'sstart'};
                }
                if ($awarded == 1 && $awtime > 0)
                {
                    $starttime = $awtime;
                }
                $startss = $starttime;
                $coeff = 0;
                $reflag = 0;
                print "startss(ent)=$startss\n";
            }
            if ($wpt->{'type'} eq 'speed')
            {
                # last point inside ..
                $starttime = 0 + $coord->{'time'};
                if (($task->{'type'} eq 'race') && ($starttime > $task->{'sstart'}))
                {
                    $starttime = 0 + $task->{'sstart'};
                }
                if ($awarded == 1 && $awtime > 0)
                {
                    $starttime = $awtime;
                }
                $startss = $starttime;
                $coeff = 0;
                print "speedss(ent)=$startss\n";
            }

            # Goal and speed section checks
            if ($wpt->{'type'} eq 'goal') 
            {
                # FIX: time should be estimated for the actual
                # line crossing on speed from last two waypoints ..
                # get first goal time ..
                if (!defined($goaltime))
                {
                    $goaltime = 0 + $coord->{'time'};
                    #print "goal: lat = ", $coord->{'lat'} * 180 / $pi;
                    #print " long = ", $coord->{'long'} * 180 / $pi, "\n";
                    if ($awarded == 1 && $awtime > 0)
                    {
                        print "goaltime=$goaltime awtime=$awtime\n";
                        $goaltime = $awtime;
                    }
                }
                if (!defined($endss))
                {
                    $endss = 0 + $coord->{'time'};
                    if ($awarded == 1 && $awtime > 0)
                    {
                        print "endss=$endss awtime=$awtime\n";
                        $endss = $awtime;
                    }
                }
            }
            if ($wpt->{'type'} eq 'endspeed')
            {
                # FIX: time should be estimated for the actual
                # line crossing on speed from last two waypoints ..
                if (!defined($endss))
                {
                    # first entry ..
                    $endss = 0 + $coord->{'time'};
                    if ($awarded == 1 && $awtime > 0)
                    {
                        $endss = $awtime;
                    }
                }
            }

            $wcount++;
            if ($wcount == $allpoints)
            {
                $closestcoord = 0;
                $result{'time'} = $endss - $startss;
                last;
            }
            $wpt = $waypoints->[$wcount];
            $cwdist = $cwdist + distance($waypoints->[$wcount-1], $waypoints->[$wcount]);

            if ($closestwpt < $wcount)
            {
                $closest = 9999999999;
                $closestcoord = $waypoints->[$wcount-1];
                $closestwpt = $wcount;
            }
        }
        elsif (($dist < $closest) && ($wcount >= $closestwpt))
        {
            #print "closest $closestwpt:$closest, distance: $dist\n";
            $closest = $dist;
            $closestcoord = $coord;
            $closestwpt = $wcount;
            #print "new closest $closestwpt:$closest\n";
        }

        # Check first exit time for exit cylinder
        if ((($dist >= $wpt->{'radius'}) || $awarded == 1)
            && ($wpt->{'how'} eq 'exit') && $lastin >= $wcount)
        {
            # print "made exit waypoint ($wasinstart,$wasinSS) ", $wpt->{'number'}, "(", $wpt->{'type'}, ") radius ", $wpt->{'radius'}, "\n";
            if (defined($wasinstart) && $wpt->{'type'} eq 'start')
            {
                # print "exit start waypoint ", $wpt->{'number'}, "(", $wpt->{'type'}, ") radius ", $wpt->{'radius'}, "\n";
                $starttime = 0 + $coord->{'time'};
                if ($awarded == 1 && $awtime > 0)
                {
                    $starttime = $awtime;
                }
                $startss = $starttime;
                $coeff = 0;
                if ($task->{'type'} eq 'race')
                {
                    $startss = 0 + $task->{'sstart'};
                }
            }

            if (defined($wasinSS) && $wpt->{'type'} eq 'speed')
            {
                # print "exit speed waypoint ", $wpt->{'number'}, "(", $wpt->{'type'}, ") radius ", $wpt->{'radius'}, "\n";
                # last point inside (elapsed)
                $starttime = 0 + $coord->{'time'};  # FIX: should this be set?
                if ($awarded == 1 && $awtime > 0)
                {
                    $starttime = $awtime;
                }
                $startss = $starttime;
                $coeff = 0;
                if ($task->{'type'} eq 'race')
                {
                    #$startss = 0 + $wpt->{'time'};
                    $startss = 0 + $task->{'sstart'};
                }
            }

            # How about a goal exit cylinder?

            # Ok - we were in and now we're out ...
            $wcount++;
            if ($wcount == $allpoints)
            {
                $closestcoord = 0;
                $result{'time'} = $endss - $startss;
                last;
            }
            $wpt = $waypoints->[$wcount];
            $cwdist = $cwdist + distance($waypoints->[$wcount-1], $waypoints->[$wcount]);
            if ($closestwpt < $wcount)
            {
                $closest = 9999999999;
                $closestcoord = $waypoints->[$wcount-1];
                $closestwpt = $wcount;
            }
        }
    }

    # Some startss corrections and checks
    #   starttime -  actual start time
    #   startss - start of task time (back to gate)
    if ($task->{'type'} eq 'race')
    {
        #print "RACE task\n";
        #$startss = $starttime;
        print "startss=$startss ($starttime)\n";
        if ($starttime < $startss)
        {
            # FIX: change to a penalty 
            if (defined($wasinSS))
            {
                $wcount = $wasinSS;
                $closestwpt = $wcount;
                $closestcoord = $waypoints->[$wcount];
                $result{'time'} = 0;
                $goaltime = 0;
                $endss = 0;
            }
            print "Jumped the start gate $wcount (race $startss: $starttime)\n";
        }
    }
    elsif ($task->{'type'} eq 'speedrun-interval')
    {
        # check ok start
        if ($starttime < $startss)
        {
            # FIX: change to a penalty 
            if (defined($wasinSS))
            {
                $wcount = $wasinSS;
                $closestwpt = $wcount;
                $closestcoord = $waypoints->[$wcount];
                $result{'time'} = 0;
                $goaltime = 0;
                $endss = 0;
            }
            print "Jumped the start gate $wcount (speedrun-interval $startss: $starttime)\n";
        }
        # set start time back to last interval ...
        $taskss = 0 + $task->{'sstart'};
        $finish = 0 + $task->{'sfinish'};
        $interval = 0 + $task->{'interval'};
        $startss = 0 + $taskss + floor(($starttime-$startss)/$interval)*$interval;
        if ($startss > $finish) 
        {
            $startss = $finish;
        }
    }
    else
    {
        if ($startss < $starttime)
        {
            print "Jumped the start gate (speedrun $starttime: $startss)\n";
            # FIX: ok to start anyway .. offset leading coeff / departure
            # penalty 100% (can be manually adjusted)
        }
    }

    #
    # Now compute our distance
    #
    $dist = 0.0;
    for my $i (0 .. $wcount-2)
    {
        $dist = $dist + distance($waypoints->[$i], $waypoints->[$i+1]);
        print "$i dist $dist\n";
    }

    print "wcount=$wcount\n";
    if ($wcount != $allpoints)
    {
        # we didn't make it in.
        $dist = $dist + 
                distance($waypoints->[$wcount-1], $waypoints->[$wcount])
                - distance($closestcoord, $waypoints->[$closestwpt]);
        # add rest of (distance_short * $task->{'sfinish'}) to coeff
        $coeff = $coeff + ($taskdist - $dist)*($task->{'sfinish'}-$startss);
    }

    # sanity ..
    if ($dist < 0)
    {
        $dist = 0;
    }

    $result{'start'} = $starttime;
    $result{'goal'} = $goaltime;
    $result{'startSS'} = $startss;
    $result{'endSS'} = $endss;
    $result{'distance'} = $dist;
    $result{'coeff'} = $coeff / $taskdist;
    if ($closestcoord)
    {
        # FIX: arc it back to the course line to get distance?
        #
        $result{'closest'} = distance($closestcoord, $waypoints->[$closestwpt]);
    }
    else
    {
        $result{'closest'} = 0;
    }
    $result{'waypoints_made'} = $wcount;

    return \%result;
}

#
# Main program here ..
#

my $flight;
my $task;
my $info;
my $duration;

if (scalar @ARGV < 1)
{
    print "track_verify.pl traPk\n";
    exit 1;
}

$dbh = db_connect();

# Read the flight
$flight = read_track($ARGV[0]);
#print Dumper($flight);

# Get the waypoints for the task
$task = read_task($flight->{'tasPk'});
#print Dumper($task);

# Verify and find waypoints / distance / speed / etc
if ($task->{'type'} eq 'olc')
{
    $info = validate_olc($flight, $task);

}
else
{
    $info = validate_task($flight, $task);
}
print Dumper($info);

# Store results in DB
store_result($flight,$info);

