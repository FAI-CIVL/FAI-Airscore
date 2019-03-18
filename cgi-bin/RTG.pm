#!/usr/bin/perl -w
#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# for race to goal 2018 scoring. 
#pwc with no leadpoints.
#points = number of pilots behind you + 1 + 5/3/1 bonus for 1st/2nd/3rd









package RTG;

require Exporter;
our @ISA = qw(Exporter);
#our @EXPORT = qw(:all);

require DBD::mysql;
use POSIX qw(ceil floor);
use Math::Trig;
use Data::Dumper;
use strict;

# Add currect bin directory to @INC
use File::Basename;
use lib '/home/untps52y/perl5/lib/perl5';
use lib dirname (__FILE__) . '/';
use TrackLib qw(:all);
# require Scoring;

sub new
{
    my $class = shift;
    my $self = {};
    # set any defaults here ...
    bless ($self, $class);
    return $self;
}

###########################################################
# This part would be nice to be put in an external file, did not find how yet
###########################################################
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

sub max
{
    my ($self, $list) = @_;
    my $x = 0;

    foreach my $y (@$list)
    {
        $x = $y if $y > $x;
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
    $nbuc->[1] = 0.0 + $buc->[1];
    for my $j ( 1 .. $sz )
    {
        $nbuc->[$j] //= 0;
        $nbuc->[$j-1] = $nbuc->[$j-1] + $buc->[$j] / 3;
        $nbuc->[$j] = $nbuc->[$j] + $buc->[$j] * 2 / 3;
        #$nbuc->[$j+1] = $buc->[$j] / 3;
    }

    return $nbuc;
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

    return $penalty;
}

#####################################################

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
    $sth = $dbh->prepare("	SELECT 
								COUNT(tarPk) as TotalPilots, 
								SUM(
									IF(
										tarDistance < $mindist, $mindist, tarDistance
									)
								) AS TotalDistance, 
								SUM(
									IF(
										tarDistance < $mindist, 
										0, 
										(tarDistance - $mindist)
									)
								) AS TotDistOverMin, 
								SUM(
									(tarDistance > 0) 
									OR (tarResultType = 'lo')
								) AS TotalLaunched, 
								STD(
									IF(
										tarDistance < $mindist, $mindist, tarDistance
									)
								) AS Deviation, 
								SUM(
									IF(
										(
											tarLastAltitude = 0 
											AND (
												tarDistance > 0 
												OR tarResultType = 'lo'
											) 
											OR tarGoal > 0
										), 
										1, 
										0
									)
								) AS Landed 
							FROM 
								tblTaskResult 
							WHERE 
								tasPk = $tasPk 
								AND tarResultType <> 'abs'");

    $sth->execute();
    $ref = $sth->fetchrow_hashref();
    $totdist = 0.0 + $ref->{'TotalDistance'};
    $launched = 0 + $ref->{'TotalLaunched'};
    $pilots = 0 + $ref->{'TotalPilots'};
    $stddev = 0 + $ref->{'Deviation'};
    my $totdistovermin = 0 + $ref->{'TotDistOverMin'};
    $task->{'sstopped'} //= 0;
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
    $taskt{'distovermin'} = $totdistovermin;
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
    # Seems like PWC formula in the rules is wrong. We will use FAI Gap one instead.
    # LVR = min (1, num pilots launched / ( total pilots * nominal Launch ) )
    # Launch Validity = 0.027*LRV + 2.917*LVR^2 - 1.944*LVR^3
    # Setting Nominal Launch = 96% (max number of DNF that still permit full validity)
    
    my $nomlau = 0.96;
    $x = $taskt->{'launched'} / ( $taskt->{'pilots'} * $nomlau );
    $x = $self->min([1, $x]);
    $launch  = 0.027*$x + 2.917*$x*$x - 1.944*$x*$x*$x;
    if ($taskt->{'launchvalid'} == 0 or $launch < 0)
    {
        print "Launch invalid - dist quality set to 0\n";
        $launch = 0;
    }
    print "PWC launch validity = $launch\n";

    # C.4.2 Distance Validity
    # DVR = (Total flown Distance over MinDist) / [ (PilotsFlying / 2) * (NomGoal +1) * (NomDist - MinDist) * NomGoal * (BestDist - NomDist) ]
    # DistVal = min (1, DVR)
    
    # my $nomgoal = $formula->{'nomgoal'}/100; # nom goal percentage
    my $nomgoal = $formula->{'nomgoal'}; # nom goal percentage
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
    
    my $tmin;
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
    my $stopv;
    if ( defined($taskt->{'fastest'} ) and $taskt->{'fastest'} > 0 )
    {
		$stopv = 1;
    }
	else
	{	
		$x = ($taskt->{'landed'} / $taskt->{'launched'});
    	print "sqrt( ($taskt->{'maxdist'} - $avgdist) / ($distlaunchtoess - $taskt->{'maxdist'}+1) * sqrt($taskt->{'stddev'} / 5)) + $x*$x*$x \n";
    	$stopv = sqrt( ($taskt->{'maxdist'} - $avgdist) / ($maxSSdist+1) * sqrt($taskt->{'stddev'} / 5) ) + $x**3 ;
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
    #if ($formula->{'weightdist'} eq 'post2014')
    #{
        $distweight = 0.9 - 1.665 * $x + 1.713 * $x * $x - 0.587 * $x*$x*$x;
        print "PWC 2016 Points Allocatiom distWeight = $distweight \n";
    #}
    #else
    #{
    #    $distweight = 1 - 0.8 * sqrt($x);
    #    print "NOT Using 2016 Points Allocatiom distWeight = $distweight \n";
    #}

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
    $LCp //= 0;
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

# Calculate pilot arrival score
# I think they are not used in PWC Formula, we could remove sub and calculation in point_allocation
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

    return $Pspeed;
}


sub ordered_results
{
    my ($self, $dbh, $task, $taskt, $formula) = @_;
    my @pilots;
    my $Tfarr = $taskt->{'firstarrival'};

    # Get all pilots and process each of them
    # pity it can't be done as a single update ...
    $dbh->do('set @x=0;');
    my $sth = $dbh->prepare("	SELECT 
								\@x := \@x + 1 AS Place, 
								tarPk, 
								traPk, 
								tarDistance, 
								tarSS, 
								tarES, 
								tarPenalty, 
								tarResultType, 
								tarLeadingCoeff2, 
								tarGoal, 
								tarLastAltitude, 
								tarLastTime 
							FROM 
								tblTaskResult 
							WHERE 
								tasPk = ? 
								AND tarResultType <> 'abs' 
							ORDER BY 
								CASE WHEN (
									tarGoal = 0 
									OR tarES IS null
								) THEN -999999 ELSE tarLastAltitude END, 
								tarDistance DESC");
    $sth->execute($task->{'tasPk'});
    while (my $ref = $sth->fetchrow_hashref())
    {
        my %taskres;

        %taskres = ();
        $taskres{'tarPk'} = $ref->{'tarPk'};
        $taskres{'traPk'} = $ref->{'traPk'};
        $taskres{'penalty'} = $ref->{'tarPenalty'};
        $taskres{'distance'} = $ref->{'tarDistance'};
        $taskres{'stopalt'} = $ref->{'tarLastAltitude'};
        $task->{'sstopped'} //= 0;
        $taskres{'stopalt'} //= 0;
        $formula->{'glidebonus'} //= 0;
        $ref->{'tarES'} //= 0;
        $ref->{'tarSS'} //= 0;
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
                $task->{'mincoeff2'} //= 0;
                if ($taskres{'coeff'} < $taskt->{'mincoeff2'})
                {
                    $taskt->{'mincoeff2'} = $taskres{'coeff'};
                }
            }
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

	# Update point weights in tblTask
	my $sth = $dbh->prepare("UPDATE tblTask SET 
		tasAvailDistPoints=$Adistance, tasAvailLeadPoints=$Astart, 
		tasAvailTimePoints=$Aspeed 
		WHERE tasPk=$tasPk");
	$sth->execute();	

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
        my $Pdepart = 0;

        # Pilot arrival score
        my $Parrival = 0;

        # Penalty for not making goal ..
        $pil->{'goal'} //= 0;
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
        $penalty //= 0;
        # Total score
        my $Pscore = $Pdist + $Pspeed + $Parrival + $Pdepart - $penalty;

        # Store back into tblTaskResult ...
        if (defined($tarPk))
        {
            print "update $tarPk: dP:$Pdist, sP:$Pspeed, LeadP:$Pdepart - score $Pscore\n";
            $sth = $dbh->prepare("update tblTaskResult set
                tarDistanceScore=$Pdist, tarSpeedScore=$Pspeed, 
                tarArrival=$Parrival, tarDeparture=$Pdepart, tarScore=$Pscore
                where tarPk=$tarPk");
            $sth->execute();
        }
    }

    #replace total scores with RTG place scores
    $sth = $dbh->prepare("UPDATE  tblTaskResult as t1
 
    inner join
    (select (select COUNT(*) FROM tblTaskResult where tarResultType <> 'dnf' and tasPk = $tasPk and tarScore is not null ) -
    (select COUNT(*) FROM tblTaskResult where tarScore > a.tarScore and tasPk = $tasPk and tarScore is not null ) +
    (case (select COUNT(*) FROM tblTaskResult where tarScore > a.tarScore and tasPk = $tasPk and tarScore is not null)
    when 0 then 5 
    when 1 then 3 
    when 2 then 1
    else 0 end ) as tarscore2,
    traPk from tblTaskResult as a
    where tarScore is not null and tasPk = $tasPk) as t2
    on t1.traPk = t2.traPk
    SET t1.tarScore = t2.tarScore2
    where t1.tasPk = $tasPk
    and t1.tarScore is not null;");
    $sth->execute();
}

1;