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
#use TrackLib qw(:all);


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

    # Launch Validity
    $x = $taskt->{'launched'}/$taskt->{'pilots'};
    $launch  = 0.028*$x + 2.917*$x*$x - 1.944*$x*$x*$x;
    $launch = $self->min([1, $launch]);
    if ($taskt->{'launchvalid'} == 0 or $launch < 0)
    {
        print "Launch invalid - dist quality set to 0\n";
        $launch = 0;
    }
    print "launch quality=$launch\n";

    # Distance Validity
    $distance = 2*($taskt->{'distance'}-$taskt->{'launched'}*$formula->{'mindist'}) / ($taskt->{'launched'}*(1+$formula->{'nomgoal'}/100)*($formula->{'nomdist'}-$formula->{'mindist'}))*($formula->{'nomgoal'}*($taskt->{'maxdist'}-$formula{'nomdist'}));
    $distance = $self->min([1, $distance]);
    print "distance validity=$distance\n";

    # Time Validity
    if ($taskt->{'goal'} > 0)
    {
        $tmin = $taskt->{'tqtime'};
        $x = $tmin / ($formula->{'nomtime'});
    }
    else
    {
        # FIX: check thisa .. should we actually check the leader's time?
        #print "DQ: maxdist=", $taskt->{'maxdist'}, " nomdist=", $formula->{'nomdist'}, "\n";
        $x = $taskt->{'maxdist'} / $formula->{'nomdist'};
    }

    $time = 1;
    if ($x < 1)
    {
        $time = -0.271 + 2.912*$x - 2.098*$x*$x + 0.457*$x*$x*$x;
        $time = $self->min([1, $time]);
    }
    if ($time < 0.1) 
    {
        $time = 0.1;
    }
    print "time quality (tmin=$tmin x=$x)=$time\n";

    # Stop Validity
    # Fix - need $distlaunchtoess, $landed
    my $avgdist = $taskt->{'distance'} / $taskt->{'launched'};
    my $distlaunchtoess = $taskt->{'endssdistance'};
    # when calculating $stopv, to avoid dividing by zero when max distance is greater than distlaunchtoess i.e. when someone reaches goal if statement added.
    my $maxSSdist = 0;
    if (0<($distlaunchtoess - $taskt->{'maxdist'}))
    {
	$maxSSdist = ($distlaunchtoess - $taskt->{'maxdist'});
    }

    $x = ($taskt->{'landed'} / $taskt->{'launched'});
    print "sqrt( ($taskt->{'maxdist'} - $avgdist) / ($distlaunchtoess - $taskt->{'maxdist'}+1) * sqrt($taskt->{'stddev'} / 5) + $x*$x*$x )\n";
    my $stopv = sqrt( ($taskt->{'maxdist'} - $avgdist) / ($maxSSdist+1) * sqrt($taskt->{'stddev'} / 5) + $x*$x*$x );
    $stopv = $self->min([1, $stopv]);

    return ($distance,$time,$launch,$stopv);
}

sub points_weight
{
    my ($self, $task, $taskt, $formula) = @_;
    my $quality;
    my $distweight;
    my ($Adistance, $Aspeed, $Astart, $Aarrival);
    my $x;
    my $dem;
    my $speedweight;


    $quality = $taskt->{'quality'};
    $x = $taskt->{'ess'} / $taskt->{'launched'}; #changed from goal to ess as per pwca

    if ($formula->{'weightdist'} eq 'post2014')
    {
        $distweight = 0.9-1.665*$x+1.713*$x*$x-0.587*$x*$x*$x;
    }
    else
    {
        $distweight = 1-0.8*sqrt($x);
    }

    # 1998 - 1999 - (speed 6 / start 1 / arrival 1) / 8
    # 2000 - 2007 - (5.6 / 1.4 / 1) / 8
    $Adistance = 1000 * $quality * $distweight;
    $Astart = 1000 * $quality * (1-$distweight) * $formula->{'weightstart'};
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

    print "points_weight: (", $formula->{'version'}, ") Adist=$Adistance, Aspeed=$Aspeed, Astart=$Astart, Aarrival=$Aarrival\n";
    return ($Adistance, $Aspeed, $Astart, $Aarrival);

}

sub pilot_departure_leadout
{
    my ($self, $formula, $task, $taskt, $pil, $Astart, $Aspeed) = @_;
    my $x = 0;
    my $Parrival = 0;
    my $Cmin = $taskt->{'mincoeff2'};
	my $lfactor;
    # Pilot departure score
    # print Dumper($pil);

    my $Pdepart = 0;
    if ($task->{'departure'} eq 'leadout')
    {
        print "    leadout: ", $pil->{'coeff'}, ", $Cmin\n";
        if ($pil->{'coeff'} > 0)
        {
            if ($pil->{'coeff'} <= $Cmin)
            {
                $Pdepart = $Astart;
				print "coeff less than min";
            }
            elsif ($Cmin <= 0)
            {
                # this shouldn't happen
                $Pdepart = 0;
            }
            else
            {
				$lfactor = (1-(($pil->{'coeff'}-$Cmin)*($pil->{'coeff'}-$Cmin)/sqrt($Cmin))**(1/3));
				
				#get the minimum of zero and lead factor as per PWCA rules 2016 C.6.3
				
				if ($lfactor > 0) 
				{
                 $Pdepart = $Astart * $lfactor;
				}
				else
				{
				$Pdepart = 0;
				}
				print "pdepart: ", $Pdepart, "\n";
			}
        }
    }
    elsif ($task->{'departure'} eq 'kmbonus')
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
    elsif ($task->{'departure'} eq 'off')
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

    # print "    Pdepart: $Pdepart\n";
    return $Pdepart;
}

sub pilot_speed
{
    my ($self, $formula, $task, $taskt, $pil, $Aspeed) = @_;

    my $Tmin = $taskt->{'fastest'};
    my $Pspeed;
    my $Ptime = 0;

    if ($pil->{'time'} > 0)
    {
        $Ptime = $pil->{'time'};
    }

    print $pil->{'traPk'}, " Ptime: $Ptime, Tmin=$Tmin\n";

    if ($Ptime > 0)
    {
        $Pspeed = $Aspeed * (1-(($Ptime-$Tmin)/3600/sqrt($Tmin/3600))**(5/6));  #Changed from 2/3 to 5/6 as per PWCA
    }
    else
    {
        $Pspeed = 0;
    }

    if ($Pspeed < 0)
    {
        $Pspeed = 0;
    }

    if (0+$Pspeed != $Pspeed)
    {
        print $pil->{'traPk'} , " Pspeed is nan: pil->{'time'}=", $Ptime, "\n";
        $Pspeed = 0;
    }

    return $Pspeed;
}


sub ordered_results
{
    my ($self, $dbh, $task, $taskt, $formula) = @_;
    my @pilots;
	my $maxtime =0;

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
        # set pilot to min distance if they're below that ..
        print "sstopped=", $task->{'sstopped'}, " stopalt=", $taskres{'stopalt'}, " glidebonus=", $formula->{'glidebonus'}, "\n";
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
        # Leadout Points
        $taskres{'coeff'} = $ref->{'tarLeadingCoeff2'};
        # FIX: adjust against fastest ..
        if ((($ref->{'tarES'} - $ref->{'tarSS'}) < 1) and ($ref->{'tarSS'} > 0)) #only pilots that started and didn't make ESS
        {
            # Fix - busted if no one is in goal?
            if ($taskt->{'goal'} > 0)
            {
				$maxtime = $taskt->{'lastarrival'};
				if ($ref->{'tarLastTime'}>$taskt->{'lastarrival'})
				{
				$maxtime = $ref->{'tarLastTime'};
				}
                # adjust for late starters
                print "No goal, adjust pilot coeff from: ", $ref->{'tarLeadingCoeff2'};
                #$taskres{'coeff'} = $ref->{'tarLeadingCoeff2'} - ($task->{'sfinish'} - $taskt->{'lastarrival'}) * ($task->{'endssdistance'} - $ref->{'tarDistance'}) / 1800 / $task->{'ssdistance'} ;
            	$taskres{'coeff'} = $ref->{'tarLeadingCoeff2'} - (($task->{'sfinish'} - $maxtime) * (($task->{'endssdistance'}/1000 - $ref->{'tarDistance'}/1000) *($task->{'endssdistance'}/1000 - $ref->{'tarDistance'}/1000)) / (1800 *($task->{'ssdistance'}/1000)* ($task->{'ssdistance'}/1000))) ;
                print " to: ", $taskres{'coeff'}, "\n";
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

