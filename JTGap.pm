#!/usr/bin/perl -w
#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2007
#

package JTGap;

require OzGap;
@ISA = ( "Gap" );

use POSIX qw(ceil floor);
#use Data::Dumper;

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
    my $taskt;
    my ($comPk, $tasPk);
    my $maxdist;

    $taskt = Gap::task_totals($self, $dbh, $task, $formula);
    #print Dumper($taskt);

    $maxdist = 0;
    $tasPk = $task->{'tasPk'};
    $comPk = $task->{'comPk'};

    $sth = $dbh->prepare("select max(TR.tarDistance * H.hanHandicap) as MaxDist from tblTaskResult TR join tblTrack T on TR.traPk=T.traPk left outer join tblHandicap H on H.pilPk=T.pilPk and H.comPk=$comPk where TR.tasPk=$tasPk");

    $sth->execute();
    if ($ref = $sth->fetchrow_hashref())
    {
        $maxdist = 0 + $ref->{'MaxDist'};
    }
    if ($maxdist < 0.1)
    {
        $maxdist = 0.1;
    }

    $taskt->{'maxdist'} = $maxdist;
    return $taskt;
}


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
    $comPk = $task->{'comPk'};
    $quality = $taskt->{'quality'};
    $Ngoal = $taskt->{'goal'};
    $Nfly = $taskt->{'launched'};
    $Nlo = $Nfly - $Ngoal;
    $Tmin = $taskt->{'fastest'};
    $Tfarr = $taskt->{'firstarrival'};
    $Cmin = $taskt->{'mincoeff'};

    print "comPk=$comPk Nfly=$Nfly Nlo=$Nlo\n";

    # Some GAP basics
    ($Adistance, $Aspeed, $Astart, $Aarrival) = $self->points_weight($task, $taskt, $formula);

    # Get all pilots and process each of them 
    # pity it can't be done as a single update ...
    $dbh->do('set @x=0;');
    $sth = $dbh->prepare("select \@x:=\@x+1 as Place, TR.tarPk, TR.tarDistance, TR.tarSS, TR.tarES, TR.tarPenalty, TR.tarResultType, TR.tarLeadingCoeff, TR.tarGoal, H.hanHandicap from tblTaskResult TR join tblTrack T on TR.traPk=T.traPk left outer join tblHandicap H on H.pilPk=T.pilPk and H.comPk=$comPk where tasPk=$tasPk and tarResultType <> 'abs' order by tarDistance desc, tarES");
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
        $taskres{'timeafter'} = $ref->{'tarES'} - $Tfarr;
        $taskres{'place'} = $ref->{'Place'};
        $taskres{'time'} = $taskres{'endSS'} - $taskres{'startSS'};
        $taskres{'goal'} = $ref->{'tarGoal'};
        $taskres{'handicap'} = $ref->{'hanHandicap'};
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

        $Pdist = $Adistance * (($pil->{'distance'}*$pil->{'handicap'})/$taskt->{'maxdist'});

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
            # OzGAP / Timed arrival
            print "$tarPk time arrival ", $pil->{'timeafter'}, ", $Ngoal\n";
            $x = 1-$pil->{'timeafter'}/(90*60);

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

