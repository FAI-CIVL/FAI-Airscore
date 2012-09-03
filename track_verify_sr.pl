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

my $debug = 0;

sub validate_olc
{
    my ($flight, $task, $tps) = @_;
    my $traPk;
    my $tasPk;
    my %result;
    my $dist;
    my $out;
    
    $traPk = $flight->{'traPk'};
    $tasPk = $task->{'tasPk'};
    $out = `optimise_flight.pl $traPk $tasPk $tps`;

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

#
# Name: validate_task
#
# Sequentially work through the track / waypoints 
# to find start / end / # of waypoints made / dist made / time if completed
# task spec:
#       type of task (free,elapsed,elapsed-interval,race)
#       start gate / start type / start time / [ waypoint ]* / 
#           end of SS / goal (shape circle/semi circle?)
#       % reduction on SS if made and not eot
#       use minimum task dist or centre of waypoints?
#   
# interpolate end times and making end sector
# Assumptions: 
#   there is never a waypoint after goal
#   once you take the waypoint after start/speed you can't restart
#       
# FIX: Function is too big and should be broken down ...
#
sub validate_task
{
    my ($flight, $task) = @_;
    my ($wpt, $rpt, $spt);
    my $coord;
    my ($lastcoord, $preSScoord);
    my $closest;
    my ($wcount,$wmade);        
    my ($awards,$awarded,$awtime);
    my $allpoints;
    my $waypoints;
    my $coords;
    my ($dist, $rdist, $edist);
    my $penalty;
    my $comment;
    my $utcmod;
    my ($reenter, $reflag);
    my ($closest, $closestwpt);
    my ($startss, $endss);
    my ($starttime, $goaltime);
    my ($wasinstart, $wasinSS);
    my ($furthest, $furthestwpt);
    my $taskss;
    my %result;

    #print Dumper($task);

    # Initialise some working variables
    $closest = 9999999999;
    $wcount = 0;
    $wmade = 0;
    $starttime = 0;
    $startss = 0;
    $lastin = -1;
    $reflag = -1;
    $waypoints = $task->{'waypoints'};
    $coords = $flight->{'coords'};
    $awards = $flight->{'awards'};
    $allpoints = scalar @$waypoints;

    # Next waypoint
    $wpt = $waypoints->[$wcount];

    # Closest waypoint
    $closestwpt = 0;
    $closestcoord = 0;

    # Stuff for leadout coeff calculation
    # against starttime (rather than first start time)
    my ($taskdist, $maxdist, $cwdist, $coeff);
    $taskdist = $task->{'short_distance'};
    $cwdist = 0;
    $coeff = 0;
    $maxdist = 0;

    # Check for UTC crossover
    $utcmod = 0;
    $coord = $coords->[0];
    if ($coord->{'time'} > $task->{'sfinish'})
    {
        print "utcmod set at 86400\n";
        $utcmod = 86400;
    }
    elsif ($coord->{'time'}+43200 < $task->{'sstart'})
    {
        print "utcmod set at -86400\n";
        $utcmod = -86400;
    }

    # Determine the start gate type
    for (my $i = 0; $i < $allpoints; $i++)
    {
        if (( $waypoints->[$i]->{'type'} eq 'start') or 
             ($waypoints->[$i]->{'type'} eq 'speed') )
        {
            $spt = $i;
        }
    } 
    # Go through the coordinates and verify the track against the task
    for $coord (@$coords)
    {
        # Check the task isn't finished ..
        $coord->{'time'} = $coord->{'time'} - $utcmod;
        if ($coord->{'time'} > $task->{'sfinish'})
        {
            print "Coordinate after task finish: ",
                $coord->{'time'}, " ", $task->{'sfinish'}, ".\n";
            last;
        }

        # Might re-enter start/speed section for elapsed time tasks 
        # Check if we did re-enter and set the task "back"
        $rpt = $waypoints->[$lastin];
        if (($rpt->{'type'} eq 'start') or ($rpt->{'type'} eq 'speed'))
        {
            # Re-entered start cyclinder?
            $rdist = distance($coord, $rpt);
            #print "Repeat check ", $rpt->{'type'}, " (reflag=$reflag lastin=$lastin): dist=$rdist\n";
            if ($rpt->{'how'} eq 'entry')
            {
                if (($rdist < ($rpt->{'radius'}+5)) and ($reflag == $lastin))
                {
                    # last point inside ..
                    $starttime = 0 + $coord->{'time'};
                    if (($task->{'type'} eq 'race') && ($starttime > $task->{'sstart'}))
                    {
                        $starttime = 0 + $task->{'sstart'};
                    }
                    $startss = $starttime;
                    $coeff = 0;
                    $reflag = -1;
                    print "re-entered (entry) startss=$startss\n";
                }
                elsif ($rdist >= ($rpt->{'radius'}-2))
                {
                    print "Exited entry start/speed cylinder\n";
                    $reflag = $lastin;
                }
            }

            if ($rpt->{'how'} eq 'exit') 
            {
                if (($rdist < ($rpt->{'radius'}+5)) and ($reflag == $lastin))
                {
                    #print "re-entered (exit) speed/startss ($lastin) at " . $coord->{'time'} . "\n";
                    $wcount = $lastin;
                    #$wmade = $lastin;
                    #printf "dec wmade=$wmade\n";
                    $wpt = $waypoints->[$wcount];
                    $reflag = -1;
                }
                elsif ($rdist >= ($rpt->{'radius'}-2) and ($reflag == -1))
                {
                    #print "exited (exit) speed/startss ($lastin) at " . $coord->{'time'} . "\n";
                    $reflag = $lastin;
                    $starttime = 0 + $coord->{'time'};
                    if (($task->{'type'} eq 'race') && ($starttime > $task->{'sstart'}))
                    {
                        $starttime = 0 + $task->{'sstart'};
                    }
                    $startss = $starttime;
                    $coeff = 0;
                }
            }
        }
        
        # Get the distance to next waypoint
        $dist = distance($coord, $wpt);
        $s1{'lat'} = $wpt->{'short_lat'};
        $s1{'long'} = $wpt->{'short_long'};
        $sdist = distance($coord, \%s1);

        # Work out leadout coeff if we've moved on
        if ($starttime != 0 and ($cwdist - $sdist > $maxdist))
        {
            $coeff = $coeff + 
                    ($cwdist-$sdist-$maxdist)*($coord->{'time'}-$starttime);
            #print "new coeff=$coeff, dist delta (cw=$cwdist,sd=$sdist,md=$maxdist)=", $cwdist-$sdist-$maxdist, "\n",
            #    " time delta (coord time-$startss)=", $coord->{'time'} - $startss,
            #    " coeff/taskdist=", $coeff/$taskdist, "\n";
            $maxdist = $cwdist - $sdist;
        }

        # Was the next point awarded via management interface?
        $awarded = 0;
        if (defined($awards) && defined($awards->{$wpt->{'key'}}))
        {
            if ($debug)
            {
                print "waypoint ($wcount) awarded\n";
            }
            $awarded = 1;
            $awtime = $awards->{$wpt->{'key'}}->{'tadTime'};
        }

        # Ok - work out if we're in cylinder
        if ($debug)
        {
            print "Check ($wcount), dist=$dist type=", $wpt->{'type'}, "\n";
        }

        if ($dist < $wpt->{'radius'} && ($wpt->{'type'} eq 'start'))
        {
            $wasinstart = $wcount;
        }
        if ($dist < $wpt->{'radius'} && ($wpt->{'type'} eq 'speed'))
        {
            #print "wasinSS=$wcount\n";
            $wasinSS = $wcount;
        }
        if ($dist < $wpt->{'radius'} || $awarded)
        {
            #print "lastin=$wcount\n";
            $lastin = $wcount;
        }

        #if ($wcount == $allpoints)
        #{
        #   if ($task->{'type'} eq 'free') 
        #   {
        #       $rdist = distance($coord, $rpt);
        #       if ($rdist > $furthest)
        #       {
        #           $furthest = $rdist;
        #           $furtheswpt = $coord;
        #       }
        #   }
        #   elsif ($task->'type' eq 'free-bearing')
        #   {
        #       $rdist = bearing_distance($coord, $rpt);
        #       if ($rdist > $furthest)
        #       {
        #           $furthest = $rdist;
        #           $furtheswpt = $coord;
        #       }
        #   }
        #}

        #
        # Handle Entry Cylinder
        #
        if ($wpt->{'how'} eq 'entry')
        {
            if (($dist < $wpt->{'radius'}) || $awarded == 1) 
            {
                if ($debug) 
                {
                    print "made entry waypoint ", $wpt->{'number'}, "(", $wpt->{'type'}, ") radius ", $wpt->{'radius'}, " at ", $coord->{'time'}, "\n";
                }
                # Do task timing stuff
                if (($wpt->{'type'} eq 'start') && ($starttime == 0) or
                    ($wpt->{'type'} eq 'speed'))
                {
                    # get last start time ..
                    # and in case they were to lazy too put in startss ...
                    $starttime = 0 + $coord->{'time'};
                    $preSScoord = $lastcoord;
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
                    print "1st ", $wpt->{'type'}, "(ent)=$startss\n";
                }
    
                # Goal and speed section checks
                if (($wpt->{'type'} eq 'goal') and (!defined($goaltime)))
                {
                    # FIX: time should be estimated for the actual
                    # line crossing on speed from last two waypoints ..
                    #print "goal: lat = ", $coord->{'lat'} * 180 / $pi;
                    #print " long = ", $coord->{'long'} * 180 / $pi, "\n";
    
                    $goaltime = 0 + $coord->{'time'};
                    if ($awarded == 1 && $awtime > 0)
                    {
                        print "goaltime=$goaltime awtime=$awtime\n";
                        $goaltime = $awtime;
                    }
                }
    
                if (($wpt->{'type'} eq 'endspeed') and (!defined($endss)))
                {
                    # FIX: time should be estimated for the actual
                    # line crossing on speed from last two waypoints ..
                    $endss = 0 + $coord->{'time'};
                    if ($awarded == 1 && $awtime > 0)
                    {
                        $endss = $awtime;
                    }
                }
    
                $wcount++;
                $wmade = $wcount;
                if ($debug)
                {
                    print "inc entry wmade=$wmade\n";
                }
                #and (($task->{'type'} eq 'race') or ($task->{'type'} eq 'speedrun') or ($task->'type' eq 'speedrun-interval')))
                if ($wcount == $allpoints) 
                {
                    # and not free bearing?
                    $closestcoord = 0;
                    $result{'time'} = $endss - $startss;
                    last;
                }
                $wpt = $waypoints->[$wcount];
                $s1{'lat'} = $waypoints->[$wcount-1]->{'short_lat'};
                $s1{'long'} = $waypoints->[$wcount-1]->{'short_long'};
                $s2{'lat'} = $wpt->{'short_lat'};
                $s2{'long'} = $wpt->{'short_long'};
                $cwdist = $cwdist + distance(\%s1,\%s2);
    
                if ($closestwpt < $wcount)
                {
                    $closest = 9999999999;
                    $closestcoord = $waypoints->[$wcount-1];
                    $closestwpt = $wcount;
                }
            }
            elsif (($dist < $closest) && ($wcount >= $closestwpt))
            {
                # Entry - check distance to current waypoint
                # print "closest (entry) $closestwpt:$closest, distance: $dist\n";
                $closest = $dist;
                $closestcoord = $coord;
                $closestwpt = $wcount;
                #print "new closest $closestwpt:$closest\n";
            }
        }
        else # Handle exit cylinder
        {
            if ((($dist >= $wpt->{'radius'}) || $awarded == 1) and ($lastin == $wcount))
            {
                #print "made exit waypoint ($wasinstart,$wasinSS) ", $wpt->{'number'}, "(", $wpt->{'type'}, ") radius ", $wpt->{'radius'}, "\n";
                if ((defined($wasinstart) and $wpt->{'type'} eq 'start')
                    or (defined($wasinSS) and $wpt->{'type'} eq 'speed'))
                {
                    print "exit waypoint ", $wpt->{'number'}, "(", $wpt->{'type'}, ") radius ", $wpt->{'radius'}, " @ ", $coord->{'time'}, "\n";
                    $starttime = 0 + $coord->{'time'};
                    if ($awarded == 1 && $awtime > 0)
                    {
                        $starttime = $awtime;
                    }
                    $startss = $starttime;
                    $coeff = 0;
                    $reflag = -1;
                    #print "start(exit)=$startss\n";
                    if ($task->{'type'} eq 'race')
                    {
                        $startss = 0 + $task->{'sstart'};
                    }
                }
    
                # Goal and speed section checks
                if (($wpt->{'type'} eq 'goal') and (!defined($goaltime)))
                {
                    # FIX: time should be estimated for the actual
                    # line crossing on speed from last two waypoints ..
                    $goaltime = 0 + $coord->{'time'};
                    if ($awarded == 1 && $awtime > 0)
                    {
                        print "awarded goaltime=$goaltime awtime=$awtime\n";
                        $goaltime = $awtime;
                    }
                }
    
                if ($wpt->{'type'} eq 'endspeed' and (!defined($endss)))
                {
                    # FIX: time should be estimated for the actual
                    # line crossing on speed from last two waypoints ..
                    $endss = 0 + $coord->{'time'};
                    if ($awarded == 1 && $awtime > 0)
                    {
                        $endss = $awtime;
                    }
                }
    
                # Ok - we were in and now we're out ...
                $wcount++;
                $wmade = $wcount;
                #printf "inc exit ($wcount) wmade=$wmade\n";
                #and (($task->{'type'} eq 'race') or ($task->{'type'} eq 'speedrun') or ($task->'type' eq 'speedrun-interval')))
                if ($wcount == $allpoints)
                {
                    # Completed task
                    $closestcoord = 0;
                    $result{'time'} = $endss - $startss;
                    last;
                }
    
                # Are we any closer?
                $wpt = $waypoints->[$wcount];
                $s1{'lat'} = $waypoints->[$wcount-1]->{'short_lat'};
                $s1{'long'} = $waypoints->[$wcount-1]->{'short_long'};
                $s2{'lat'} = $wpt->{'short_lat'};
                $s2{'long'} = $wpt->{'short_long'};
                $cwdist = $cwdist + distance(\%s1, \%s2);
                if ($closestwpt < $wcount)
                {
                    $closest = 9999999999;
                    $closestcoord = $waypoints->[$wcount-1];
                    $closestwpt = $wcount;
                    #print "closestwpt $closestwpt:$closest\n";
                }
            }
            else
            {
                # Exit - so check the distance to the next waypoint 
                $edist = distance($coord, $waypoints->[$wcount+1]);
                if (($edist < $closest) && ($wcount >= $closestwpt))
                {
                    # print "closest (exit) $closestwpt:$closest, distance next: $edist\n";
                    $closest = $edist;
                    $closestcoord = $coord;
                    $closestwpt = $wcount;
                    #print "new closest $closestwpt:$closest\n";
                }
            }
        }

        $lastcoord = $coord;
        # end of mail coordinate loop
    }

    # We made goal?
    if (defined($goaltime))
    {
        # FIX: time should be estimated for the actual
        # line crossing on speed from last two waypoints ..
        # get first goal time ..
        #$goaltime = 0 + $coord->{'time'};
        #print "goal: lat = ", $coord->{'lat'} * 180 / $pi;
        #print " long = ", $coord->{'long'} * 180 / $pi, "\n";
        #if ($awarded == 1 && $awtime > 0)
        #{
        #    print "goaltime=$goaltime awtime=$awtime\n";
        #    $goaltime = $awtime;
        #}

        if (!defined($endss))
        {
            $endss = $goaltime;
            if ($awarded == 1 && $awtime > 0)
            {
                print "endss=$endss awtime=$awtime\n";
                $endss = $awtime;
            }
        }
    }

    # Some startss corrections and checks
    #   starttime -  actual start time
    #   startss - start of task time (back to gate)

    $taskss = 0 + $task->{'sstart'};
    $finish = 0 + $task->{'sfinish'};
    $interval = 0 + $task->{'interval'};
    print "wasinSS=$wasinSS taskss=$taskss startss=$startss starttime=$starttime interval=$interval\n";

    # Elapsed-interval - pick previous gate
    if ($task->{'type'} eq 'speedrun-interval')
    {
        print "speedrun-interval .. startss=$startss taskss=$taskss\n";
        if ($startss > $taskss) 
        {
            $startss = 0 + $taskss + floor(($starttime-$taskss)/$interval)*$interval;
        }
    }

    # Can't start later than start close time
    if (($task->{'sstartclose'} > $task->{'sstart'}) and ($startss > $task->{'sstartclose'}))
    {
        $startss = $task->{'sstartclose'};
    }

    # Sanity
    if ($startss > $finish) 
    {
        $startss = $finish;
    }

    # Jumped the start/speedss?
    if ($task->{'type'} != 'route' and $starttime > 0 and (($starttime < $startss) or ($starttime < $taskss)) and ($wmade > $spt))
    {
        my $jump;
        print "Jumped the start gate ($spt) (taskss=$taskss finish=$finish) (startss=$startss: $starttime)\n";
        $jump = $taskss - $startss;
        $comment = "jumped $jump secs";
        if ($task->{'type'} eq 'race')
        {
            print "Race start jump: $comment\n";
            # Store # of seconds jumped in penalty
            $penalty = $jump
            # shift leadout graph so it doesn't screw other lo points
            # Should be covered by using starttime elsewhere now ..
            #$coeff = $coeff + $taskdist*($startss-$starttime);
        }
        else
        {
            # Otherwise it's a zero for elapsed (?)
            $coeff = $coeff + $taskdist*($finish-$startss);
            if ($waypoints->[$spt]->{'how'} eq 'entry')
            {
                print "Elasped entry jump: $comment\n";
                $wcount = $spt - 1;
                if ($wmade >= $spt)
                {
                    $closestwpt = $spt;
                    $closestcoord = $preSScoord;
                    #print "preSScoord=", Dumper($preSScoord);
                }
                $wmade = $spt;
                if ($wmade < 0)
                {
                    $wmade = 0;
                }
            }
            else
            {
                # exit jump
                print "Exit gate jump: $comment\n";
                $wcount = $spt;
                if ($wmade > $spt)
                {
                    $closestwpt = $spt;
                    $closestcoord = $waypoints->[$spt];
                }
                $wmade = $spt;
                $closestwpt = $spt;
                $closestcoord = $waypoints->[$spt];
            }
            $result{'time'} = 0;
            $goaltime = 0;
            $endss = 0;
        }
    }

    #
    # Now compute our distance
    #
    $dist = 0.0;
    for my $i (0 .. $wcount-2)
    {
        $s1{'lat'} = $waypoints->[$i]->{'short_lat'};
        $s1{'long'} = $waypoints->[$i]->{'short_long'};
        $s2{'lat'} = $waypoints->[$i+1]->{'short_lat'};
        $s2{'long'} = $waypoints->[$i+1]->{'short_long'};
        $dist = $dist + distance(\%s1, \%s2);
        print "$i dist $dist\n";
    }

    print "wcount=$wcount wmade=$wmade\n";
    
    if ($wcount < $wmade)
    {
        $wcount = $wmade;
    }

    if ($wmade == 0)
    {
        print "Didn't make the start\n";
        $s1{'lat'} = $waypoints->[$wcount]->{'short_lat'};
        $s1{'long'} = $waypoints->[$wcount]->{'short_long'};
        $s2{'lat'} = $waypoints->[$wcount+1]->{'short_lat'};
        $s2{'long'} = $waypoints->[$wcount+1]->{'short_long'};
        #$s3{'lat'} = $waypoints->[$closestwpt]->{'short_lat'};
        #$s3{'long'} = $waypoints->[$closestwpt]->{'short_long'};
        $dist = distance(\%s1, \%s2) - distance($closestcoord, \%s2);
        if ($dist > $waypoints->[0]->{'radius'})
        {
            $dist = $waypoints->[0]->{'radius'};
        }
        if ($dist < 0)
        {
            print "No distance achieved\n";
            $dist = 0;
        }
        print "wcount=0 dist=$dist\n";
        #$coeff = $coeff + ($taskdist - $dist)*($task->{'sfinish'}-$startss);
        $coeff = $taskdist * ($task->{'sfinish'}-$task->{'sstart'});
    }
    elsif ($wcount == 0)
    {
        print "Didn't make startss ($maxdist), closest wpt=$closestwpt\n";
        $s1{'lat'} = $waypoints->[$wcount]->{'short_lat'};
        $s1{'long'} = $waypoints->[$wcount]->{'short_long'};
        $s2{'lat'} = $waypoints->[$wcount+1]->{'short_lat'};
        $s2{'long'} = $waypoints->[$wcount+1]->{'short_long'};
        #$s3{'lat'} = $waypoints->[$closestwpt]->{'short_lat'};
        #$s3{'long'} = $waypoints->[$closestwpt]->{'short_long'};
        $dist = distance(\%s1, \%s2); # - distance($closestcoord, \%s2);
        print "wcount=0 dist=$dist\n";
        $coeff = $coeff + ($taskdist - $dist)*($task->{'sfinish'}-$startss);
    }
    elsif ($wcount != $allpoints)
    {
        # we didn't make it in.
        print "Didn't make goal (closest=$closestwpt)\n";
        $s1{'lat'} = $waypoints->[$wcount-1]->{'short_lat'};
        $s1{'long'} = $waypoints->[$wcount-1]->{'short_long'};
        $s2{'lat'} = $waypoints->[$wcount]->{'lat'};
        $s2{'long'} = $waypoints->[$wcount]->{'long'};
        $s3{'lat'} = $waypoints->[$closestwpt]->{'lat'};
        $s3{'long'} = $waypoints->[$closestwpt]->{'long'};
        $dist = $dist + 
                distance(\%s1, \%s2) - distance($closestcoord, \%s3);
        print "closest dist=", distance($closestcoord, \%s3), " vs closest=$closest\n";
        #print Dumper($closestcoord);
        # add rest of (distance_short * $task->{'sfinish'}) to coeff
        #print "incomplete coeff=", ($taskdist - $dist)*($task->{'sfinish'}-$startss), "\n";
        $coeff = $coeff + ($taskdist - $dist)*($task->{'sfinish'}-$startss);
    }
    #elsif ($task->{'type'} eq 'free' or $task->{'type'} eq 'free-bearing') 
    #   {
    #       $dist = $dist + $furthest;
    #   }


    # sanity ..
    if ($dist < 0)
    {
        printf "Somehow the distance ($dist) is < 0\n";
        $dist = 0;
    }

    $result{'start'} = $starttime;
    $result{'goal'} = $goaltime;
    $result{'startSS'} = $startss;
    $result{'endSS'} = $endss;
    $result{'distance'} = $dist;
    $result{'penalty'} = $penalty;
    $result{'comment'} = $comment;
    $result{'coeff'} = $coeff / $taskdist;
    if ($closestcoord)
    {
        # FIX: arc it back to the course line to get distance?
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
my $tasPk;
my $info;
my $duration;

if (scalar @ARGV < 1)
{
    print "track_verify_sr.pl traPk [tasPk]\n";
    exit 1;
}

$dbh = db_connect();

# Read the flight
$flight = read_track($ARGV[0]);
#print Dumper($flight);

# Get the waypoints for specific task
if (0+$ARGV[1] > 0)
{
    $flight->{'tasPk'} = 0 + $ARGV[1];
}
$task = read_task($flight->{'tasPk'});
#print Dumper($task);

# Verify and find waypoints / distance / speed / etc
if ($task->{'type'} eq 'olc')
{
    $info = validate_olc($flight, $task, 3);

}
elsif ($task->{'type'} eq 'free')
{
    $info = validate_olc($flight, $task, 0);
}
else
{
    $info = validate_task($flight, $task);
}
print Dumper($info);

# Store results in DB
store_result($flight,$info);

