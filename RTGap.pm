#!/usr/bin/perl -I/home/geoff/bin


#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2007
#

package RTGap;

require Gap;
@ISA = ( "Gap" );

#require DBD::mysql;
#use POSIX qw(ceil floor);
#use Math::Trig;
#use Data::Dumper;
#use TrackLib qw(:all);

sub points_weight
{
    my ($self, $task, $taskt, $formula) = @_;
    my $Fversion;
    my $quality;
    my $distweight;
    my ($Adistance, $Aspeed, $Astart, $Aarrival);
    my $x;


    $quality = $taskt->{'quality'};

    #print "distweight=$distweight($Ngoal/$Nfly)\n";
    $x = $taskt->{'goal'} / $taskt->{'launched'};
    $distweight = 1-0.8*sqrt($x);
    $Adistance = 1000 * $quality * $distweight;
    $Aspeed = 1000 * $quality * (1-$distweight);
    $Fversion = $formula->{'version'};

    print "points_weight (1): ($Fversion) Quality=$quality Adist=$Adistance, Aspeed=$Aspeed, Astart=$Astart, Aarrival=$Aarrival\n";

    return ($Adistance, $Aspeed, $Astart, $Aarrival);

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

    $launch = 1;
    $time = 1;

    $distance = 2*($taskt->{'distance'}-$taskt->{'launched'}*$formula->{'mindist'}) / 
        ($taskt->{'launched'}*(1+$formula->{'nomgoal'}/100)*($formula->{'nomdist'}-$formula->{'mindist'}));
    print "distance quality=$distance\n";

    if ($distance > 1) 
    {
        $distance = 1;
    }
    if ($distance < 0) 
    {
        $distance = 0;
    }
            
    return ($distance,$time,$launch);
}

#    POINTS ALLOCATION
#    Points Allocation:
#    x=Ngoal/Nfly
#    distweight =  1-0.8*x^0.5
#
# Pilot Distance Score:
# half of the available distance points is assigned linearly with the 
# distance flown; the other half is assigned considering the relative 
# difficulty of each km flown.
# DistancePoints = 
#   Available DistancePoints *(PilotDistance/(2*MaxDistance) + KmDiff)
#
# Pilot speed score:
# P.speed = 1-((PilotTime-Tmin)/radq(Tmin))^(2/3)
#
sub points_allocation
{
    my ($self, $dbh, $task, $taskt, $formula) = @_;
    my $tasPk;
    my $quality;
    my $Ngoal;
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

    # Find fastest pilot into goal and calculate leading coefficients
    # for each track .. (GAP2002 only?)

    $tasPk = $task->{'tasPk'};
    $quality = $taskt->{'quality'};
    $Ngoal = $taskt->{'goal'};
    $Tmin = $taskt->{'fastest'};
    $Tfarr = $taskt->{'firstarrival'};
    $Cmin = $taskt->{'mincoeff'};
    print Dumper($taskt);

    print "Nfly=$Nfly Nlo=$Nlo\n";

    # Some GAP basics
    ($Adistance, $Aspeed, $Astart, $Aarrival) = $self->points_weight($task, $taskt, $formula);


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

        $Pdist = $Adistance * (($pil->{'distance'}/$taskt->{'maxdist'});

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

        # No arrival/departure
        $Pdepart = 0;
        $Parrival = 0;

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


1;

