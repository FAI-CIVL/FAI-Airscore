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
use strict;

# Add currect bin directory to @INC
use lib '/var/www/cgi-bin';
use Route qw(:all);


my $dbh;
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

    my $sth = $dbh->prepare("select * from tblTrack where traPk=$traPk");
    my $ref;
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

sub precompute_waypoint_dist
{
    my ($waypoints) = @_;
    my $wcount = scalar @$waypoints;

    my $dist;
    my $exdist;
    my (%s1, %s2);

    $wptdistcache = [];

    $dist = 0.0;
    $wptdistcache->[0] = 0.0;
    print Dumper($waypoints);
    for my $i (0 .. $wcount-2)
    {
        $s1{'lat'} = $waypoints->[$i]->{'short_lat'};
        $s1{'long'} = $waypoints->[$i]->{'short_long'};
        $s2{'lat'} = $waypoints->[$i+1]->{'short_lat'};
        $s2{'long'} = $waypoints->[$i+1]->{'short_long'};
        $exdist = distance(\%s1, \%s2);
        print "s1 lat = $s1{'lat'} , lon = $s1{'long'} - s2 lat = $s2{'lat'} , lon = $s2{'long'}";
        print "exdist waypoint $i=$exdist\n";
        if ($exdist > 0.0)
        {
            $dist = $dist + $exdist;
        }
        elsif ($waypoints->[$i]->{'how'} eq 'exit' && $waypoints->[$i+1]->{'how'} eq 'exit')
        {
            # Check centres?
            print Dumper($waypoints->[$i]);
            print Dumper($waypoints->[$i+1]);
            if ($i > 0 && (ddequal($waypoints->[$i], $waypoints->[$i-1]) && $waypoints->[$i-1]->{'how'} eq 'exit'))
            {
                $dist = $dist + $waypoints->[$i]->{'radius'} - $waypoints->[$i-1]->{'radius'};
            }
            else
            {
                $dist = $dist + $waypoints->[$i]->{'radius'};
            }
        }
        $wptdistcache->[$i+1] = $dist;
        print "$i: cumdist=$dist\n";

        my $sdist = qckdist2(\%s1, $waypoints->[$i]);
        if ($waypoints->[$i]->{'radius'} > $sdist+100)
        {
            $waypoints->[$i]->{'inside'} = 1;
        }
        else
        {
            $waypoints->[$i]->{'inside'} = 0;
        }
    }
    print "precompute dist=$dist\n";
}

sub compute_waypoint_dist
{
    my ($waypoints, $wcount) = @_;
    my $dist;
    my $wpdist = -1;
    my (%s1, %s2);
    my $i;

    if (defined($wptdistcache))
    {
        return $wptdistcache->[$wcount];
    }

    if ($debug)
    {
        print "compute_waypoint_dist (wcount=$wcount\n";
    }

    $dist = 0.0;
    for $i (0 .. $wcount-1)
    {
        $s1{'lat'} = $waypoints->[$i]->{'short_lat'};
        $s1{'long'} = $waypoints->[$i]->{'short_long'};
        $s2{'lat'} = $waypoints->[$i+1]->{'short_lat'};
        $s2{'long'} = $waypoints->[$i+1]->{'short_long'};
        $wpdist = distance(\%s1, \%s2);
        $dist = $dist + $wpdist;

        if ($debug)
        {
            print "   compute_waypoint_dist (wcount=$wcount): $i: dist=$dist ($wpdist)\n";
        }
    }

    if ($wcount > -1 && $wpdist == 0)
    {
        $dist = $dist + $waypoints->[$wcount-1]->{'radius'};
    }

    if ($debug)
    {
        print "    compute_waypoint_dist (wcount=$wcount): $i final dist $dist\n";
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
        if ($debug) { print "utcmod set at 86400\n"; }
        $utcmod = 86400;
    }
    elsif ($coord->{'time'}+43200 < $task->{'sstart'})
    {
        if ($debug) { print "utcmod set at -86400\n"; }
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
    my $dist = 0;
    my $cwdist = 0;
    my $nwdist = 0;
    my $exitflag = 0;
    my %s1;

    if ($wmade > 0)
    {
        if ($nextwpt->{'how'} eq 'exit')
        {
            # Move to the end of a sequence of 'exit' cylinders (start / speed / etc)
            my $nxtnxt = $wmade+1;
            while (($nxtnxt < scalar @$waypoints) && ($waypoints->[$nxtnxt]->{'how'} eq 'exit') && ddequal($nextwpt, $waypoints->[$nxtnxt]))
            {
                $nxtnxt++;
            }

            if ($nxtnxt < scalar @$waypoints)
            {
                if ($waypoints->[$nxtnxt]->{'how'} eq 'entry')
                {
                    if (qckdist2($waypoints->[$nxtnxt], $nextwpt) + $waypoints->[$nxtnxt]->{'radius'} < $waypoints->[$nxtnxt-1]->{'radius'})
                    {
                        $exitflag = 1;
                    }
                }
            }
            else
            {
                $exitflag = 1;
            }
        }
    }


    if ($exitflag) 
    {
        # Scoring any exit direction (because we're coming back in)
        $cwdist = compute_waypoint_dist($waypoints, $wmade-1);
        $dist = qckdist2($coord, $nextwpt) + $cwdist;
    }
    else
    {
        my $rdist;

        $nwdist = compute_waypoint_dist($waypoints, $wmade);

        if ($nextwpt->{'type'} ne 'goal' && $nextwpt->{'type'} ne 'endspeed')
        {
            # Distance to shortest route waypoint, but should this be shortest distance to make the waypoint?
            $s1{'lat'} = $nextwpt->{'short_lat'};
            $s1{'long'} = $nextwpt->{'short_long'};
            $rdist = qckdist2($coord, \%s1);
            #my $sdist = qckdist2($coord, $nextwpt) - $nextwpt->{'radius'};
            #if ($sdist < $rdist)
            #{
            #    $rdist = $sdist;
            #}
        }
        else
        {
            if ($nextwpt->{'shape'} eq 'line')
            {
                # @todo: should really be distance to the goal line (not centre), if route to goal goes through back of semi, then subtract radius
                $rdist = qckdist2($coord, $nextwpt);
            }
            else
            {
                $rdist = qckdist2($coord, $nextwpt) - $nextwpt->{'radius'};
            }
        }

        $dist = $nwdist - $rdist;
        if ($dist < $cwdist)
        {
            $dist = $cwdist;
        }
    }

    if ($debug)
    {
        print "wmade=$wmade cwdist=$cwdist nwdist=$nwdist dist=$dist\n";
    }

    return $dist;
}

sub made_entry_waypoint
{
    my ($waypoints, $wmade, $coord, $dist, $awarded) = @_;
    my $made = 0;
    my $wpt = $waypoints->[$wmade];

    if ($awarded)
    {
        return 1;
    }

    if ($wpt->{'shape'} eq 'circle')
    {
        if ($dist < ($wpt->{'radius'}+$wpt->{'margin'})) 
        {
            $made = 1;
        }
    }
    elsif ($wmade > 0 && $wpt->{'shape'} eq 'line')
    {
        # does the track intersect with the semi-circle
        if ($dist < ($wpt->{'radius'}+$wpt->{'margin'}) and (in_semicircle($waypoints, $wmade, $coord)))
        {
            $made = 1;
        }
    }
    
    if ($made == 0) 
    {
        return 0;
    }

    if ($debug)
    {
        print "made entry waypoint ", $wpt->{'number'}, "(", $wpt->{'type'}, ") radius ", $wpt->{'radius'}, " at ", $coord->{'time'}, "\n";
    }

    return 1;
}

sub re_entered_start
{
    my ($waypoints, $coord, $lastin, $reflag) = @_;
    my $wcount = undef;
    my $reset = undef;
    my $newreflag = undef;

    # Might re-enter start/speed section for elapsed time tasks 
    # Check if we did re-enter and set the task "back"
    my $rpt = $waypoints->[$lastin];

    # Re-entered start cyclinder?
    my $rdist = distance($coord, $rpt);
    if ($rpt->{'how'} eq 'entry')
    {
        #print "Repeat check ", $rpt->{'type'}, " (reflag=$reflag lastin=$lastin): dist=$rdist\n";
        if (($rdist < ($rpt->{'radius'}+5)) and ($reflag == $lastin))
        {
            # last point inside ..
            #$starttime = 0 + $coord->{'time'};
            #if (($task->{'type'} eq 'race') && ($starttime > $task->{'sstart'}))
            #{
            #    $starttime = 0 + $task->{'sstart'};
            #}
            #if (($task->{'type'} eq 'speedrun-interval') && ($starttime > $taskss))
            #{
            #    $starttime = 0 + $taskss + floor(($starttime-$taskss)/$interval)*$interval;
            #}
            #$startss = $starttime;
            #$coeff = 0; $coeff2 = 0; 
            #if ($debug)
            #{
            #    print "made startss(entry)=$startss\n";
            #}
            $newreflag = -1;
            $reset = 1;
        }
        elsif ($rdist >= ($rpt->{'radius'}-2))
        {
            #print "Exited entry start/speed cylinder\n";
            $newreflag = $lastin;
        }
    }

    if ($rpt->{'how'} eq 'exit') 
    {
        if (($rdist < ($rpt->{'radius'}+5)) and ($reflag == $lastin))
        {
            #print "re-entered (exit) speed/startss ($lastin) at " . $coord->{'time'} . " maxdist=$maxdist\n";
            $wcount = $lastin;
            #$wpt = $waypoints->[$wcount];
            $newreflag = -1;
        }
        elsif ($rdist >= ($rpt->{'radius'}-2) and ($reflag == -1))
        {
            #print "exited (exit) speed/startss ($lastin) at " . $coord->{'time'} . " maxdist=$maxdist\n";
            $newreflag = $lastin;
            $reset = 1;
        }
    }
    return ($reset, $newreflag, $wcount);
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

sub validate_task
{
    my ($flight, $task, $formula) = @_;
    my ($wpt, $rpt);
    my $coord;
    my ($lastcoord, $preSScoord);
    my $lastmaxcoord;
    my ($awarded,$awtime);
    my ($dist, $rdist, $edist);
    my $penalty;
    my $comment = '';
    my ($wasinstart, $wasinSS);
    my $kmtime = [];
    my $kmmark;
    my %result;
    my (%s1, %s2, %s3);

    # Initialise some working variables
    my $closest = 9999999999;		# Min distance from next waypoint
    my $wcount = 0;					# Index of next Waypoint 
    my $wmade = 0;					# Index of last waypoint I made
    my $stopalt = 0;				# altitude when task was stopped
    my $stoptime = 0;				# Time task was stopped
    my $starttime = undef;			# Time I made start
    my $goaltime = undef;			# Time I made goal (ESS?)
    my $startss = 0;				# Time Start opens
    my $endss = undef;				# Time Start closes
    my $lastin = -1;
    my $reflag = -1;

    if ($debug)
    {
        print Dumper($task);
    }

    # Get some key times
    my $taskss = 0 + $task->{'sstart'};
    my $finish = 0 + $task->{'sfinish'};
    my $interval = 0 + $task->{'interval'};

    my $waypoints = $task->{'waypoints'};
    precompute_waypoint_dist($waypoints);
    $dist = compute_waypoint_dist($waypoints, $wcount-1);
    my $coords = $flight->{'coords'};
    my $awards = $flight->{'awards'};
    my $allpoints = scalar @$waypoints;
    # my $margin = $formula->{'margin'}/100; # Radius Tolerance from Formula, I think we don't need as we use wpt->{'margin'}

    # Next waypoint
    $wpt = $waypoints->[$wcount];

    # Closest waypoint
    my $closestwpt = 0;
    my $closestcoord = 0;

    # Stuff for leadout coeff calculation
    # against starttime (rather than first start time)
    my ($maxdist, $coeff, $coeff2);
    $coeff = 0; $coeff2 = 0; 
    $kmtime = init_kmtime($task->{'ssdistance'});  # Resets LeadOuts
    $maxdist = 0;
    my $taskTime = 0; # PWC TaskTime
    my $bestDistToESS = 0; # PWC bestDistToESS

    # Check for UTC crossover
    my $utcmod = determine_utcmod($task, $coords->[0]);

    # Determine the start gate type and ESS dist
    my ($spt, 						# Start type (entry, exit)
    	$ept, 						# ESS type (entry, exit)
    	$gpt, 						# Goal type (entry, exit, line)
    	$essdist, 					# Distance to ESS
    	$startssdist, 				# Distance to start
    	$endssdist, 				# speed section lenght
    	$totdist) 					# total task distance
    	= task_distance($task);

    # Go through the coordinates and verify the track against the task
    for $coord (@$coords)
    {
        # Check the task isn't finished ..
        $coord->{'time'} = $coord->{'time'} - $utcmod;
        if (defined($task->{'sstopped'}) && !defined($endss)) 
        {
            my $maxtime;

            # PWC elapsed scoring (everyone gets same time on course)
            if ($formula->{'stoppedelapsedcalc'} eq 'shortesttime')
            {
                $maxtime = $task->{'sstopped'} - $task->{'laststart'};
                if ($debug)
                {
                    print "elapsed maxtime=$maxtime\n";
                }
            }

            if (($coord->{'time'} > $task->{'sstopped'}) or
                (defined($maxtime) && ($coord->{'time'} > $starttime + $maxtime)))
            {
                print "Coordinate after stopped time: ", $coord->{'time'}, " ", $task->{'sstopped'}, ".\n";
                # Pilot position and altitude at stopped time
                $stopalt = $coord->{'alt'};
                $stoptime = $coord->{'time'};
                last;
            }
        }
        if ($coord->{'time'} > $task->{'sfinish'})
        {
            print "Coordinate after task finish: ", $coord->{'time'}, " ", $task->{'sfinish'}, ".\n";
            # task is already closed
            last;
        }

        # Might re-enter start/speed section for elapsed time tasks 
        # Check if we did re-enter and set the task "back"
        if (($lastin == $spt)
                and ((($task->{'type'} eq 'race') and ($starttime < $task->{'sstart'})) or ($task->{'type'} ne 'race')))
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
                    if (($task->{'type'} eq 'race') && ($coord->{'time'} > $task->{'sstart'}))
                    {
                        $starttime = 0 + $task->{'sstart'};		# startgate time
                    }
                    elsif (($task->{'type'} eq 'speedrun-interval') && ($starttime > $taskss))
                    {
                        $starttime = 0 + $taskss + floor(($coord->{'time'}-$taskss)/$interval)*$interval;		#last startgate time before my time
                    }
                    else
                    {
                    	$starttime = 0 + $coord->{'time'};		# my time
                    }

                    $startss = $starttime;
                    $coeff = 0; $coeff2 = 0; 
                    $reflag = -1;
                    if ($debug)
                    {
                        print "made startss(entry)=$startss\n";
                    }
                }
                elsif ($rdist >= ($rpt->{'radius'}-2))
                {
                    $reflag = $lastin;		# I am out of the cylinder
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
                    if (($task->{'type'} eq 'race') && ($coord->{'time'} > $task->{'sstart'}))
                    {
                        $starttime = 0 + $task->{'sstart'};
                    }
                    elsif (($task->{'type'} eq 'speedrun-interval') && ($starttime > $taskss))
                    {
                        $starttime = 0 + $taskss + floor(($coord->{'time'}-$taskss)/$interval)*$interval;
                    }
                    else
                    {
                    	$starttime = 0 + $coord->{'time'};
                    }
                    $startss = $starttime;
                    $coeff = 0; $coeff2 = 0; 
                    if ($debug)
                    {
                        print "made startss(exit)=$startss\n";
                    }
                }
            }
        } # re-enter start
        
        # Get the distance to next waypoint
        my $newdist = distance_flown($waypoints, $wmade, $coord);

        #print "wcount=$wcount wmade=$wmade newdist=$newdist maxdist=$maxdist starttime=$starttime time=", $coord->{'time'}, "\n";

        # Work out leadout coeff / maxdist if we've moved on
        $taskTime = $coord->{'time'} - $startss;
        $bestDistToESS = ($essdist - $maxdist)/1000;
        my $newDistToESS = ($essdist - $newdist)/1000;
        if (defined($starttime) and ($newdist > $maxdist))
        {
            if (!defined($endss))
            {
                if (defined($lastmaxcoord) && !defined($endss))
                {
                    $coeff = $coeff + $taskTime * ( ($essdist - $maxdist) - ($essdist - $newdist) ); # this is = coeff + tt * (newdist - maxdist) : is it what is meant to be?
                    #$coeff2 = $coeff2 + ($coord->{'time'} - $startss) * ( ($essdist - $maxdist)*($essdist - $maxdist) - ($essdist - $newdist)*($essdist - $newdist) );
                    # distances should be in km
		     		$coeff2 = $coeff2 + $taskTime * ( $bestDistToESS**2 - $newDistToESS**2 );
                }
                $lastmaxcoord = $coord;
                if ($debug)
                {
                    print "newdist=$newdist maxdist=$maxdist time=", ($coord->{'time'} - $startss), " distrem=", ($essdist - $maxdist), " ncoeff=$coeff\n";
                }
            }

            $maxdist = $newdist;
            if (($maxdist >= $startssdist) && (!defined($endss)) 
                && ($kmtime->[floor(($maxdist-$startssdist)/1000)] == 0))
            {
                $kmtime->[floor(($maxdist-$startssdist)/1000)] = $coord->{'time'};
                print "kmtime ($maxdist): ", floor(($maxdist-$startssdist)/1000), ":", $coord->{'time'}, "\n";
            }
            # else { print "new max ($maxdist)\n"; }

            # @todo: Do closestwpt / closestcoord here too?
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
            $awtime = $awards->{$wpt->{'key'}}->{'tadTime'};		# This screws LeadOut calculation
        }

        # Ok - work out if we're in cylinder
        $dist = distance($coord, $wpt);
        # takeoff check
        if ($dist < $wpt->{'radius'} and ($wpt->{'type'} eq 'start'))		# this is the takeoff, we should change name, very confusing
        {
            $wasinstart = $wcount;
        }
        # Start Check
        if ( ($wpt->{'type'} eq 'speed') and ( ( $dist < ($wpt->{'radius'} + $wpt->{'margin'}) and $wpt->{'how'} eq 'exit' ) or ($dist < ($wpt->{'radius'} - $wpt->{'margin'}) and $wpt->{'how'} eq 'entry') ))		# Start Pilon : this could be a Exit point, I think inverted tolerances in this case should work correctly
        {
            #print "wasinSS=$wcount\n";
            $wasinSS = $wcount;
        }
        if ($dist < ($wpt->{'radius'} + $wpt->{'margin'}) || $awarded)
        {
            #print "lastin=$wcount\n";
            $lastin = $wcount;
        }

        #
        # Handle Entry Cylinder
        #
        if ($wpt->{'how'} eq 'entry')
        {
            if (made_entry_waypoint($waypoints, $wmade, $coord, $dist, $awarded))
            {

                # Do task timing stuff
                if (($wpt->{'type'} eq 'start') and (!defined($starttime)) or
                    ($wpt->{'type'} eq 'speed'))
                {
                    # get last start time ..
                    # and in case they were too lazy to put in startss ...
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
                    $coeff = 0; $coeff2 = 0; 
                    if ($debug)
                    {
                        print "1st ", $wpt->{'type'}, "(ent) startss=$startss\n";
                    }
                }
    
                # Goal and speed section checks
                #if (($wpt->{'type'} eq 'goal') and (!defined($goaltime)))
                if ($wcount == $gpt and (!defined($goaltime)))
                {
                    # @todo time should be estimated for the actual
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
    
                if ($wcount == $ept and (!defined($endss)))
                {
                    # @todo time should be estimated for the actual
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
        } # entry
        else 
        {
            # Handle exit cylinder
            if ((($dist >= ($wpt->{'radius'} - $wpt->{'margin'})) || $awarded == 1) and ($lastin == $wcount)) # added margin
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
                    $coeff = 0; $coeff2 = 0;
                    $reflag = -1;
                    #print "start(exit)=$startss\n";
                    if ($task->{'type'} eq 'race')
                    {
                        $startss = 0 + $task->{'sstart'};
                    }
                    if ($debug)
                    {
                        print "made startss=$startss\n";
                    }
                }
    
                # Goal and speed section checks
                #if (($wpt->{'type'} eq 'goal') and (!defined($goaltime)))
                if ($wcount == $gpt and (!defined($goaltime)))
                {
                    # @todo time should be estimated for the actual
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
    
                if ($wcount == $ept and (!defined($endss)))
                {
                    # @todo time should be estimated for the actual
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
                        # @todo - should only check exit cylinders and handle an entry with same centre separately?
                        if (compare_centres($waypoints->[$nextwp-1], $waypoints->[$nextwp]) == 0)
                        {
                            last;
                        }
                        $nextwp++;
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
        } # exit

        $lastcoord = $coord;
    } # end of main coordinate loop

    # Some startss corrections and checks
    #   starttime -  actual start time
    #   startss - start of task time (back to gate)
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
    print "sstartclose=", $task->{'sstartclose'}, " sstart=", $task->{'sstart'}, "\n";
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
    if ( ($task->{'class'} ne 'PG') and ($task->{'type'} ne 'route') and defined($starttime) and (($starttime < $startss) or ($starttime < $taskss)) and ($wmade > $spt))
    {
        my $jump;
        print "Jumped the start gate ($spt) (taskss=$taskss finish=$finish) (startss=$startss: $starttime)\n";
        $jump = $taskss - $startss;
        $comment = "jumped $jump secs";
        # clear leadout markers
        $kmtime = init_kmtime($task->{'ssdistance'});
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
            $coeff = $coeff + $essdist*($startss-$taskss);
            $coeff2 = $coeff2 + ($essdist/1000)**2 * ($startss-$taskss);
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
    my $dist_flown;
    print "wcount=$wcount wmade=$wmade\n";
    
    if ($wcount < $wmade)
    {
        $wcount = $wmade;
    }

    if ($wmade == 0)
    {
        print "Didn't make the start / TO\n";
        $s2{'lat'} = $waypoints->[$wcount+1]->{'short_lat'};
        $s2{'long'} = $waypoints->[$wcount+1]->{'short_long'};
        if ($closestcoord != 0)
        {
            $dist_flown = short_dist($waypoints->[$wcount], $waypoints->[$wcount+1]) - distance($closestcoord, \%s2);
            if ($dist_flown > $waypoints->[0]->{'radius'})
            {
                $dist_flown = $waypoints->[0]->{'radius'};
            }
        }
        else
        {
            $dist_flown = 0;
        }
        if ($dist_flown < 0)
        {
            print "No distance achieved\n";
            $dist_flown = 0;
        }
        print "wcount=0 dist=$dist_flown\n";
        #$coeff = $coeff + ($essdist - $dist_flown)*($task->{'sfinish'}-$startss);
        $coeff = $essdist * ($task->{'sfinish'}-$task->{'sstart'});
        $coeff2 = ($essdist/1000)**2 * ($task->{'sfinish'}-$task->{'sstart'}); # Did not takeoff? Did fly but to T/O wpt?
    }
    elsif ($wcount == 0)
    {
        print "Didn't make startss ($maxdist), closest wpt=$closestwpt\n";
        $dist_flown = $maxdist; # short_dist($waypoints->[$wcount], $waypoints->[$wcount+1]); # - distance($closestcoord, \%s2);
        print "wcount=0 dist=$dist_flown\n";
        $coeff = $essdist * ($task->{'sfinish'}-$task->{'sstart'});
        $coeff2 = ($essdist/1000)**2 * ($task->{'sfinish'}-$task->{'sstart'});
    }
    elsif ($wcount < $allpoints)
    {
        # we didn't make it into goal
        my $remainingss;
        my $cwclosest;

        $dist_flown = $maxdist; # distance_flown($waypoints, $wmade, $closestcoord);
        $remainingss = $essdist - $dist_flown + $startssdist;

        # add rest of (distance_short * $task->{'sfinish'}) to coeff
        print "Incomplete ESS wcount=$wcount dist=$dist_flown remainingss=$remainingss: ", $remainingss*($task->{'sfinish'}-$startss), "\n";
        
        # Leadout point Calculation for landed out pilots
        if (!defined($endss))
        {
            $coeff = $coeff + $essdist * ($startss - $taskss) + $remainingss * ($task->{'sfinish'}-$coord->{'time'});
            $coeff2 = $coeff2 +  ($remainingss/1000)**2 *  ($task->{'sfinish'} - $startss ); # we need to do this after other operations
        }
    }
    else
    {
        # Goal
        print "goal (dist=$totdist)\n";
        $dist_flown = $totdist; # compute_waypoint_dist($waypoints, $wcount-1);
    }

    # sanity ..
    if ($dist_flown < 0)
    {
        printf "Somehow the distance ($dist_flown) is < 0\n";
        $dist_flown = 0;
    }

    $result{'start'} = 0+$starttime;
    $result{'goal'} = $goaltime;
    $result{'startSS'} = $startss;
    $result{'endSS'} = $endss;
    $result{'distance'} = $dist_flown;
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
    print "## coeff=$coeff essdist=$essdist\n";
    $result{'coeff'} = $coeff / 1800 / $essdist;
    
#     # C.6.3.1
#     Commented because we are doing this adjustment in PWC.pm ordered_result
#     if (!defined($endss))
#     {
#     	$result{'coeff2'} = $coeff2 / (1800 * ($essdist/1000)**2) +  ($remainingss/1000)**2 *  ($task->{'sfinish'} - $startss );
#     }
#     else
#     {
#     	$result{'coeff2'} = $coeff2 / (1800 * ($essdist/1000)**2);
#     }

	$result{'coeff2'} = $coeff2 / (1800 * ($essdist/1000)**2);
	
    print "    coeff=", $result{'coeff'}, " coeff2=", $result{'coeff2'}, "\n";
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

sub apply_handicap
{
    my ($task, $flight, $result) = @_;
    my $handicap = 0;
    my $ref;
    my $origdist = $result->{'distance'};
    
    my $sth = $dbh->prepare("select hanHandicap from tblHandicap where pilPk=? and comPk=?");
    $sth->execute($flight->{'pilPk'}, $task->{'comPk'});
    if ($ref = $sth->fetchrow_hashref())
    {
        $handicap = 0.0 + $ref->{'hanHandicap'};
    }

    #if ($debug)
    {
        print "    handicap=$handicap, ", $flight->{'pilPk'}," ",  $task->{'comPk'}, "\n";
    }

    if ($handicap == 0)
    {
        return $result;
    }

    if ($result->{'endSS'} > 0)
    {
        my $tmdif = $result->{'endSS'} - $result->{'startSS'} - 3600;
        if ($tmdif > 0)
        {
            $tmdif = $tmdif / $handicap + 3600;
            $result->{'endSS'} = $result->{'startSS'} + $tmdif;
        }

        if ($result->{'distance'} < $task->{'short_distance'})
        {
            $result->{'distance'} *= $handicap ;
        }
    }
    else
    {
        $result->{'distance'} *= $handicap;
        $result->{'coeff'} *= $handicap;
    }

    if ($result->{'distance'} > $task->{'short_distance'})
    {
        my ($spt, $ept, $gpt, $essdist, $startssdist, $endssdist, $totdist) = task_distance($task);
        my $ssdist = $essdist - $startssdist;

        print "    handicap essdist=$essdist startssdist=$startssdist ssdist=$ssdist result dist=", $result->{'distance'}, "\n";
        my $multi =  $ssdist / ($origdist - $startssdist);

        $result->{'distance'} = $task->{'short_distance'};
        if ($result->{'endSS'} == 0)
        {
            # Calculate a time
            print "    handicap time multi=$multi stoptime=", $result->{'stoptime'}, " startSS=", $result->{'startSS'}, "\n";
            $result->{'endSS'} = ($result->{'stoptime'} - $result->{'startSS'}) * $multi + $result->{'startSS'};
            $result->{'goal'} = $result->{'endSS'};
        }
    }

    # No leadout 
    $result->{'kmtime'} = undef;

#    $result{'closest'} = distance($closestcoord, $waypoints->[$closestwpt]);
#    $result{'waypoints_made'} = $wcount;

    return $result;
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
    my $formula = read_formula($task->{'comPk'});
    $info = validate_task($flight, $task, $formula);
}
#print Dumper($info);

my $comp = read_competition($task->{'comPk'});
if ($comp->{'type'} eq 'RACE-handicap')
{
    $info = apply_handicap($task, $flight, $info);
}

# Store results in DB
store_result($flight,$info);

