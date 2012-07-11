#!/usr/bin/perl -I/home/geoff/bin


#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2007
#

package Nzl;

require Gap;
@ISA = ( "Gap" );

require DBD::mysql;

use POSIX qw(ceil floor);
use Math::Trig;
use Data::Dumper;
use TrackLib qw(:all);

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
    my $goal;
    my %taskt;
    my $tasPk;
    my ($minarr, $fastest, $firstdep, $mincoeff);
    my $mindist;
    my $topnine;

    $mindist = 0;
    $tasPk = $task->{'tasPk'};
    $sth = $dbh->prepare("select F.* from tblTask T, tblCompetition C, tblFormula F where T.tasPk=$tasPk and C.comPk=T.comPk and F.forPk=C.forPk");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref()) 
    {
        # convert to metres ...
        $mindist = $ref->{'forMinDistance'} * 1000;
    }

    # FIX: failsafe for now?
    if ($mindist == 0)
    {
        print "WARNING: mindist was 0, using 5000m instead\n";
        $mindist = 5000;
    }

    $sth = $dbh->prepare("select count(tarPk) as TotalPilots, sum(if(tarDistance < $mindist, $mindist, tarDistance)) as TotalDistance, sum((tarDistance > 0) or (tarResultType='lo')) as TotalLaunched FROM tblTaskResult where tasPk=$tasPk and tarResultType <> 'abs'");

    $sth->execute();
    $ref = $sth->fetchrow_hashref();
    $totdist = $ref->{'TotalDistance'};
    $launched = $ref->{'TotalLaunched'};
    $pilots = $ref->{'TotalPilots'};

    # pilots in goal?
    $sth = $dbh->prepare("select count(tarPk) as GoalPilots from tblTaskResult where tasPk=$tasPk and tarGoal > 0");
    $sth->execute();
    $goal = 0;
    if ($ref = $sth->fetchrow_hashref())
    {
        $goal = $ref->{'GoalPilots'};
    }

    # fastest?
    $sth = $dbh->prepare("select min(tarES-tarSS) as MinTime, min(tarES) as MinArr from tblTaskResult where tasPk=$tasPk and tarES > 0");
    $sth->execute();
    $minarr = 0;
    if ($ref = $sth->fetchrow_hashref())
    {
        $fastest = $ref->{'MinTime'};
        $minarr = $ref->{'MinArr'};
    }
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

    $maxdist = 0;
    $mindept = 0;
    $sth = $dbh->prepare("select max(tarDistance) as MaxDist from tblTaskResult where tasPk=$tasPk");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref())
    {
        $maxdist = 0 + $ref->{'MaxDist'};
    }

    $sth = $dbh->prepare("select min(tarSS) as MinDept from tblTaskResult where tasPk=$tasPk and tarSS > 0 and tarGoal > 0");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref())
    {
        $mindept = $ref->{'MinDept'};
    }

    # Get the top 90% dist ...
    $topnine = 0;
    $dbh->do('set @x=0;');
    $sth = $dbh->prepare("select \@x:=\@x+1 as Place, tarDistance from tblTaskResult where tasPk=$tasPk and (tarResultType='lo' or tarResultType='goal') order by tarDistance desc");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        if ($ref->{'Place'} <= $self->round($launched * 0.90))
        {
            $topnine = $topnine + $ref->{'tarDistance'};
        }
    }
    print "distance=$totdist 90%dist=$topnine\n";

    # task quality 
    $taskt{'pilots'} = $pilots;
    $taskt{'maxdist'} = $maxdist;
    $taskt{'distance'} = $totdist;
    #$taskt{'taskdist'} = $taskdist;
    $taskt{'launched'} = $launched;
    #$taskt{'quality'} = $quality;
    $taskt{'goal'} = $goal;
    $taskt{'fastest'} = $fastest;
    $taskt{'firstdepart'} = $mindept;
    $taskt{'firstarrival'} = $minarr;
    $taskt{'mincoeff'} = $mincoeff;
    $taskt{'topninety'} = $topnine;

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

    $launch = $taskt->{'launched'}/($taskt->{'pilots'} * 0.9);
    #$launch  = 0.028*$x + 2.917*$x*$x - 1.944*$x*$x*$x;
    print "launch quality=$launch\n";
    if ($launch > 1) 
    {
        $launch = 1;
    }
    if ($launch < 0) 
    {
        $launch = 0;
    }

    $distance = $taskt->{'topninety'} / $self->round($taskt->{'launched'} * 0.9) 
            / ($formula->{'nomdist'} / 1000) / 1000;
    #print "top90=", $taskt->{'topninety'}, " launched=", $self->round($taskt->{'launched'} * 0.9), " nomdist=", $formula->{'nomdist'} / 1000;
    print "distance quality=$distance\n";
    if ($distance > 1.2) 
    {
        $distance = 1.2;
    }
    if ($distance < 0) 
    {
        $distance = 0;
    }
            
    if ($taskt->{'fastest'} > 0)
    {
        $tmin = $taskt->{'fastest'};
        $time = $tmin / ($formula->{'nomtime'});
    }
    else
    {
        $time = 1;
    }

    print "time quality=$time\n";
    if ($time > 1.2) 
    {
        $time = 1.2;
    }
    if ($time < 0.1) 
    {
        $time = 0.1;
    }

    return ($distance,$time,$launch);
}


sub points_weight
{
    my ($self, $task, $taskt, $formula) = @_;
    my $Fversion;
    my $quality;
    my $distweight;
    my $Adistance;
    my $Aspeed;
    my $Astart;
    my $Aarrival;
    my $x;


    $quality = $taskt->{'quality'};
    $Fversion = $formula->{'version'};

    # Way simple for NZ (no departure / leadout or arrival)
    #print "distweight=$distweight($Ngoal/$Nfly)\n";
    $x = $taskt->{'goal'} / $taskt->{'launched'};
    $distweight = 1-0.6*sqrt($x);

    $Adistance = 1000 * $quality * $distweight;
    $Aspeed = 1000 * $quality * (1-$distweight);
    $Astart = 0;
    $Aarrival = 0;
    
    print "points_weight: ($Fversion) Adist=$Adistance, Aspeed=$Aspeed, Astart=$Astart, Aarrival=$Aarrival\n";

    return ($Adistance, $Aspeed, $Astart, $Aarrival);

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
    my $tasPk;
    my $quality;
    my ($Ngoal,$Nfly);
    my ($Tnom, $Tmin);
    my $Tmindist;
    my $Tfarr;
    my $Dmax;
    my $Fclass;
    my $Fversion;
    my $Cmin;

    my $x;
    my $distweight;

    my $Adistance;
    my $Aspeed;
    my $Astart;
    my $Arival;

    my $difdist;

    my @pilots;
    my $kmdiff = [];

    # Find fastest pilot into goal and calculate leading coefficients
    # for each track .. (GAP2002 only?)

    $tasPk = $task->{'tasPk'};
    $quality = $taskt->{'quality'};
    $Ngoal = $taskt->{'goal'};
    $Nfly = $taskt->{'launched'};
    $Tmin = $taskt->{'fastest'};
    $Tfarr = $taskt->{'firstarrival'};
    $Cmin = $taskt->{'mincoeff'};

    $Tnom = $formula->{'nomtime'};
    $Tmindist = $formula->{'mindist'};
    $Dmax = $taskt->{'maxdist'} / 1000.0;
    $Fclass = $formula->{'class'};
    $Fversion = $formula->{'version'};

    print "Tnom=$Tnom Tmindist=$Tmindist Dmax=$Dmax Flcass=$Fclass Fversion=$Fversion Nfly=$Nfly\n";

    if ($Dmax == 0)
    {
        return;
    }

    # Some GAP basics
    ($Adistance, $Aspeed, $Astart, $Aarrival) = $self->points_weight($task, $taskt, $formula);

    # KM difficulty
    for my $it ( 0 .. floor($taskt->{'maxdist'} / 100.0) )
    {
        $kmdiff->[$it] = 0;
    }

    $sth = $dbh->prepare("select truncate(tarDistance/100,0) as Distance, count(truncate(tarDistance/100,0)) as Difficulty from tblTaskResult where tasPk=$tasPk and tarResultType not in ('abs','dnf') group by truncate(tarDistance/100,0)");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        # populate kmdiff - set back 1km to stop dangerous overflying
        $difdist = 0 + $ref->{'Distance'} - 10;
        if ($difdist < 0) 
        {
            $difdist = 0;
        }

        $kmdiff->[$difdist] = 0+$ref->{'Difficulty'};
    }
    # Smooth it out 
    for my $it ( 0 .. 4 )
    {
        $kmdiff = $self->spread($kmdiff);
    }

    $x = 0;
    for my $dif (0 .. scalar @$kmdiff-1)
    {
        my $sdif;
        my $landed;
        my $rdif;
        my $range;
        my $ddif;

        # FIX: currently assuming a range of 1km
        # not using this
        # $range = round($Dmax/($Nfly-$Ngoal));

        $landed = $kmdiff->[$dif];
        #print "landed $dif=$landed\n";
        $x = $x + $landed;
        $ddif = $dif;
        if ($ddif < $Tmindist)
        {
            $ddif = $Tmindist;
        }
        $sdif = $ddif/$Dmax * 0.5;
        $rdif = 0;
        if ($x > 0)
        {
            $rdif = $x/(2*$Nfly);
        }
        # CHECK: distance component handled below?
        #   just need relative difficulty and not distance diff?
        #$kmdiff[$dif] = ($sdif + $rdif) / 2;
        $kmdiff->[$dif] = ($rdif);
        #print "$dif - sdif=$sdif rdif=$rdif kmdif = ", $kmdiff[$dif], "\n";
    }

    # Get all pilots and process each of them 
    # pity it can't be done as a single update ...
    $dbh->do('set @x=0;');
    $sth = $dbh->prepare("select \@x:=\@x+1 as Place, tarPk, tarDistance, tarSS, tarES, tarPenalty, tarResultType, tarLeadingCoeff from tblTaskResult where tasPk=$tasPk and tarResultType <> 'abs' order by tarDistance desc, tarES");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        my %taskres;

        %taskres = ();
        $taskres{'tarPk'} = $ref->{'tarPk'};
        $taskres{'penalty'} = $ref->{'tarPenalty'};
        $taskres{'distance'} = $ref->{'tarDistance'};
        # set pilot to min distance if they're below that ..
        if ($taskres{'distance'} < $Tmindist)
        {
            $taskres{'distance'} = $Tmindist;
        }
        $taskres{'result'} = $ref->{'tarResultType'};
        $taskres{'startSS'} = $ref->{'tarSS'};
        $taskres{'endSS'} = $ref->{'tarES'};
        # OZGAP2005 
        $taskres{'timeafter'} = $ref->{'tarES'} - $Tfarr;
        $taskres{'place'} = $ref->{'Place'};
        $taskres{'time'} = $taskres{'endSS'} - $taskres{'startSS'};
        if ($taskres{'time'} < 0)
        {
            $taskres{'time'} = 0;
        }
        # Leadout Points
        $taskres{'coeff'} = $ref->{'tarLeadingCoeff'};
        # FIX: adjust against fastest ..

        push @pilots, \%taskres;
    }

    # Score each pilot now 
    for my $pil ( @pilots )
    {
        my $Pdist;
        my $Pspeed;
        my $Parrival;
        my $Pdepart;
        my $Pscore;
        my $tarPk;
        my $penalty;

        $tarPk = $pil->{'tarPk'};
        $penalty = $pil->{'penalty'};

        # Pilot distance score 
        #print "task->maxdist=", $taskt->{'maxdist'}, "\n";
        #print "pil->distance/(2*maxdist)=", $pil->{'distance'}/(2*$taskt->{'maxdist'}), "\n";
        #print "kmdiff=", $kmdiff[floor($pil->{'distance'}/1000.0)], "\n";
        $Pdist = $Adistance * sqrt($pil->{'distance'}/$taskt->{'maxdist'});
                    # $kmdiff->[floor($pil->{'distance'}/100.0)]);

        # Pilot speed score
        print "$tarPk speed: ", $pil->{'time'}, ", $Tmin\n";
        if ($pil->{'time'} > 0)
        {
            $Pspeed = $Aspeed * ($Tmin/$pil->{'time'}) * ($Tmin/$pil->{'time'}) * ($Tmin/$pil->{'time'});
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
            print "Pdepart is nan for $tarPk, pil->{'time'}=", $pil->{'time'}, "\n";
            $Pspeed = 0;
        }

        # Pilot departure score
        print "$tarPk pil->startSS=", $pil->{'startSS'}, "\n";
        print "$tarPk pil->endSS=", $pil->{'endSS'}, "\n";
        print "$tarPk tast->first=", $taskt->{'firstdepart'}, "\n";

        $Pdepart = 0;
        $Parrival = 0;

        if (($pil->{'result'} eq 'dnf') or ($pil->{'result'} eq 'abs'))
        {
            $Pdist = 0;
            $Pspeed = 0;
            $Parrival = 0;
            $Pdepart = 0;
        }

        if (0+$Pdepart != $Pdepart)
        {
            print "Pdepart is nan for $tarPk\n";
            $Pdepart = 0;
        }

        $Pscore = $Pdist + $Pspeed + $Parrival + $Pdepart - $penalty;

        # Store back into tblTaskResult ...
        if (defined($tarPk))
        {
            print "update $tarPk: d:$Pdist, s:$Pspeed, a:$Parrival, g:$Pdepart\n";
            $sth = $dbh->prepare("update tblTaskResult set
                tarDistanceScore=$Pdist, tarSpeedScore=$Pspeed,
                tarArrival=$Parrival, tarDeparture=$Pdepart, tarScore=$Pscore
                where tarPk=$tarPk");
            $sth->execute();
        }
    }
}


1;

