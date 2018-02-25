#!/usr/bin/perl -I/home/geoff/bin


#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2016
#
# PWC differences
# 1. No arrival points (go to time) if ESS != Goal
# 1a. Altitude Arrival points if ESS == Goal (wtf?) (@todo)
# 2. LC2 - lead coeff^2
# 3. Launch validity altered?
# 4. Stopped task different
#       - if in goal - subtract time points == goal at ESS task stop time
#       - if pilot has made ESS, then complete flight is scored even after task stop time
#       - if not a race, then every pilot scored for the time in the air of the last pilot to start

package PWC;

require Gap;
@ISA = ( "Gap" );

#require DBD::mysql;
#use POSIX qw(ceil floor);
#use Math::Trig;

use Data::Dumper;

# Add currect bin directory to @INC
# use lib '/var/www/cgi-bin';
# use TrackLib qw(:all);


#
# Calculate Task Validity - PWC 2016
# 
# dayQ = launchV * distanceQ * timeV * stopV
#

sub day_quality
{
    my ($self, $taskt, $formula) = @_;
    my $launch = 0;
    my $distance = 0;
    my $time = 0;
    my $topspeed;
    my $x;

    if ($taskt->{'pilots'} == 0)
    {
        $launch = 0;
        $distance = 0;
        $time = 0.1;
        return ($distance,$time,$launch);
    }

    # C.4.1 Launch Validity
    # LVR = min (1, (num pilots launched + nominal launch) / total pilots )
    # Launch Validity = 0.028*LRV + 2.917*LVR^2 - 1.944*LVR^3
    # Setting Nominal Launch = 10 (max number of DNF that still permit full validity)
    
    my $nomlau = 10;
    $x = ($taskt->{'launched'} + $nomlau) / $taskt->{'pilots'};
    $x = $self->min([1, $x]);
    $launch  = 0.028*$x + 2.917*$x*$x - 1.944*$x*$x*$x;
    if ($taskt->{'launchvalid'} == 0 or $launch < 0)
    {
        print "Launch invalid - dist quality set to 0\n";
        $launch = 0;
    }
    print "PWC launch validity = $launch\n";

    # C.4.2 Distance Validity
    # DVR = (Total flown Distance over MinDist) / [ (PilotsFlying / 2) * (NomGoal +1) * (NomDist - MinDist) * NomGoal * (BestDist - NomDist) ]
    # DistVal = min (1, DVR)
    
    my $nomgoal = $formula->{'nomgoal'}/100; # nom goal percentage
    my $nomdist = $formula->{'nomdist'};	# nom distance
    my $mindist = $formula->{'mindist'};	# min distance
    my $totalflown = $taskt->{'distovermin'}; # total distance flown by pilots over min. distance
    my $bestdistovermin = $taskt->{'maxdist'}-$formula->{'nomdist'}; # best distance flown ove minimum dist.
    my $numlaunched = $taskt->{'launched'}; # Num Pilots flown
    my $nomdistarea = 0;
    
    print "nom goal * best dist over min : " . $nomgoal * $bestdistovermin . "\n";
    
    # $distance = 2 * $totalflown / ( $taskt->{'launched'} * ( (1+$nomgoal) * (int( $formula->{'nomdist'}-$formula->{'mindist'}) + .5 ) ) * ($nomgoal * $bestdist) );
    if ( ($nomgoal * $bestdistovermin) > 0 )
    {
    	print "It is positive\n";
    	$nomdistarea = ( ($nomgoal + 1) * ($nomdist - $mindist) + ($nomgoal * $bestdistovermin) ) / 2;
    	print "NomDistArea : $nomdistarea\n";
    }
    else
    {
    	print "It is negative or null";
    	$nomdistarea = ($nomgoal + 1) * ($nomdist - $mindist) / 2;
    }
 
	print "Nom. Goal parameter: $nomgoal\n";
    print "Min. Distance : $mindist\n";
    print "Nom. Distance: $nomdist\n";
    print "Total Flown Distance : $taskt->{'distance'}\n";
    print "Total Flown Distance over min. dist. : $totalflown\n";
    print "Pilots launched : $numlaunched\n";
    print "Best Distance: $bestdistovermin\n";
    print "NomDistArea : $nomdistarea\n";
    
    $distance = $totalflown / ($numlaunched * $nomdistarea);
    $distance = $self->min([1, $distance]);
    

    print "Total : ". $totalflown / ($numlaunched * $nomdistarea) . "\n";
    print "PWC distance validity = $distance\n";

    # C.4.3 Time Validity
    # if no pilot @ ESS
    # TVR = min(1, BestDist/NomDist)
    # else
    # TVR = min(1, BestTime/NomTime)
    # TimeVal = max(0, min(1, -0.271 + 2.912*TVR - 2.098*TVR^2 + 0.457*TVR^3))
    
    if ($taskt->{'ess'} > 0)
    {
        $tmin = $taskt->{'tqtime'};
        $x = $tmin / ($formula->{'nomtime'});
        print "ess > 0, x before min $x\n";
        $x = $self->min([1, $x]);
        print "ess > 0, x = $x\n";
    }
    else
    {
        $x = $taskt->{'maxdist'} / $formula->{'nomdist'};
        print "none in goal, x before min $x\n";
        $x = $self->min([1, $x]);
        print "none in goal, x = $x\n";
    }

	$time = -0.271 + 2.912*$x - 2.098*$x*$x + 0.457*$x*$x*$x;
	print "time quality before min $time\n";
	$time = $self->min([1, $time]);
	print "time quality before max $time\n";
	$time = $self->max([0, $time]);
	
    print "PWC time validity (tmin=$tmin x=$x) = $time\n";

    # C.7.1 Stopped Task Validity
    # If ESS > 0 -> StopVal = 1
    # else StopVal = min (1, sqrt((bestDistFlown - avgDistFlown)/(TaskDistToESS-bestDistFlown+1)*sqrt(stDevDistFlown/5))+(pilotsLandedBeforeStop/pilotsLaunched)^3)
    # Fix - need $distlaunchtoess, $landed
    my $avgdist = $taskt->{'distance'} / $taskt->{'launched'};
    my $distlaunchtoess = $taskt->{'endssdistance'};
    # when calculating $stopv, to avoid dividing by zero when max distance is greater than distlaunchtoess i.e. when someone reaches goal if statement added.
    my $maxSSdist = 0;
    if ( defined($taskt->{'fastest'} ) and $taskt->{'fastest'} > 0 )
    {
		$stopv = 1;
    }
	else
	{	
		$x = ($taskt->{'landed'} / $taskt->{'launched'});
    	print "sqrt( ($taskt->{'maxdist'} - $avgdist) / ($distlaunchtoess - $taskt->{'maxdist'}+1) * sqrt($taskt->{'stddev'} / 5)) + $x*$x*$x \n";
    	my $stopv = sqrt( ($taskt->{'maxdist'} - $avgdist) / ($maxSSdist+1) * sqrt($taskt->{'stddev'} / 5) ) + $x**3 ;
    	$stopv = $self->min([1, $stopv]);
    }

    return ($distance,$time,$launch,$stopv);
}

sub points_weight
{
    my ($self, $task, $taskt, $formula) = @_;
    my $quality;
    my $distweight;
    my ($Adistance, $Aspeed, $Astart, $Aarrival);
    my $leadweight;
    my $x;
    my $dem;
    my $speedweight;


    $quality = $taskt->{'quality'};
    $x = $taskt->{'ess'} / $taskt->{'launched'}; #GoalRatio
	
	# DistWeight = 0.9 - 1.665* goalRatio + 1.713*GolalRatio^2 - 0.587*goalRatio^3
	
	# Condition unnecessary? what post2014?
    if ($formula->{'weightdist'} eq 'post2014')
    {
        $distweight = 0.9 - 1.665 * $x + 1.713 * $x * $x - 0.587 * $x*$x*$x;
        print "PWC 2016 Points Allocatiom distWeight = $distweight \n";
    }
    else
    {
        $distweight = 1 - 0.8 * sqrt($x);
        print "NOT Using 2016 Points Allocatiom distWeight = $distweight \n";
    }

    # 1998 - 1999 - (speed 6 / start 1 / arrival 1) / 8
    # 2000 - 2007 - (5.6 / 1.4 / 1) / 8
    
    # leadingWeight = (1-distWeight)/8 * 1.4
    $leadweight = (1 - $distweight)/8 * 1.4;
    print "LeadingWeight = $leadweight \n";
    $Adistance = 1000 * $quality * $distweight; # AvailDistPoints
    print "Available Dist Points = $Adistance \n";
    $Astart = 1000 * $quality * $leadweight; # AvailLeadPoints
    print "Available Lead Points = $Astart \n";
 
 	## Old stuff - probably jettison
 	#$Astart = 1000 * $quality * (1-$distweight) * $formula->{'weightstart'};
    $Aarrival = 1000 * $quality * (1-$distweight) * $formula->{'weightarrival'};
    $speedweight = $formula->{'weightspeed'};

    if ($task->{'arrival'} eq 'off')
    {
        $Aarrival = 0;
        $speedweight += $formula->{'weightarrival'};
    }

    if ($task->{'departure'} eq 'off')
    {
        $Astart = 0;
        $speedweight += $formula->{'weightstart'};
    }

    $Aspeed = 1000 * $quality * (1-$distweight) * $speedweight;

    if ($formula->{'scaletovalidity'})
    {
        $dem = $Adistance + $Aspeed + $Aarrival + $Astart;
        $Adistance = 1000 * $quality * $Adistance / $dem;
        $Aspeed = 1000 * $quality * $Aspeed / $dem;
        $Aarrival = 1000 * $quality * $Aarrival / $dem;
        $Astart =  1000 * $quality * $Astart / $dem;
    }
	## old stuff end
	
	# resetting $speedweight and $Aspeed using PWC2016 formula
	$Aspeed = 0;
	$speedweight = 1 - $distweight - $leadweight;
	$Aspeed = 1000 * $quality * $speedweight; # AvailSpeedPoints
	print "Available Speed Points = $Aspeed \n";
	
    print "points_weight: (", $formula->{'version'}, ") Adist=$Adistance, Aspeed=$Aspeed, Astart=$Astart, Aarrival=$Aarrival\n";
    return ($Adistance, $Aspeed, $Astart, $Aarrival);

}

sub pilot_departure_leadout
{
	# C.6.3 Leading Points
	
    my ($self, $formula, $task, $taskt, $pil, $Astart, $Aspeed) = @_;
    my $x = 0;
    my $Parrival = 0;
    my $LCmin = $taskt->{'mincoeff2'}; # min(tarLeadingCoeff2) as MinCoeff2 : is PWC's LCmin?
    my $LCp = $pil->{'coeff'}; # Leadout coefficient did not understand how calculated though
    my $LF = 0; #LeadingFactor

    # Pilot departure score
    # print Dumper($pil);

    my $Pdepart = 0;
    if ($task->{'departure'} eq 'leadout') # In PWC is always the case, we can ignore else cases
    {
        print "  - PWC  leadout: LC ", $LCp, ", LCMin : $LCmin\n";
        if ($LCp > 0)
        {
            if ($LCp <= $LCmin) # ??
            {
                print "======= being LCp <= LCmin  ========= \n";
                $Pdepart = $Astart;
            }
            elsif ($LCmin <= 0) # ??
            {
                # this shouldn't happen
                print "=======  being LCmin <= 0   ========= \n";
                $Pdepart = 0;
            }
            else # We should have ONLY this case
            {
                #$Pdepart = $Astart * (1-(($LCp-$LCmin)*($LCp-$LCmin)/sqrt($LCmin))**(1/3));
                #$Pdepart = $Alead * (1-(($LCp-$LCmin)*($LCp-$LCmin)/sqrt($LCmin))**(1/3)); # Why $Alead is not working?
                
                # LeadingFactor = max (0, 1 - ( (LCp -LCmin) / sqrt(LCmin) )^(2/3))
                # LeadingPoints = LeadingFactor * AvailLeadPoints
                $LF = 1 - ( ($LCp - $LCmin)**2 / sqrt($LCmin) )**(1/3);
                print "LeadFactor = $LF \n";
                if ($LF > 0)
                {
                	$Pdepart = $Astart * $LF;
                	print "=======  Normal Pdepart   ========= \n";
                }
            }
        }
        print "======= PDepart = $Pdepart  ========= \n";
    }
    elsif ($task->{'departure'} eq 'kmbonus') # We do NOT need this in PWC scoring
    {
        my $kmarr = $taskt->{'kmmarker'};
        my @tmarker = @$kmarr;

        #print "TMARKER=", Dumper(\@tmarker);
        # KmBonus award points
        if (scalar(@tmarker) > 0)
        {
            #print "Astart=$Astart PKM=", Dumper($pil->{'kmmarker'});
            for my $km (1..scalar(@tmarker))
            {
                if ($pil->{'kmmarker'}->[$km] > 0 && $tmarker[$km] > 0)
                {
                    #$x = 1 - ($pil->{'kmmarker'}->[$km] - $tmarker[$km]) / ($tmarker[$km]/4);
                    $x = 1 - ($pil->{'kmmarker'}->[$km] - $tmarker[$km]) / 600;
                    if ($x > 0)
                    {
                        $Pdepart = $Pdepart + (0.2+0.037*$x+0.13*($x*$x)+0.633*($x*$x*$x));
                    }
                }
            }
            $Pdepart = $Pdepart * $Astart * 1.25 / floor($task->{'ssdistance'}/1000.0);
            if ($Pdepart > $Astart)
            {
                $Pdepart = $Astart;
            }
        }
        else
        {
            $Pdepart = 0;
        }
    }
    elsif ($task->{'departure'} eq 'off') # We do NOT need this in PWC scoring
    {
        $Pdepart = 0;
        # print "    depart off\n";
    }
    else
    {
        # Normal departure points ..
        $x = ($pil->{'startSS'} - $taskt->{'firstdepart'})/$formula->{'nomtime'};
        # print "    normal departure x=$x\n";
        if ($x < 1/2 && $pil->{'time'} > 0)
        {
            my $Pspeed = $self->pilot_speed($formula, $task, $taskt, $pil, $Aspeed);

            $Pdepart = $Pspeed*$Astart/$Aspeed*(1-6.312*$x+10.932*($x*$x)-2.990*($x*$x*$x));
            #$Pdepart = $Astart*(1-6.312*$x+10.932*($x*$x)-2.990*($x*$x*$x));
            #$Pdepart = $Aspeed/6*(1-6.312*$x+10.932*($x*$x)-2.990*($x*$x*$x));
        }
    }

    # Sanity
    if (0+$Pdepart != $Pdepart)
    {
        # print "    Pdepart is nan\n";
        $Pdepart = 0;
    }

    if ($Pdepart < 0)
    {
        $Pdepart = 0;
    }

    print "    Pdepart: $Pdepart\n";
    return $Pdepart;
}

sub pilot_speed
{
    # C.6.2 Time Points
    
    my ($self, $formula, $task, $taskt, $pil, $Aspeed) = @_;

    my $Tmin = $taskt->{'fastest'};
    my $Pspeed = 0;
    my $Ptime = 0;
    my $SF = 0; # SpeedFraction

    if ( $pil->{'time'} > 0 and $Tmin > 0 ) # checking that task has pilots in ESS, and that pilot is in ESS
    {
        $Ptime = $pil->{'time'};
        $SF = 1 - ( ($Ptime-$Tmin)/3600 / sqrt($Tmin/3600) )**(5/6);
		if ($SF > 0)
		{
			$Pspeed = $Aspeed * $SF;
		}
    }

    print $pil->{'traPk'}, " Ptime: $Ptime, Tmin=$Tmin\n";

#     if ($Ptime > 0) # ?? Already checked
#     {
#         $Pspeed = $Aspeed * (1-(($Ptime-$Tmin)/3600/sqrt($Tmin/3600))**(5/6));  #Changed from 2/3 to 5/6 as per PWCA
#     }
#     else
#     {
#         $Pspeed = 0;
#     }
# 
#     if ($Pspeed < 0)
#     {
#         $Pspeed = 0;
#     }
# 
#     if (0+$Pspeed != $Pspeed)
#     {
#         print $pil->{'traPk'} , " Pspeed is nan: pil->{'time'}=", $Ptime, "\n";
#         $Pspeed = 0;
#     }
	
	# SpeedFraction = max (0, 1 - ( (Time - BestTime) / sqrt(bestTime) )^(5/6) )
	# TimePoints = SpeedFraction * AvailTimePoints


    return $Pspeed;
}


sub ordered_results
{
    my ($self, $dbh, $task, $taskt, $formula) = @_;
    my @pilots;

    # Get all pilots and process each of them
    # pity it can't be done as a single update ...
    $dbh->do('set @x=0;');
    $sth = $dbh->prepare("select \@x:=\@x+1 as Place, tarPk, tarDistance, tarSS, tarES, tarPenalty, tarResultType, tarLeadingCoeff2, tarGoal, tarLastAltitude from tblTaskResult where tasPk=? and tarResultType <> 'abs' order by case when (tarGoal=0 or tarES is null) then -999999 else tarLastAltitude end, tarDistance desc");
    $sth->execute($task->{'tasPk'});
    while ($ref = $sth->fetchrow_hashref())
    {
        my %taskres;

        %taskres = ();
        $taskres{'tarPk'} = $ref->{'tarPk'};
        $taskres{'penalty'} = $ref->{'tarPenalty'};
        $taskres{'distance'} = $ref->{'tarDistance'};
        $taskres{'stopalt'} = $ref->{'tarLastAltitude'};
        
        # Handle Stopped Task
        # print "sstopped=", $task->{'sstopped'}, " stopalt=", $taskres{'stopalt'}, " glidebonus=", $formula->{'glidebonus'}, "\n";
        if ($task->{'sstopped'} > 0 && $taskres{'stopalt'} > 0 && $formula->{'glidebonus'} > 0)
        {
           if ($taskres{'stopalt'} > $task->{'goalalt'})
           {
                print "Stopped height bonus: ", $formula->{'glidebonus'} * $taskres{'stopalt'}, "\n";
                $taskres{'distance'} = $taskres{'distance'} + $formula->{'glidebonus'} * ($taskres{'stopalt'} - $task->{'goalalt'});
                if ($taskres{'distance'} > $task->{'ssdistance'})
                {
                    $taskres{'distance'} = $task->{'ssdistance'};
                }
            }
        }
        
        # set pilot to min distance if they're below that ..
        if ($taskres{'distance'} < $formula->{'mindist'})
        {
            $taskres{'distance'} = $formula->{'mindist'};
        }
        $taskres{'result'} = $ref->{'tarResultType'};
        $taskres{'startSS'} = $ref->{'tarSS'};
        $taskres{'endSS'} = $ref->{'tarES'};
        $taskres{'timeafter'} = $ref->{'tarES'} - $Tfarr;
        $taskres{'place'} = $ref->{'Place'};
        $taskres{'time'} = $taskres{'endSS'} - $taskres{'startSS'};
        $taskres{'goal'} = $ref->{'tarGoal'};
        if ($taskres{'time'} < 0)
        {
            $taskres{'time'} = 0;
        }
        # Leadout Points Adjustment
        # C.6.3.1
        # 
        $taskres{'coeff'} = $ref->{'tarLeadingCoeff2'}; #PWC LeadCoeff (with squared distances)
        # FIX: adjust against fastest ..
        if ((($ref->{'tarES'} - $ref->{'tarSS'}) < 1) and ($ref->{'tarSS'} > 0)) #only pilots that started and didn't make ESS
        {
            # Fix - busted if no one is in goal?
            if ($taskt->{'goal'} > 0)
            {
				my $maxtime = $taskt->{'lastarrival'};	# Time of the last in ESS
				if ($ref->{'tarLastTime'} > $task->{'sfinish'})
				{
					$maxtime = $task->{'sfinish'}; # If I was still flying after task deadline
				}
				elsif ($ref->{'tarLastTime'} > $taskt->{'lastarrival'})
				{
					$maxtime = $ref->{'tarLastTime'}; # If I was still flying after the last ESS time
				}
                # adjust for late starters
                print "No goal, adjust pilot coeff from: ", $ref->{'tarLeadingCoeff2'};
                my $BestDistToESS = $task->{'endssdistance'}/1000 - $ref->{'tarDistance'}/1000; # PWC bestDistToESS in Km
                # $taskres{'coeff'} = $ref->{'tarLeadingCoeff2'} - (($task->{'sfinish'} - $maxtime) * (($task->{'endssdistance'}/1000 - $ref->{'tarDistance'}/1000)**2 / ( 1800 * ($task->{'ssdistance'}/1000)**2 )) ; # I think it's wrong
                $taskres{'coeff'} = $ref->{'tarLeadingCoeff2'} - ($task->{'sfinish'} - $maxtime) * $BestDistToESS**2 / ( 1800 * ($task->{'ssdistance'}/1000)**2 ) ;
                print " to: ", $taskres{'coeff'}, "\n";
                print "(maxtime - sstart)   =      ", ($maxtime - $task->{'sstart'});
                print "ref->{'tarLeadingCoeff2'} = ", $ref->{'tarLeadingCoeff2'};
                print "Result taskres{coeff}  =    ", $taskres{'coeff'};
                # adjust mincoeff?
                if ($taskres{'coeff'} < $task->{'mincoeff2'})
                {
                    $task->{'mincoeff2'} = $taskres{'coeff'};
                }
            }
        }

        push @pilots, \%taskres;
    }

    return \@pilots;
}

1;