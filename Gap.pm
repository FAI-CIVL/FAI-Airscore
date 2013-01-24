#!/usr/bin/perl 


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
    my %taskt;
    my $tasPk;
    my ($minarr, $fastest, $firstdep, $mincoeff, $tqtime);
    my $launchvalid;

    $tasPk = $task->{'tasPk'};
    $launchvalid = $task->{'launchvalid'};
    $mindist = $formula->{'mindist'};

    $sth = $dbh->prepare("select count(tarPk) as TotalPilots, sum(if(tarDistance < $mindist, $mindist, tarDistance)) as TotalDistance, sum((tarDistance > 0) or (tarResultType='lo')) as TotalLaunched FROM tblTaskResult where tasPk=$tasPk and tarResultType <> 'abs'");

    $sth->execute();
    $ref = $sth->fetchrow_hashref();
    $totdist = 0.0 + $ref->{'TotalDistance'};
    $launched = 0 + $ref->{'TotalLaunched'};
    $pilots = 0 + $ref->{'TotalPilots'};

    # pilots in goal?
    $sth = $dbh->prepare("select count(tarPk) as GoalPilots from tblTaskResult where tasPk=$tasPk and tarGoal > 0");
    $sth->execute();
    $goal = 0;
    if ($ref = $sth->fetchrow_hashref())
    {
        $goal = $ref->{'GoalPilots'};
    }

    $sth = $dbh->prepare("select min(tarES) as MinArr from tblTaskResult where tasPk=$tasPk and (tarES-tarSS) > 0");
    $sth->execute();
    $minarr = 0;
    if ($ref = $sth->fetchrow_hashref())
    {
        $minarr = $ref->{'MinArr'};
    }

    $sth = $dbh->prepare("select (tarES-tarSS) as MinTime from tblTaskResult where tasPk=$tasPk and (tarES-tarSS) > 0 order by (tarES-tarSS) asc limit 2");
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

    $maxdist = 0;
    $mindept = 0;
    $sth = $dbh->prepare("select max(tarDistance) as MaxDist from tblTaskResult where tasPk=$tasPk");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref())
    {
        $maxdist = 0 + $ref->{'MaxDist'};
    }
    if ($maxdist < 0.1)
    {
        $maxdist = 0.1;
    }

    $sth = $dbh->prepare("select min(tarSS) as MinDept from tblTaskResult where tasPk=$tasPk and tarSS > 0 and tarGoal > 0");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref())
    {
        $mindept = $ref->{'MinDept'};
    }

    # task quality 
    $taskt{'pilots'} = $pilots;
    $taskt{'maxdist'} = $maxdist;
    $taskt{'distance'} = $totdist;
    #$taskt{'taskdist'} = $taskdist;
    $taskt{'launched'} = $launched;
    $taskt{'launchvalid'} = $launchvalid;
    #$taskt{'quality'} = $quality;
    $taskt{'goal'} = $goal;
    $taskt{'fastest'} = $fastest;
    $taskt{'tqtime'} = $tqtime;
    $taskt{'firstdepart'} = $mindept;
    $taskt{'firstarrival'} = $minarr;
    $taskt{'mincoeff'} = $mincoeff;

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

    if ($x < 1)
    {
        $time = -0.271 + 2.912*$x - 2.098*$x*$x + 0.457*$x*$x*$x;
    }
    else
    {
        $time = 1;
    }
    print "time quality=$time\n";
    if ($time > 1) 
    {
        $time = 1;
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
    my $quality;
    my $distweight;
    my $Adistance;
    my $Aspeed;
    my $Astart;
    my $Aarrival;
    my $x;
    my $dem;


    $quality = $taskt->{'quality'};

    #print "distweight=$distweight($Ngoal/$Nfly)\n";
    $x = $taskt->{'goal'} / $taskt->{'launched'};
    $distweight = 1-0.8*sqrt($x);
    $Adistance = 1000 * $quality * $distweight;

    if ($formula->{'version'} eq '1998')
    {
        $Aspeed = 1000 * $quality * (1-$distweight) * 6/8;
        $Astart = 1000 * $quality * (1-$distweight) * 1/8;
        $Aarrival = 1000 * $quality * (1-$distweight) * 1/8;
    }
    else
    {
        # 2000, 2002, 2007
        $Aspeed = 1000 * $quality * (1-$distweight) * 5.6/8;
        $Astart = 1000 * $quality * (1-$distweight) * 1.4/8;
        $Aarrival = 1000 * $quality * (1-$distweight) * 1/8;
    }

    # need to rescale if depart / arrival are "off"
    if (($task->{'arrival'} eq 'off') and ($task->{'departure'} eq 'off'))
    {
        $dem = $Adistance + $Aspeed;
        $Adistance = 1000 * $quality * ($Adistance / $dem);
        $Aspeed = 1000 * $quality * ($Aspeed / $dem);
        $Astart = 0;
        $Aarrival = 0; 
    }
    elsif ($task->{'arrival'} eq 'off')
    {
        $dem = $Adistance + $Aspeed + $Astart;
        $Adistance = 1000 * $quality *($Adistance / $dem);
        $Aspeed = 1000 * $quality * ($Aspeed / $dem);
        $Astart =  1000 * $quality * ($Astart / $dem);
        $Aarrival = 0; 
    }
    elsif ($task->{'departure'} eq 'off')
    {
        $dem = $Adistance + $Aspeed + $Aarrival;
        $Adistance = 1000 * $quality * ($Adistance / $dem);
        $Aspeed = 1000 * $quality * ($Aspeed / $dem);
        $Aarrival = 1000 * $quality * ($Aarrival / $dem);
        $Astart = 0;
    }


    print "points_weight: (", $formula->{'version'}, ") Adist=$Adistance, Aspeed=$Aspeed, Astart=$Astart, Aarrival=$Aarrival\n";

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
    my ($Ngoal,$Nfly,$Nlo);
    my ($Tmin);
    my $Tfarr;
    my $Cmin;

    my $x;
    my $distweight;

    my $Adistance;
    my $Aspeed;
    my $Astart;
    my $Arival;

    my $penspeed;
    my $pendist;
    my $difdist;

    my $debc;

    my @pilots;
    my $kmdiff = [];

    # Find fastest pilot into goal and calculate leading coefficients
    # for each track .. (GAP2002 only?)

    $tasPk = $task->{'tasPk'};
    $quality = $taskt->{'quality'};
    $Ngoal = $taskt->{'goal'};
    $Nfly = $taskt->{'launched'};
    $Nlo = $Nfly - $Ngoal;
    $Tmin = $taskt->{'fastest'};
    $Tfarr = $taskt->{'firstarrival'};
    $Cmin = $taskt->{'mincoeff'};
    print Dumper($taskt);

    print "Nfly=$Nfly Nlo=$Nlo\n";

    # Some GAP basics
    ($Adistance, $Aspeed, $Astart, $Aarrival) = $self->points_weight($task, $taskt, $formula);

    # KM difficulty
    for my $it ( 0 .. floor($taskt->{'maxdist'} / 100.0) )
    {
        $kmdiff->[$it] = 0;
    }

    if ($formula->{'diffcalc'} eq 'lo')
    {
        $sth = $dbh->prepare("select truncate(tarDistance/100,0) as Distance, count(truncate(tarDistance/100,0)) as Difficulty from tblTaskResult where tasPk=$tasPk and tarResultType not in ('abs','dnf') and (tarGoal=0 or tarGoal is null) group by truncate(tarDistance/100,0)");
    }
    else
    {
        $sth = $dbh->prepare("select truncate(tarDistance/100,0) as Distance, count(truncate(tarDistance/100,0)) as Difficulty from tblTaskResult where tasPk=$tasPk and tarResultType not in ('abs','dnf') group by truncate(tarDistance/100,0)");
    }
    $sth->execute();
    $debc = 0;
    while ($ref = $sth->fetchrow_hashref()) 
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
    $x = 0.0;
    for my $dif (0 .. scalar @$kmdiff-1)
    {
        my $rdif;

        $rdif = 0.0;

        $x = $x + $kmdiff->[$dif];
        # Use only landed-out pilots or all pilots for difficulty?
        if ($formula->{'diffcalc'} eq 'lo')
        {
            $rdif = $x/$Nlo;
        }
        else
        {
            $rdif = $x/$Nfly;
        }
        $kmdiff->[$dif] = ($rdif);
    }
    print "debc=$debc x=$x (vs $Nlo)\n";

    # Get all pilots and process each of them 
    # pity it can't be done as a single update ...
    $dbh->do('set @x=0;');
    $sth = $dbh->prepare("select \@x:=\@x+1 as Place, tarPk, tarDistance, tarSS, tarES, tarPenalty, tarResultType, tarLeadingCoeff, tarGoal from tblTaskResult where tasPk=$tasPk and tarResultType <> 'abs' order by tarDistance desc, tarES");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        my %taskres;

        %taskres = ();
        $taskres{'tarPk'} = $ref->{'tarPk'};
        $taskres{'penalty'} = $ref->{'tarPenalty'};
        $taskres{'distance'} = $ref->{'tarDistance'};
        # set pilot to min distance if they're below that ..
        if ($taskres{'distance'} < $formula->{'mindist'})
        {
            $taskres{'distance'} = $formula->{'mindist'};
        }
        $taskres{'result'} = $ref->{'tarResultType'};
        $taskres{'startSS'} = $ref->{'tarSS'};
        $taskres{'endSS'} = $ref->{'tarES'};
        # OZGAP2005 
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
        my $pilrdist;

        $tarPk = $pil->{'tarPk'};
        $penalty = $pil->{'penalty'};

        # Pilot distance score 
        # FIX: should round $pil->distance properly?
        # $pilrdist = round($pil->{'distance'}/100.0) * 100;

        $Pdist = $Adistance * 
            (($pil->{'distance'}/$taskt->{'maxdist'}) * $formula->{'lineardist'}
            + $kmdiff->[floor($pil->{'distance'}/100.0)] * (1-$formula->{'lineardist'}));

        print "$tarPk lin dist: ", $Adistance * ($pil->{'distance'}/$taskt->{'maxdist'}) * $formula->{'lineardist'}, " dif dist: ", $Adistance * $kmdiff->[floor($pil->{'distance'}/100.0)] * (1-$formula->{'lineardist'});
        # Pilot speed score
        print "$tarPk speed: ", $pil->{'time'}, ", $Tmin\n";
        if ($pil->{'time'} > 0)
        {
            $Pspeed = $Aspeed * (1-(($pil->{'time'}-$Tmin)/3600/sqrt($Tmin/3600))**(2/3));
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
        if ($task->{'departure'} eq 'leadout')
        {
            # Leadout point (instead of departure)
            if ($pil->{'startSS'} > $taskt->{'firstdepart'})
            {
                # adjust for late starters
                $pil->{'coeff'} = $pil->{'coeff'} + ($pil->{'startSS'} - $taskt->{'firstdepart'});
            }
            print "$traPk leadout: ", $pil->{'coeff'}, ", $Cmin\n";
            if ($pil->{'coeff'} > 0)
            {
                if ($pil->{'coeff'} <= $Cmin)
                {
                    $Pdepart = $Astart;
                }
                elsif ($Cmin <= 0)
                {
                    $Pdepart = 0;
                }
                else
                {
                    $Pdepart = $Astart * (1-(($pil->{'coeff'}-$Cmin)/3600/sqrt($Cmin/3600))**(2/3));
                }
                print "$tarPk Pdepart: $Pdepart\n";
            }
        }
        else
        {
            # Normal departure points ..
            $x = ($pil->{'startSS'} - $taskt->{'firstdepart'})/$formula->{'nomtime'};
            if ($x < 1/2 && $pil->{'time'} > 0)
            {
                $Pdepart = $Pspeed*$Astart/$Aspeed*(1-6.312*$x+10.932*($x*$x)-2.990*($x*$x*$x));
                #$Pdepart = $Astart*(1-6.312*$x+10.932*($x*$x)-2.990*($x*$x*$x));
                #$Pdepart = $Aspeed/6*(1-6.312*$x+10.932*($x*$x)-2.990*($x*$x*$x));
            }
        }

        # Sanity
        if ($Pdepart < 0)
        {
            $Pdepart = 0;
        }


        # Pilot arrival score
        $Parrival = 0;
        if ($pil->{'time'} > 0)
        {
            if ($formula->{'class'} eq 'ozgap' && $formula->{'version'} ne '2000')
            {
                # OzGAP / Timed arrival
                print "$tarPk time arrival ", $pil->{'timeafter'}, ", $Ngoal\n";
                $x = 1-$pil->{'timeafter'}/(90*60);
            }
            else
            {   
                # Place arrival
                print "$tarPk place arrival ", $pil->{'place'}, ", $Ngoal\n";
                $x = 1-($pil->{'place'}-1)/($Ngoal);
            }

            $Parrival = $Aarrival*(0.2+0.037*$x+0.13*($x*$x)+0.633*($x*$x*$x));
            print "x=$x parrive=$Parrival\n";
        }
        if ($Parrival < 0)
        {
            $Parrival = 0;
        }

        # Penalty for not making goal ..
        if ($pil->{'goal'} == 0)
        {
            $Pspeed = $Pspeed - $Pspeed * $formula->{'sspenalty'};
            $Parrival = $Parrival - $Parrival * $formula->{'sspenalty'}; 
        }

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

        $Pscore = $Pdist + $Pspeed + $Parrival + $Pdepart - $penalty;

        # Store back into tblTaskResult ...
        if (defined($tarPk))
        {
            print "update $tarPk: d:$Pdist, s:$Pspeed, p: $penalty, a:$Parrival, g:$Pdepart\n";
            $sth = $dbh->prepare("update tblTaskResult set
                tarDistanceScore=$Pdist, tarSpeedScore=$Pspeed, 
                tarArrival=$Parrival, tarDeparture=$Pdepart, tarScore=$Pscore
                where tarPk=$tarPk");
            $sth->execute();
        }
    }
}


1;

