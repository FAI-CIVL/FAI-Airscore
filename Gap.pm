#!/usr/bin/perl -I/home/bin/geoff


#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2007
#
package Gap;

require Exporter;
our @ISA       = qw(Exporter);
#our @EXPORT = qw(:all);

require DBD::mysql;
use POSIX qw(ceil floor);
use Math::Trig;
use Data::Dumper;
use TrackLib qw(:all);
use strict;

sub new
{
    my $class = shift;
    my $self = {};
    # set any defaults here ...
    bless ($self, $class);
    return $self;
}

sub round 
{
    my ($self, $number) = @_;
    return int($number + .5);
}

sub min
{
    my ($self, $list) = @_;
    my $x = ~0 >> 1;

    foreach my $y (@$list)
    {
        $x = $y if $y < $x;
    }
    return $x;
}

sub spread
{
    my ($self, $buc) = @_;
    my $nbuc = [];
    my $sz;

    $sz = scalar @$buc - 1;
    #print "spread: $sz\n";
    $nbuc->[0] = 0.0 + $buc->[0];
    for my $j ( 1 .. $sz )
    {
        $nbuc->[$j-1] = $nbuc->[$j-1] + $buc->[$j] / 3;
        $nbuc->[$j] = $nbuc->[$j] + $buc->[$j] * 2 / 3;
        #$nbuc->[$j+1] = $buc->[$j] / 3;
    }

    return $nbuc;
}

#
# Find the task totals and update ..
#   tasTotalDistanceFlown, tasPilotsLaunched, tasPilotsTotal
#   tasPilotsGoal, tasPilotsLaunched, 
#
# FIX: TotalDistance wrong with 'lo' type results?
#
sub task_totals
{
    my ($self, $dbh, $task, $formula) = @_;
    my $totdist;
    my $launched;
    my $pilots;
    my $mindist;
    my $goal;
    my $ess;
    my $glidebonus;
    my %taskt;
    my $tasPk;
    my ($minarr, $maxarr, $fastest, $firstdep, $mincoeff, $mincoeff2, $tqtime);
    my $launchvalid;
    my $median;
    my $stddev;
    my @distspread;
    my $landed;
    my $kmmarker;
    my $sth;
    my $ref;

    $tasPk = $task->{'tasPk'};
    $launchvalid = $task->{'launchvalid'};
    $mindist = $formula->{'mindist'};
    $glidebonus = 0;
    $landed = 0;

    # @todo: 'Landed' misses people who made ESS but actually landed before goal
    $sth = $dbh->prepare("select count(tarPk) as TotalPilots, sum(if(tarDistance < $mindist, $mindist, tarDistance)) as TotalDistance, sum((tarDistance > 0) or (tarResultType='lo')) as TotalLaunched, std(if(tarDistance < $mindist, $mindist, tarDistance)) as Deviation, sum(if((tarLastAltitude=0 and (tarDistance>0 or tarResultType='lo') or tarGoal>0),1,0)) as Landed FROM tblTaskResult where tasPk=$tasPk and tarResultType <> 'abs'");

    $sth->execute();
    $ref = $sth->fetchrow_hashref();
    $totdist = 0.0 + $ref->{'TotalDistance'};
    $launched = 0 + $ref->{'TotalLaunched'};
    $pilots = 0 + $ref->{'TotalPilots'};
    $stddev = 0 + $ref->{'Deviation'};

    if ($task->{'sstopped'} > 0)
    {
        print "F: glidebonus=$glidebonus\n";
        $glidebonus = $formula->{'glidebonus'};
        $landed = 0 + $ref->{'Landed'};
    }

    # pilots in goal?
    $sth = $dbh->prepare("select count(tarPk) as GoalPilots from tblTaskResult where tasPk=$tasPk and tarGoal > 0");
    $sth->execute();
    $goal = 0;
    if ($ref = $sth->fetchrow_hashref())
    {
        $goal = $ref->{'GoalPilots'};
    }

    # pilots in ESS
    $sth = $dbh->prepare("select count(tarPk) as ESSPilots from tblTaskResult where tasPk=$tasPk and (tarES-tarSS) > 0");
    $sth->execute();
    $ess = 0;
    if ($ref = $sth->fetchrow_hashref())
    {
        $ess  = $ref->{'ESSPilots'};
    }

    $sth = $dbh->prepare("select min(tarES) as MinArr, max(tarES) as MaxArr from tblTaskResult where tasPk=$tasPk and (tarES-tarSS) > 0");
    $sth->execute();
    $maxarr = 0;
    if ($ref = $sth->fetchrow_hashref())
    {
        $minarr = $ref->{'MinArr'};
        $maxarr = $ref->{'MaxArr'};
    }

    $sth = $dbh->prepare("select (tarES-tarSS) as MinTime from tblTaskResult where tasPk=$tasPk and tarES > 0 and (tarES-tarSS) > 0 order by (tarES-tarSS) asc limit 2");
    $sth->execute();
    $fastest = 0;
    while ($ref = $sth->fetchrow_hashref())
    {
        if ($fastest == 0)
        {
            $fastest = $ref->{'MinTime'};
            $tqtime = $fastest;
        }
        else
        {
            $tqtime = $ref->{'MinTime'};
        }
    }

    # Sanity
    if (!$fastest)
    {
        $fastest = 0;
        $minarr = 0;
    }

    # FIX: lead out coeff - first departure in goal and adjust min coeff 
    $sth = $dbh->prepare("select min(tarLeadingCoeff) as MinCoeff from tblTaskResult where tasPk=$tasPk and tarLeadingCoeff is not NULL");
    $sth->execute();
    $mincoeff = 0;
    if ($ref = $sth->fetchrow_hashref())
    {
        $mincoeff = $ref->{'MinCoeff'};
    }

    # FIX: lead out coeff2 - first departure in goal and adjust min coeff 
    $sth = $dbh->prepare("select min(tarLeadingCoeff2) as MinCoeff2 from tblTaskResult where tasPk=$tasPk and tarLeadingCoeff2 is not NULL");
    $sth->execute();
    $mincoeff2 = 0;
    if ($ref = $sth->fetchrow_hashref())
    {
        $mincoeff2 = $ref->{'MinCoeff2'};
    }
    #print "TTT: min leading coeff=$mincoeff\n";

    my $maxdist = 0;
    my $mindept = 0;
    my $lastdept = 0;
    #$sth = $dbh->prepare("select max(tarDistance) as MaxDist from tblTaskResult where tasPk=$tasPk");
    $sth = $dbh->prepare("select max(tarDistance+tarLastAltitude*$glidebonus) as MaxDist from tblTaskResult where tasPk=$tasPk");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref())
    {
        $maxdist = 0 + $ref->{'MaxDist'};
    }
    #if someone got to goal, maxdist should be dist to goal (to avoid stopped glide creating a max dist > task dist)
    if ($goal > 0)
    {
	
   	$sth = $dbh->prepare("select tasShortRouteDistance as GoalDist from tblTask where tasPk=$tasPk");
   	$sth->execute();
 	if ($ref = $sth->fetchrow_hashref())	
	{
		$maxdist = $ref->{'GoalDist'};
    	}
     }

    if ($maxdist < $mindist)
    {
        $maxdist = $mindist;
    }
    #print "TT: glidebonus=$glidebonus maxdist=$maxdist\n";

    $sth = $dbh->prepare("select min(tarSS) as MinDept, max(tarSS) as LastDept from tblTaskResult where tasPk=$tasPk and tarSS > 0 and tarGoal > 0");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref())
    {
        $mindept = $ref->{'MinDept'};
        $lastdept = $ref->{'LastDept'};
    }

    # Find the median distance flown
    $dbh->do('set @rownum=-1;');
    $sth = $dbh->prepare("select avg(TM.dist) as median from ( select \@rownum:=\@rownum+1 AS rownum, TR.tarDistance AS dist FROM tblTaskResult TR where tasPk=$tasPk and tarResultType not in ('abs', 'dnf') ORDER BY tarDistance ) AS TM WHERE TM.rownum IN ( CEIL(\@rownum/2), FLOOR(\@rownum/2))");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref()) 
    {
        $median = $ref->{'median'};
    }
    print "Median=$median\n";

    
    # Find the distance spread
    if ($formula->{'diffcalc'} eq 'lo')
    {
        $sth = $dbh->prepare("select truncate(tarDistance/100,0) as Distance, count(truncate(tarDistance/100,0)) as Difficulty from tblTaskResult where tasPk=$tasPk and tarResultType not in ('abs','dnf') and (tarGoal=0 or tarGoal is null) group by truncate(tarDistance/100,0)");
    }
    else
    {
        $sth = $dbh->prepare("select truncate(tarDistance/100,0) as Distance, count(truncate(tarDistance/100,0)) as Difficulty from tblTaskResult where tasPk=$tasPk and tarResultType not in ('abs','dnf') group by truncate(tarDistance/100,0)");
    }
    $sth->execute();

    while ($ref = $sth->fetchrow_hashref()) 
    {
        push @distspread, $ref;
    }

    # Determine first to reach each 'KM' marker
    $sth = $dbh->prepare("select M.tmDistance, min(M.tmTime) as FirstArrival from 
            tblTrackMarker M, tblComTaskTrack C where C.tasPk=$tasPk and M.traPk=C.traPk and M.tmTime > 0 group by M.tmDistance order by M.tmDistance");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref())
    {
        $kmmarker->[$ref->{'tmDistance'}] = $ref->{'FirstArrival'};
    }

    # task quality 
    $taskt{'pilots'} = $pilots;
    $taskt{'maxdist'} = $maxdist;
    $taskt{'distance'} = $totdist;
    $taskt{'median'} = $median;
    $taskt{'stddev'} = $stddev;
    #$taskt{'taskdist'} = $taskdist;
    $taskt{'landed'} = $landed;
    $taskt{'launched'} = $launched;
    $taskt{'launchvalid'} = $launchvalid;
    #$taskt{'quality'} = $quality;
    $taskt{'goal'} = $goal;
    $taskt{'ess'} = $ess;
    $taskt{'fastest'} = $fastest;
    $taskt{'tqtime'} = $tqtime;
    $taskt{'firstdepart'} = $mindept;
    $taskt{'lastdepart'} = $lastdept;
    $taskt{'firstarrival'} = $minarr;
    $taskt{'lastarrival'} = $maxarr;
    $taskt{'mincoeff'} = $mincoeff;
    $taskt{'mincoeff2'} = $mincoeff2;
    $taskt{'distspread'} = \@distspread;
    $taskt{'kmmarker'} = $kmmarker;
    $taskt{'endssdistance'} = $task->{'endssdistance'};

    return \%taskt;
}

#
# Calculate Task Validity - GAP
#
#  Distance Validity - is the ratio between the area under the ActDistrib and 
#     the area under the NomDistrib. Only the areas above MinDist considered. 
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

    $x = $taskt->{'launched'}/$taskt->{'pilots'};
    $launch  = 0.028*$x + 2.917*$x*$x - 1.944*$x*$x*$x;
    if ($launch > 1) 
    {
        $launch = 1;
    }
    if ($launch < 0) 
    {
        $launch = 0;
    }
    if ($taskt->{'launchvalid'} == 0)
    {
        print "Launch invalid - dist quality set to 0\n";
        $launch = 0;
    }
    print "launch quality=$launch\n";

    $distance = 2*($taskt->{'distance'}-$taskt->{'launched'}*$formula->{'mindist'}) / ($taskt->{'launched'}*(1+$formula->{'nomgoal'}/100)*($formula->{'nomdist'}-$formula->{'mindist'}));
    print "distance quality=$distance\n";
    if ($distance > 1) 
    {
        $distance = 1;
    }
    if ($distance < 0) 
    {
        $distance = 0;
    }
            
    my $tmin;
    if ($taskt->{'ess'} > 0)
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

    if ($x < 1)
    {
        $time = -0.271 + 2.912*$x - 2.098*$x*$x + 0.457*$x*$x*$x;
    }
    else
    {
        $time = 1;
    }
    print "time quality (tmin=$tmin x=$x)=$time\n";
    if ($time > 1) 
    {
        $time = 1;
    }
    if ($time < 0.1) 
    {
        $time = 0.1;
    }

    return ($distance,$time,$launch,1.0);
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
    $x = $taskt->{'goal'} / $taskt->{'launched'};

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

sub calc_kmdiff
{
    my ($self, $task, $taskt, $formula) = @_;
    my $tasPk;
    my $kmdiff = [];
    my $Nlo;
    my $distspread;
    my $difdist;
    my $debc = 0;

    $tasPk = $task->{'tasPk'};
    $Nlo = $taskt->{'launched'}-$taskt->{'goal'};

    # KM difficulty
    for my $it ( 0 .. floor($taskt->{'maxdist'} / 100.0) )
    {
        $kmdiff->[$it] = 0;
    }

    $distspread = $taskt->{'distspread'};
    for my $ref ( @$distspread )
    {
        # populate kmdiff
        # At half the difficulty dist back they get all the points
        $difdist = 0 + $ref->{'Distance'} - ($formula->{'diffdist'}/200);
        if ($difdist < 0) 
        {
            $difdist = 0;
        }
        $kmdiff->[$difdist] = 0 + $kmdiff->[$difdist] + $ref->{'Difficulty'};
        $debc = $debc + $ref->{'Difficulty'};
        #print "dist($difdist): ", $ref->{'Distance'}, " diff: ", $kmdiff->[$difdist], "\n";
        #$kmdiff->[(0+$ref->{'Distance'})] = 0+$ref->{'Difficulty'};
    }

    # Then smooth it out (non-linearly) for the other half
    #print Dumper($kmdiff);
    for my $it ( 0 .. ($formula->{'diffdist'}/200))
    {
        $kmdiff = $self->spread($kmdiff);
    }
    #print Dumper($kmdiff);

    # Determine cumulative distance difficulty 
    my $x = 0.0;
    for my $dif (0 .. scalar @$kmdiff-1)
    {
        my $rdif;

        $rdif = 0.0;

        $x = $x + $kmdiff->[$dif];
        # Use only landed-out pilots or all pilots for difficulty?
        if ($formula->{'diffcalc'} eq 'lo' && $Nlo > 0)
        {
            $rdif = $x/$Nlo;
        }
        else
        {
            $rdif = $x/$taskt->{'launched'};
        }
        $kmdiff->[$dif] = ($rdif);
    }
    # print "debc=$debc x=$x (vs $Nlo)\n";

    return $kmdiff;
}


# Calculate pilot arrival score
sub pilot_arrival
{
    my ($self, $formula, $task, $taskt, $pil, $Aarrival) = @_;
    my $x = 0;
    my $Parrival = 0;

    if ($pil->{'time'} > 0)
    {
        if ($formula->{'arrival'} eq 'timed')
        {
            # OzGAP / Timed arrival
            print "    time arrival ", $pil->{'timeafter'}, ", ", $taskt->{'goal'}, "\n";
            $x = 1-$pil->{'timeafter'}/(90*60);
            $Parrival = $Aarrival*(0.2+0.037*$x+0.13*($x*$x)+0.633*($x*$x*$x));
        }
        else
        {   
            # Place arrival
            print "    place arrival ", $pil->{'place'}, ", ",$taskt->{'ess'}, "\n";
            if ($taskt->{'ess'} > 0)
            {
                $x = 1 - ($pil->{'place'}-1)/$taskt->{'ess'};
                $Parrival = $Aarrival*(0.2+0.037*$x+0.13*($x*$x)+0.633*($x*$x*$x));
            }
            else
            {
                $Parrival = 0;
            }
        }

        if ($Parrival < 0)
        {
            $Parrival = 0;
        }

        print "x=$x parrive=$Parrival\n";
    }

    return $Parrival;
}


sub pilot_departure_leadout
{
    my ($self, $formula, $task, $taskt, $pil, $Astart, $Aspeed) = @_;
    my $x = 0;
    my $Parrival = 0;
    my $Cmin = $taskt->{'mincoeff'};

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
            }
            elsif ($Cmin <= 0)
            {
                # this shouldn't happen
                $Pdepart = 0;
            }
            else
            {
                $Pdepart = $Astart * (1-(($pil->{'coeff'}-$Cmin)/sqrt($Cmin))**(2/3));
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
        $Pspeed = $Aspeed * (1-(($Ptime-$Tmin)/3600/sqrt($Tmin/3600))**(2/3));
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

sub pilot_distance
{
    my ($self, $formula, $task, $taskt, $pil, $Adistance) = @_;

    my $kmdiff = $self->calc_kmdiff($task, $taskt, $formula);
    my $Pdist = $Adistance * 
            (($pil->{'distance'}/$taskt->{'maxdist'}) * $formula->{'lineardist'}
            + $kmdiff->[floor($pil->{'distance'}/100.0)] * (1-$formula->{'lineardist'}));

    # print $pil->{'tarPk'}, " Adist=$Adistance pil->dist=", $pil->{'distance'}, " maxdist=", $taskt->{'maxdist'}, " kmdiff=", $kmdiff->[floor($pil->{'distance'}/100.0)], "\n";
    print $pil->{'traPk'}, " lin dist: ", $Adistance * ($pil->{'distance'}/$taskt->{'maxdist'}) * $formula->{'lineardist'}, " dif dist: ", $Adistance * $kmdiff->[floor($pil->{'distance'}/100.0)] * (1-$formula->{'lineardist'}), "\n";

    return $Pdist;
}

sub pilot_penalty
{
    my ($self, $formula, $task, $taskt, $pil, $astart, $aspeed) = @_;
    my $penalty = 0;
    my $penspeed;
    my $pendist;

# Penalty is in seconds .. convert for OzGap penalty.
#        if ($penalty > 0) 
#        {
#            $penspeed = $penalty;
#            if ($penspeed > 90)
#            {
#                $penspeed = 90;
#            };
#            $penspeed = ($penspeed + 10) / 100;
#            $penspeed = ($Pdepart + $Pspeed) * $penspeed;
#
#            $pendist = 0;
#            $penalty = $penalty - 90;
#            if ($penalty > 0)
#            {
#                if ($penalty > $Tnom / 3)
#                {
#                    $pendist = $Pdist;
#                }
#                else
#                {
#                    $pendist = ((($penalty + 30) / 60) * 2) / 100;
#                    $pendist = $Pdist * $penalty;
#                }
#            }
#
#            print "jumped=$penalty penspeed=$penspeed pendist=$pendist\n";
#
#            $penalty = round($penspeed + $pendist);
#            print "computed penalty=$penalty\n";
#        }

    return $penalty;
}

sub ordered_results
{
    my ($self, $dbh, $task, $taskt, $formula) = @_;
    my $tasPk = $task->{'tasPk'};
    my $Tfarr = $taskt->{'firstarrival'};
    my @pilots;
    my $ref;
    my $sth;

    # Get all pilots and process each of them 
    # pity it can't be done as a single update ...
    $dbh->do('set @x=0;');
    $sth = $dbh->prepare("select \@x:=\@x+1 as Place, tarPk, traPk, tarDistance, tarSS, tarES, tarPenalty, tarResultType, tarLeadingCoeff, tarGoal, tarLastAltitude from tblTaskResult where tasPk=$tasPk and tarResultType <> 'abs' order by case when (tarES=0 or tarES is null) then 99999999 else tarES end, tarDistance desc");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        my %taskres;

        %taskres = ();
        $taskres{'tarPk'} = $ref->{'tarPk'};
        $taskres{'traPk'} = $ref->{'traPk'};
        $taskres{'penalty'} = $ref->{'tarPenalty'};
        $taskres{'distance'} = $ref->{'tarDistance'};
        $taskres{'stopalt'} = $ref->{'tarLastAltitude'};
        # set pilot to min distance if they're below that ..
        # print "sstopped=", $task->{'sstopped'}, " stopalt=", $taskres{'stopalt'}, " glidebonus=", $formula->{'glidebonus'}, "\n";
        if ($task->{'sstopped'} > 0 && $taskres{'stopalt'} > 0 && $formula->{'glidebonus'} > 0)
        {
            print "Stopped height bonus: ", $formula->{'glidebonus'} * $taskres{'stopalt'}, "\n";
            if ($taskres{'stopalt'} > $task->{'goalalt'})
            {
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
        $taskres{'coeff'} = $ref->{'tarLeadingCoeff'};
        # FIX: adjust against fastest ..
        if ((($ref->{'tarES'} - $ref->{'tarSS'}) < 1) and ($ref->{'tarSS'} > 0))
        {
            # Fix - busted if no one is in goal?
            if ($taskt->{'goal'} > 0)
            {
                # adjust for late starters
                print "No goal, adjust pilot coeff from: ", $ref->{'tarLeadingCoeff'};
                $taskres{'coeff'} = $ref->{'tarLeadingCoeff'} - ($task->{'sfinish'} - $taskt->{'lastarrival'}) * ($task->{'endssdistance'} - $ref->{'tarDistance'}) / 1800 / $task->{'ssdistance'} ;
            
                print " to: ", $taskres{'coeff'}, "\n";
                # adjust mincoeff?
                if ($taskres{'coeff'} < $task->{'mincoeff'})
                {
                    $task->{'mincoeff'} = $taskres{'coeff'};
                }
            }
        }
    
        # KMBonus markers
        # @todo adjust against fastest?
        $taskres{'kmmarker'} = [];
        my $kt = $taskres{'kmmarker'};
        my $sub = $dbh->prepare("select * from tblTrackMarker where traPk=" . $taskres{'traPk'} . " order by tmDistance");
        $sub->execute();
        my $sref;
        while ($sref = $sub->fetchrow_hashref())
        {
            push @$kt, $sref->{'tmTime'};
        }

        push @pilots, \%taskres;
    }

    return \@pilots;
}

#    POINTS ALLOCATION
#    Points Allocation:
#    x=Ngoal/Nfly
#    distweight =  1-0.8*x^0.5
#
#    A.distance   = 1000 * DayQuality * distweight
#    A.speed       = 1000 * DayQuality * (1-distweight) * 5.6/8
#    A.start          = 1000 * DayQuality * (1-distweight) * 1.4/8
#    A.position    = 1000 * DayQuality * (1-distweight) * 1/8
#
#
# Pilot Distance Score:
# half of the available distance points is assigned linearly with the 
# distance flown; the other half is assigned considering the relative 
# difficulty of each km flown.
# DistancePoints = 
#   Available DistancePoints *(PilotDistance/(2*MaxDistance) + KmDiff)
#
# To calculate KmDiff first calculate range used for the moving average 
# Range = round(Dmax/(Nfly-Ngoal))          Range>=3
# second make an array with a column with 100 meters, another column 
# with number of pilots landed in that 100 m, a third column with the 
# difficulty i.e. the number of pilots landed in that 100m plus  Range  km.
# The Relative Difficulty of each 100 is: Difficulty/(2*sum(Difficulty))
# Score% is the sum of the Linear difficulty plus the Rel.Difficulty 
# of all the previous 100 
# Of course all the pilots with less than Dmin will score  Dmin.
#
# Pilot speed score:
# P.speed = 1-((PilotTime-Tmin)/radq(Tmin))^(2/3)
#
# Pilot departure score:
# x = Tdelay / Tnom
# if x>1/3 departure points =0
#  else
#  P.start = SpeedPoints/6*(1-6.312*X+10.932*X^2-2.990*X^3)
#
#  Pilot arrival score
#  X= 1-(PilotPos-1)/(Ngoal)
#  Pposition = 0.2+0.037*X+0.13*X^2+0.633*X^3
#
# Should be separate one of these for each type/version combo?
#
sub points_allocation
{
    my ($self, $dbh, $task, $taskt, $formula) = @_;
    my @pilots;

    # Find fastest pilot into goal and calculate leading coefficients
    # for each track .. (GAP2002 only?)

    my $tasPk = $task->{'tasPk'};
    my $quality = $taskt->{'quality'};
    my $Ngoal = $taskt->{'goal'};
    my $Tmin = $taskt->{'fastest'};
    my $Tfarr = $taskt->{'firstarrival'};
    # print Dumper($taskt);


    my $sorted_pilots = $self->ordered_results($dbh, $task, $taskt, $formula);

    # Get basic GAP allocation values
    my ($Adistance, $Aspeed, $Astart, $Aarrival) = $self->points_weight($task, $taskt, $formula);

    # Score each pilot now 
    for my $pil ( @$sorted_pilots )
    {
        my $tarPk = $pil->{'tarPk'};
        my $penalty = $pil->{'penalty'};

        # Pilot distance score 
        # FIX: should round $pil->distance properly?
        # my $pilrdist = round($pil->{'distance'}/100.0) * 100;

        my $Pdist = $self->pilot_distance($formula, $task, $taskt, $pil, $Adistance);

        # Pilot speed score
        my $Pspeed = $self->pilot_speed($formula, $task, $taskt, $pil, $Aspeed);

        # Pilot departure/leading points
        my $Pdepart = $self->pilot_departure_leadout($formula, $task, $taskt, $pil, $Astart, $Aspeed);

        # Pilot arrival score
        my $Parrival = $self->pilot_arrival($formula, $task, $taskt, $pil, $Aarrival);

        # Penalty for not making goal ..
        if ($pil->{'goal'} == 0)
        {
            $Pspeed = $Pspeed - $Pspeed * $formula->{'sspenalty'};
            $Parrival = $Parrival - $Parrival * $formula->{'sspenalty'}; 
        }

        # Sanity
        if (($pil->{'result'} eq 'dnf') or ($pil->{'result'} eq 'abs'))
        {
            $Pdist = 0;
            $Pspeed = 0;
            $Parrival = 0;
            $Pdepart = 0;
        }

        # Penalties
        # $penalty = $self->pilot_penalty($formula, $task, $taskt, $pil, $Astart, $Aspeed);

        # Total score
        my $Pscore = $Pdist + $Pspeed + $Parrival + $Pdepart - $penalty;

        # Store back into tblTaskResult ...
        if (defined($tarPk))
        {
            print "update $tarPk: d:$Pdist, s:$Pspeed, p: $penalty, a:$Parrival, g:$Pdepart\n";
            my $sth = $dbh->prepare("update tblTaskResult set
                tarDistanceScore=$Pdist, tarSpeedScore=$Pspeed, 
                tarArrival=$Parrival, tarDeparture=$Pdepart, tarScore=$Pscore
                where tarPk=$tarPk");
            $sth->execute();
        }
    }
}

1;

