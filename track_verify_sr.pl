#!/usr/bin/perl

#
# Verify a track against a task
# Used for Race competitions and Routes.
#
# Geoff Wong 2007
#

require DBD::mysql;

#use Math::Trig;
#use Data::Dumper;
use POSIX qw(ceil floor);
use TrackLib qw(:all);

my $debug = 0;
my $wptdistcache;

sub validate_olc
{
    my ($flight, $task, $tps) = @_;
    my $traPk;
    my $tasPk;
    my $comPk;
    my %result;
    my $dist;
    my $out;
    
    $traPk = $flight->{'traPk'};
    $tasPk = $task->{'tasPk'};
    $comPk = $task->{'comPk'};
    $out = `optimise_flight.pl $traPk $comPk $tasPk $tps`;

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

sub short_dist
{
    my ($w1, $w2) = @_;
    my $dist;
    my (%s1, %s2);

    $s1{'lat'} = $w1->{'short_lat'};
    $s1{'long'} = $w1->{'short_long'};
    $s2{'lat'} = $w2->{'short_lat'};
    $s2{'long'} = $w2->{'short_long'};

    $dist = distance(\%s1, \%s2);
    return $dist;
}

#
# Determine the start gate type and ESS dist
#
sub determine_start
{
    my ($task, $waypoints) = @_;
    my $cwdist;
    my ($spt, $ept, $gpt);
    my $ssdist;
    my $allpoints;
    my $startssdist;

    $allpoints = scalar @$waypoints;
    $cwdist = 0;
    for (my $i = 0; $i < $allpoints; $i++)
    {
        # Margins
        my $margin = $waypoints->[$i]->{'radius'} * 0.0005;
        if ($margin < 5.0)
        {
            $margin = 5.0;
        }
        $waypoints->[$i]->{'margin'} = $margin;

        if (( $waypoints->[$i]->{'type'} eq 'start') or 
             ($waypoints->[$i]->{'type'} eq 'speed') )
        {
            $spt = $i;
            $startssdist = $cwdist;
            #if ($waypoints->[$i]->{'how'} eq 'exit' && )
            #{
            #    $startssdist += $waypoints->[$i]->{'radius'};
            #}
        }
        if ($waypoints->[$i]->{'type'} eq 'speed') 
        {
            $cwdist = 0;
        }
        if ($waypoints->[$i]->{'type'} eq 'endspeed') 
        {
            $ept = $i;
            $ssdist = $cwdist;
            if ($waypoints->[$i]->{'how'} eq 'exit')
            {
                $ssdist += $waypoints->[$i]->{'radius'};
            }
        }
        if ($waypoints->[$i]->{'type'} eq 'goal') 
        {
            $gpt = $i;
        }
        if ($i < $allpoints-1)
        {
            $cwdist = $cwdist + short_dist($waypoints->[$i], $waypoints->[$i+1]);
        }
    } 
    if (!defined($ept))
    {
        $ept = $i;
    }
    if (!defined($gpt))
    {
        $gpt = $allpoints;
    }
    if (!defined($ssdist)) 
    {
        $ssdist = $cwdist;
        if ($waypoints->[$gpt]->{'how'} eq 'exit')
        {   
            $ssdist += $waypoints->[$gpt]->{'radius'};
        }   
    }

    $ssdist = $ssdist - $startssdist;
    print "spt=$spt ept=$ept gpt=$gpt ssdist=$ssdist startssdist=$startssdist\n";
    return ($spt, $ept, $gpt, $ssdist, $startssdist);
}

sub precompute_waypoint_dist
{
    my ($waypoints) = @_;
    my $wptdistcache = [];
    my $wcount = scalar @$waypoints;

    my $dist;
    my (%s1, %s2);

    $dist = 0.0;
    for my $i (0 .. $wcount-1)
    {
        $s1{'lat'} = $waypoints->[$i]->{'short_lat'};
        $s1{'long'} = $waypoints->[$i]->{'short_long'};
        $s2{'lat'} = $waypoints->[$i+1]->{'short_lat'};
        $s2{'long'} = $waypoints->[$i+1]->{'short_long'};
        $dist = $dist + distance(\%s1, \%s2);
        $wptdistcache->[$i+1] = $dist;
    }
}

sub compute_waypoint_dist
{
    my ($waypoints, $wcount) = @_;
    my $dist;
    my (%s1, %s2);

    if (defined($wptdistcache))
    {
        return $wptdistcache->[$wcount];
    }

    $dist = 0.0;
    for my $i (0 .. $wcount-1)
    {
        $s1{'lat'} = $waypoints->[$i]->{'short_lat'};
        $s1{'long'} = $waypoints->[$i]->{'short_long'};
        $s2{'lat'} = $waypoints->[$i+1]->{'short_lat'};
        $s2{'long'} = $waypoints->[$i+1]->{'short_long'};
        $dist = $dist + distance(\%s1, \%s2);
        if ($debug)
        {
            print "compute_waypoint_dist (wcount=$wcount): $i dist $dist\n";
        }
    }

    return $dist;
}

# Compare the centre of two waypoints.
# If the same return '1'.
sub compare_centres
{
    my ($wp1, $wp2) = @_;

    if ($wp1->{'dlat'} == $wp2->{'dlat'} && 
        $wp1->{'dlon'} == $wp2->{'dlon'})
    {
        return 1;
    }

    return 0;
}

sub init_kmtime
{
    my ($ssdist) = @_;
    my $kmtime = [];

    for my $it ( 0 .. floor($ssdist / 1000.0) )
    {
        $kmtime->[$it] = 0;
    }

    return $kmtime;
}

sub determine_utcmod
{
    my ($task, $coord) = @_;
    my $utcmod;

    $utcmod = 0;
    if ($coord->{'time'} > $task->{'sfinish'})
    {
        if (debug) { print "utcmod set at 86400\n"; }
        $utcmod = 86400;
    }
    elsif ($coord->{'time'}+43200 < $task->{'sstart'})
    {
        if (debug) { print "utcmod set at -86400\n"; }
        $utcmod = -86400;
    }

    return $utcmod;
}

# Compute current distance flown
# assumes we're not in goal
sub distance_flown
{
    my ($waypoints, $wmade, $coord) = @_;
    my $nextwpt = $waypoints->[$wmade];
    my $allpoints = scalar @$waypoints;
    my $cwdist = 0;
    my $nwdist = 0;
    my $rdist;

    if ($wmade > 0)
    {
        $cwdist = compute_waypoint_dist($waypoints, $wmade-1);
    }
    $nwdist = compute_waypoint_dist($waypoints, $wmade);

    if ($nextwpt->{'how'} eq 'exit')
    {
        # Same centre .. is this correct?
        $rdist = $nextwpt->{'radius'} - qckdist2($coord, $nextwpt);
        $dist = $nwdist - $rdist;
    }
    else
    {
        $rdist = qckdist2($coord, $nextwpt) - $nextwpt->{'radius'};;
        $dist = $nwdist - $rdist;
    }

    if ($dist < $cwdist)
    {
        $dist = $cwdist;
    }

    return $dist;
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
    my ($wpt, $rpt, $spt, $ept, $gpt);
    my $coord;
    my ($lastcoord, $preSScoord);
    my $lastmaxcoord;
    my $closest;
    my ($wcount,$wmade);        
    my ($awards,$awarded,$awtime);
    my $allpoints;
    my $waypoints;
    my $coords;
    my ($dist, $rdist, $edist);
    my $startssdist;
    my $penalty;
    my $comment;
    my $utcmod;
    my ($reenter, $reflag);
    my ($closest, $closestcoord, $closestwpt);
    my ($startss, $endss);
    my ($starttime, $stoptime, $goaltime);
    my ($wasinstart, $wasinSS);
    my ($furthest, $furthestwpt);
    my $taskss;
    my $stopalt;
    my $kmtime = [];
    my $kmmark;
    my %result;
    my (%s1, %s2, %s3);

    if ($debug)
    {
        print Dumper($task);
    }

    # Initialise some working variables
    $closest = 9999999999;
    $wcount = 0;
    $wmade = 0;
    $stopalt = 0;
    $stoptime = 0;
    $starttime = 0;
    $startss = 0;
    $lastin = -1;
    $reflag = -1;

    $waypoints = $task->{'waypoints'};
    $dist = compute_waypoint_dist($waypoints, $wcount-1);
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
    my ($maxdist, $coeff, $essdist);
    $coeff = 0;
    $kmtime = init_kmtime($task->{'ssdistance'});
    $maxdist = 0;

    # Check for UTC crossover
    $utcmod = determine_utcmod($task, $coords->[0]);

    # Determine the start gate type and ESS dist
    ($spt, $ept, $gpt, $essdist, $startssdist) = determine_start($task, $waypoints);

    # Go through the coordinates and verify the track against the task
    for $coord (@$coords)
    {
        # Check the task isn't finished ..
        $coord->{'time'} = $coord->{'time'} - $utcmod;
        #print "Coordinate time & stopped: ", $coord->{'time'}, " ", $task->{'sstopped'}, ".\n";
        if (defined($task->{'sstopped'}) && ($coord->{'time'} > $task->{'sstopped'}))
        {
            print "Coordinate after stopped time: ", $coord->{'time'}, " ", $task->{'sstopped'}, ".\n";
            $stopalt = $coord->{'alt'};
            $stoptime = $coord->{'time'};
            last;
        }
        if ($coord->{'time'} > $task->{'sfinish'})
        {
            print "Coordinate after task finish: ", $coord->{'time'}, " ", $task->{'sfinish'}, ".\n";
            last;
        }

        # Might re-enter start/speed section for elapsed time tasks 
        # Check if we did re-enter and set the task "back"
        if ($lastin == $spt)
        {
            $rpt = $waypoints->[$lastin];
            # Re-entered start cyclinder?
            $rdist = distance($coord, $rpt);
            if ($rpt->{'how'} eq 'entry')
            {
                #print "Repeat check ", $rpt->{'type'}, " (reflag=$reflag lastin=$lastin): dist=$rdist\n";
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
                    #$kmtime = init_kmtime($task->{'ssdistance'});
                    $reflag = -1;
                    # reset $wpt?
                    #print "re-entered (entry) startss=$startss\n";
                }
                elsif ($rdist >= ($rpt->{'radius'}-2))
                {
                    #print "Exited entry start/speed cylinder\n";
                    # if next wpt is inside this one then decrement ..
                    #if ($wpt->{'how'} == 'entry') { }
                    $reflag = $lastin;
                }
            }

            if ($rpt->{'how'} eq 'exit') 
            {
                if (($rdist < ($rpt->{'radius'}+5)) and ($reflag == $lastin))
                {
                    #print "re-entered (exit) speed/startss ($lastin) at " . $coord->{'time'} . " maxdist=$maxdist\n";
                    $wcount = $lastin;
                    #$wmade = $lastin;
                    #printf "dec wmade=$wmade\n";
                    $wpt = $waypoints->[$wcount];
                    $reflag = -1;
                }
                elsif ($rdist >= ($rpt->{'radius'}-2) and ($reflag == -1))
                {
                    #print "exited (exit) speed/startss ($lastin) at " . $coord->{'time'} . " maxdist=$maxdist\n";
                    $reflag = $lastin;
                    $starttime = 0 + $coord->{'time'};
                    if (($task->{'type'} eq 'race') && ($starttime > $task->{'sstart'}))
                    {
                        $starttime = 0 + $task->{'sstart'};
                    }
                    $startss = $starttime;
                    $coeff = 0;
                    #$kmtime = init_kmtime($task->{'ssdistance'});
                }
            }
        }
        
        # Get the distance to next waypoint
        my $newdist = distance_flown($waypoints, $wmade, $coord);
        $s1{'lat'} = $wpt->{'short_lat'};
        $s1{'long'} = $wpt->{'short_long'};
        #$sdist = distance($coord, \%s1);

        #print "wcount=$wcount wmade=$wmade newdist=$newdist maxdist=$maxdist time=", $coord->{'time'}, "\n";

        # Work out leadout coeff / maxdist if we've moved on
        if ($starttime != 0 and ($newdist > $maxdist))
        {
            if (!defined($endss))
            {
                if (defined($lastmaxcoord))
                {
                    $coeff = $coeff + $maxdist*($coord->{'time'}-$lastmaxcoord->{'time'});
                }
                $lastmaxcoord = $coord;
                #print "newdist=$newdist maxdist=$maxdist ctime=", $coord->{'time'}, " last ctime=", $lastmaxcoord->{'time'}, " ncoeff=$coeff\n";
            }

            $maxdist = $newdist;
            if (($maxdist >= $startssdist) && (!defined($endss)) 
                && ($kmtime->[floor(($maxdist-$startssdist)/1000)] == 0))
            {
                $kmtime->[floor(($maxdist-$startssdist)/1000)] = $coord->{'time'};
                print "kmtime ($maxdist): ", floor(($maxdist-$startssdist)/1000), ":", $coord->{'time'}, "\n";
            }
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
        $dist = distance($coord, $wpt);
        if ($dist < $wpt->{'radius'} && ($wpt->{'type'} eq 'start'))
        {
            $wasinstart = $wcount;
        }
        if ($dist < $wpt->{'radius'} && ($wpt->{'type'} eq 'speed'))
        {
            #print "wasinSS=$wcount\n";
            $wasinSS = $wcount;
        }
        if ($dist < ($wpt->{'radius'}+$wpt->{'margin'}) || $awarded)
        {
            #print "lastin=$wcount\n";
            $lastin = $wcount;
        }

        #
        # Handle Entry Cylinder
        #
        if ($wpt->{'how'} eq 'entry')
        {
            if (($dist < ($wpt->{'radius'}+$wpt->{'margin'})) || $awarded == 1) 
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
                    #$kmtime = init_kmtime($task->{'ssdistance'});
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
                    if ($stopalt == 0)
                    {
                        $stopalt = $coord->{'alt'};
                    }
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
                    if ($stopalt == 0)
                    {
                        $stopalt = $coord->{'alt'};
                    }
                    if ($awarded == 1 && $awtime > 0)
                    {
                        $endss = $awtime;
                    }
                    print $wpt->{'name'}, " endss=$endss at $dist\n";
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
        else 
        {
            # Handle exit cylinder
            if ((($dist >= $wpt->{'radius'}) || $awarded == 1) and ($lastin == $wcount))
            {
                #print "exited waypoint ($wasinstart,$wasinSS) ", $wpt->{'number'}, "(", $wpt->{'type'}, ") radius ", $wpt->{'radius'}, "\n";
                if ((defined($wasinstart) and $wpt->{'type'} eq 'start')
                    or (defined($wasinSS) and $wpt->{'type'} eq 'speed'))
                {
                    #print "exit waypoint ", $wpt->{'number'}, "(", $wpt->{'type'}, ") radius ", $wpt->{'radius'}, " @ ", $coord->{'time'}, "\n";
                    $starttime = 0 + $coord->{'time'};
                    if ($awarded == 1 && $awtime > 0)
                    {
                        $starttime = $awtime;
                    }
                    $startss = $starttime;
                    $coeff = 0;
                    #$kmtime = init_kmtime($task->{'ssdistance'});
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
                    if ($stopalt == 0)
                    {
                        $stopalt = $coord->{'alt'};
                    }
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
                    if ($stopalt == 0)
                    {
                        $stopalt = $coord->{'alt'};
                    }
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
                # Exit - so check the distance to the next waypoint with a different centre ..
                my $nextwp;

                if ($wcount > 0)
                {
                    $nextwp = $wcount;
                    while ($nextwp <= $gpt)
                    {
                        if (compare_centres($waypoints->[$nextwp-1], $waypoints->[$nextwp]) == 0)
                        {
                            last;
                        }
                        $nextwp++;
                    }
                }
                #print "wcount=$wcount nextwp=$nextwp\n";

                $edist = distance($coord, $waypoints->[$nextwp]);
                if (($edist < $closest) && ($wcount >= $closestwpt))
                {
                    $closest = $edist;
                    $closestcoord = $coord;
                    $closestwpt = $wcount;
                    if ($debug)
                    {
                        print "Exit(edist): new closest closestwpt=$closestwpt:closest=$closest\n";
                    }
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
            #$coeff = $coeff + $task->{'ssdistance'}*($startss-$starttime);
        }
        else
        {
            # Otherwise it's a zero for elapsed (?)
            $coeff = $coeff + $essdist*($finish-$startss);
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
    print "wcount=$wcount wmade=$wmade\n";
    
    if ($wcount < $wmade)
    {
        $wcount = $wmade;
    }

    if ($wmade == 0)
    {
        print "Didn't make the start\n";
        $s2{'lat'} = $waypoints->[$wcount+1]->{'short_lat'};
        $s2{'long'} = $waypoints->[$wcount+1]->{'short_long'};
        if ($closestcoord != 0)
        {
            $dist = short_dist($waypoints->[$wcount], $waypoints->[$wcount+1]) - distance($closestcoord, \%s2);
            if ($dist > $waypoints->[0]->{'radius'})
            {
                $dist = $waypoints->[0]->{'radius'};
            }
        }
        else
        {
            $dist = 0;
        }
        if ($dist < 0)
        {
            print "No distance achieved\n";
            $dist = 0;
        }
        print "wcount=0 dist=$dist\n";
        #$coeff = $coeff + ($essdist - $dist)*($task->{'sfinish'}-$startss);
        $coeff = $essdist * ($task->{'sfinish'}-$task->{'sstart'});
    }
    elsif ($wcount == 0)
    {
        print "Didn't make startss ($maxdist), closest wpt=$closestwpt\n";
        $dist = short_dist($waypoints->[$wcount], $waypoints->[$wcount+1]); # - distance($closestcoord, \%s2);
        print "wcount=0 dist=$dist\n";
        $coeff = $coeff + ($essdist - $dist)*($task->{'sfinish'}-$startss);
    }
    elsif ($wcount < $allpoints)
    {
        # we didn't make it into goal
        my $remainingss;
        my $cwclosest;

        $dist = distance_flown($waypoints, $wmade, $closestcoord);
        $remainingss = $essdist - $dist;

        # add rest of (distance_short * $task->{'sfinish'}) to coeff
        print "Incomplete ESS wcount=$wcount dist=$dist remainingss=$remainingss: ", $remainingss*($task->{'sfinish'}-$startss), "\n";
        $coeff = $coeff + $remainingss*($task->{'sfinish'}-$startss);
    }
    else
    {
        # Goal
        $dist = compute_waypoint_dist($waypoints, $wcount-1);
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
    $result{'stopalt'} = $stopalt;
    if ($stoptime > 0)
    {
        $result{'stoptime'} = $stoptime;
    }
    else
    {
        $result{'stoptime'} = $lastcoord->{'time'};
    }
    $result{'coeff'} = $coeff / $essdist;
    if ($closestcoord)
    {
        # FIX: arc it back to the course line to get distance?
        $result{'closest'} = distance($closestcoord, $waypoints->[$closestwpt]);
    }
    else
    {
        $result{'closest'} = 0;
    }
    $result{'kmtime'} = $kmtime;
    $result{'waypoints_made'} = $wcount;

    #print Dumper($kmtime);

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

if ($ARGV[0] eq '-d')
{
    $debug = 1;
    shift @ARGV;
}

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
#print Dumper($info);

# Store results in DB
store_result($flight,$info);

