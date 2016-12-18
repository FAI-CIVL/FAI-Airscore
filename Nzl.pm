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
    my $pilots;
    my $taskt;
    my $tasPk;
    my ($minarr, $fastest, $firstdep, $mincoeff);
    my $mindist;
    my $topnine;
    my $stop;
    my $stddev;

    $taskt = Gap::task_totals(@_);

    $mindist = 0;
    $tasPk = $task->{'tasPk'};
    $sth = $dbh->prepare("select F.*, T.tasStoppedTime from tblTask T, tblCompetition C, tblFormula F where T.tasPk=$tasPk and C.comPk=T.comPk and F.forPk=C.forPk");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref()) 
    {
        # convert to metres ...
        $stop = $ref->{'tasStoppedTime'};
        $mindist = $ref->{'forMinDistance'} * 1000;
    }

    # FIX: failsafe for now?
    if ($mindist == 0)
    {
        print "WARNING: mindist was 0, using 5000m instead\n";
        $mindist = 5000;
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

    $maxdist = 0;
    $mindept = 0;
    $sth = $dbh->prepare("select max(tarDistance) as MaxDist from tblTaskResult where tasPk=$tasPk");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref())
    {
        $maxdist = 0 + $ref->{'MaxDist'};
    }

    # Get the top 90% dist ...
    $topnine = 0;
    $dbh->do('set @x=0;');
    $sth = $dbh->prepare("select \@x:=\@x+1 as Place, tarDistance, (tarLastTime - tarSS) as airTime from tblTaskResult where tasPk=$tasPk and (tarResultType='lo' or tarResultType='goal') order by tarDistance desc");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        if ($fastest == 0 && $ref->{'Place'} == 1)
        {
            $fastest = $ref->{'airTime'};
        }

        if ($ref->{'Place'} <= $self->round($taskt->{'pilots'} * 0.90))
        {
            $topnine = $topnine + $ref->{'tarDistance'};
        }
    }
    print "distance=$totdist 90%dist=$topnine\n";

    # task quality 
    $taskt->{'maxdist'} = $maxdist;
    $taskt->{'fastest'} = $fastest;
    $taskt->{'firstdepart'} = $mindept;
    $taskt->{'firstarrival'} = $minarr;
    $taskt->{'mincoeff'} = $mincoeff;
    $taskt->{'topninety'} = $topnine;
    $taskt->{'stopped'} = $stop;

    return $taskt;
}

#
# Calculate Task Validity - NZ
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

    $distance = $taskt->{'topninety'} / $self->round($taskt->{'pilots'} * 0.9) 
            / ($formula->{'nomdist'} / 1000) / 1000;
    print "top90=", $taskt->{'topninety'}, " launched=", $self->round($taskt->{'launched'} * 0.9), " nomdist=", $formula->{'nomdist'} / 1000;
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

    return ($distance,$time,$launch,1);
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
    my $leading;

    
    # Way simple for NZ (no departure / leadout or arrival)
    $x = $taskt->{'goal'} / $taskt->{'launched'};
    $distweight = 1-0.6*sqrt($x);

    $quality = $taskt->{'quality'};
    $Fversion = $formula->{'version'};
    $leading = $formula->{'weightstart'} * 1000;

    # need to rescale if depart / arrival are "off"
    if ($task->{'departure'} eq 'off')
    {
        $Astart = 0;
        $Aarrival = 0; 
        $Adistance = 1000 * $quality * $distweight;
        $Aspeed = 1000 * $quality * (1-$distweight);
    }
    else
    {
        $Astart = $leading * $quality;
        $Aarrival = 0; 
        $Adistance = (1000 - $leading) * $quality * $distweight;
        $Aspeed = (1000 - $leading)* $quality * (1-$distweight);
    }


    print "points_weight: ($Fversion) Adist=$Adistance, Aspeed=$Aspeed, Astart=$Astart, Aarrival=$Aarrival\n";

    return ($Adistance, $Aspeed, $Astart, $Aarrival);

}

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

    my $sorted_pilots;
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

    my $sorted_pilots = $self->ordered_results($dbh, $task, $taskt, $formula);

    # Some GAP basics
    ($Adistance, $Aspeed, $Astart, $Aarrival) = $self->points_weight($task, $taskt, $formula);

    # Score each pilot now 
    for my $pil ( @$sorted_pilots )
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
        $Pdist = $Adistance * sqrt($pil->{'distance'}/$taskt->{'maxdist'});

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
            print "Pspeed is nan for $tarPk, pil->{'time'}=", $pil->{'time'}, "\n";
            $Pspeed = 0;
        }

        #print "$tarPk pil->startSS=", $pil->{'startSS'}, "\n";
        #print "$tarPk pil->endSS=", $pil->{'endSS'}, "\n";
        #print "$tarPk tast->first=", $taskt->{'firstdepart'}, "\n";

        # Pilot departure/leading points
        $Pdepart = $self->pilot_departure_leadout($formula, $task, $taskt, $pil, $Astart, $Aspeed);

        # No arrival NZ
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

