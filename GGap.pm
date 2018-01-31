#!/usr/bin/perl -I/home/geoff/bin


#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2007
#

package GGap;

require Gap;
@ISA = ( "Gap" );

#require DBD::mysql;
use POSIX qw(ceil floor);
use Data::Dumper;
use strict;
#use Math::Trig;
#use TrackLib qw(:all);

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

    $x = $taskt->{'median'} / $formula->{'nomdist'};
    if ($x < 1) 
    {
        $distance = $x;

        #$distance = -0.271 + 2.912*$x - 2.098*$x*$x + 0.457*$x*$x*$x;
        #if ($distance < 0)
        #{
        #    $distance = 0;
        #}
    }
    else 
    {
        $distance = 1;
    }
    print "distance quality=$distance\n";
            
    my $tmin;
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
    print "time quality (tmin=$tmin x=$x)=$time\n";
    if ($time > 1) 
    {
        $time = 1;
    }
    if ($time < 0.1) 
    {
        $time = 0.1;
    }

    return ($distance,$time,$launch,1);
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
        $Pspeed = $Aspeed * (1-(($Ptime-$Tmin)/3600/sqrt($Tmin/1800))**(2/3));
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

sub points_weight
{
    my ($self, $task, $taskt, $formula) = @_;
    my $distweight;
    my $Adistance;
    my $Aspeed;
    my $Astart;
    my $Aarrival = 0;
    my $x;

    my $quality = $taskt->{'quality'};

    #print "distweight=$distweight($Ngoal/$Nfly)\n";
    my $leading = $formula->{'weightstart'} * 1000;

    $x = $taskt->{'goal'} / $taskt->{'launched'};
    $distweight = 1-0.8*sqrt($x);
    my $Fversion = $formula->{'version'};
    
    # need to rescale if depart / arrival are "off"
    if ($task->{'departure'} eq 'off')
    {
        $Astart = 0;
        if ($task->{'arrival'} eq 'on')
        {
            $Adistance = 1000 * $quality * $distweight;
            $Aspeed = 1000 * $quality * (1-$distweight) * 3/4;
            $Aarrival = 1000 * $quality * (1-$distweight) * 1/4;
        }
        else
        {
            $Aarrival = 0; 
            $Adistance = 1000 * $quality * $distweight;
            $Aspeed = 1000 * $quality * (1-$distweight);
        }
    }
    else
    {
        $Astart = $leading * $quality;
        if ($task->{'arrival'} eq 'on')
        {
            $Adistance = (1000 - $leading) * $quality * $distweight;
            $Aspeed = (1000 - $leading) * $quality * (1-$distweight) * 3/4;
            $Aarrival = (1000 - $leading) * $quality * (1-$distweight) * 1/4;
        }
        else
        {
            $Aarrival = 0; 
            $Adistance = (1000 - $leading) * $quality * $distweight;
            $Aspeed = (1000 - $leading)* $quality * (1-$distweight);
        }
    }


    print "points_weight: (GGap) Adist=$Adistance, Aspeed=$Aspeed, Astart=$Astart, Aarrival=$Aarrival\n";

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
    my $Fclass;
    my $Fversion;
    my $Cmin;

    my $x;
    my $distweight;

    my $Adistance;
    my ($Aspeed, $Astart, $Aarrival);

    my $penspeed;
    my $pendist;
    my $difdist;

    my @pilots;
    my @tmarker;
    my ($sub, $sref);
    my $hbess;

    # Find fastest pilot into goal and calculate leading coefficients
    # for each track .. (GAP2002 only?)

    $tasPk = $task->{'tasPk'};
    $quality = $taskt->{'quality'};
    $Ngoal = $taskt->{'goal'};
    $Nfly = $taskt->{'launched'};
    $Tmin = $taskt->{'fastest'};
    $Tfarr = $taskt->{'firstarrival'};
    $Cmin = $taskt->{'mincoeff'};

    $Tnom = $formula->{'nomtime'} * 60;
    $Tmindist = $formula->{'mindist'};
    $Fclass = $formula->{'class'};
    $Fversion = $formula->{'version'};

    print "Tnom=$Tnom Tmindist=$Tmindist Flcass=$Fclass Fversion=$Fversion Nfly=$Nfly\n";

    # Some GAP basics
    ($Adistance, $Aspeed, $Astart, $Aarrival) = $self->points_weight($task, $taskt, $formula);

    #$kmdiff = $self->calc_kmdiff($dbh, $task, $taskt, $formula);
    #print Dumper($kmdiff);

    # Get all pilots and process each of them 
    # pity it can't be done as a single update ...
    $dbh->do('set @x=0;');
    my $sth = $dbh->prepare("select \@x:=\@x+1 as Place, tarPk, traPk, tarDistance, tarSS, tarES, tarPenalty, tarResultType, tarLeadingCoeff, tarGoal, tarLastAltitude from tblTaskResult where tasPk=$tasPk and tarResultType <> 'abs' order by tarDistance desc, tarES");
    $sth->execute();
    my $ref;
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
        if ($taskres{'stopalt'} > 0)
        {
            $taskres{'distance'} = $taskres{'distance'} + $formula->{'glidebonus'} * ($taskres{'stopalt'} - $task->{'goalalt'});
        }
        if ($taskres{'distance'} > $task->{'short_distance'})
        {
            $taskres{'distance'} = $task->{'short_distance'};
        }
        if ($taskres{'distance'} < $formula->{'mindist'})
        {
            $taskres{'distance'} = $formula->{'mindist'};
        }
        print $ref->{'traPk'}, " effective dist=", $taskres{'distance'}, " glide bonus=", $formula->{'glidebonus'} * ($taskres{'stopalt'} -$task->{'goalalt'}), "\n";
        $taskres{'result'} = $ref->{'tarResultType'};
        $taskres{'startSS'} = $ref->{'tarSS'};
        $taskres{'endSS'} = $ref->{'tarES'};
        # OZGAP2005 
        $taskres{'timeafter'} = $ref->{'tarES'} - $Tfarr;
        $taskres{'place'} = $ref->{'Place'};
        $taskres{'time'} = $taskres{'endSS'} - $taskres{'startSS'};
        $taskres{'goal'} = $ref->{'tarGoal'};
        $taskres{'lastalt'} = $ref->{'tarLastAltitude'};
        # Determine ESS time bonus against goal height
        $hbess = 0;
        if ($task->{'heightbonus'} eq 'on' and $taskres{'goal'} > 0)
        {
            my $habove = $taskres{'lastalt'} - $task->{'goalalt'};
            print "    habove: $habove (", $task->{'goalalt'}, ")\n";
            if ($habove > 400)
            {
                $habove = 400;
            }
            if ($habove > 50)
            {
                print "    oldtime=", $taskres{'time'};
                $hbess = 20.0*(($habove-50.0)**0.40);
                $taskres{'time'} = $taskres{'time'} - $hbess;
                print " hbess=$hbess time=", $taskres{'time'}, "\n";
                if ($taskres{'time'} < $Tmin)
                {
                    $Tmin = $taskres{'time'};
                    $taskt->{'fastest'} = $Tmin;
                }
            }
        }
        $taskres{'hbess'} = $hbess;

        if ($taskres{'time'} < 0)
        {
            $taskres{'time'} = 0;
        }
        # Leadout Points
        $taskres{'coeff'} = $ref->{'tarLeadingCoeff'};
        $taskres{'kmmarker'} = [];
        # FIX: adjust against fastest ..
        my $kt = $taskres{'kmmarker'};
        $sub = $dbh->prepare("select * from tblTrackMarker where traPk=" . $taskres{'traPk'} . " order by tmDistance");
        $sub->execute();
        while ($sref = $sub->fetchrow_hashref()) 
        {
            #print "sref=",, $sref->{'tmTime'}, "\n";
            push @$kt, $sref->{'tmTime'};
        }

        push @pilots, \%taskres;
    }

    # Stop stopped speed penalty
    my $stopped_reduction = 0;
    if ($task->{'sstopped'} > 0)
    {
        print "sstopped=", $task->{'sstopped'}, "\n";
        print "startSS=", $task->{'sstart'}, "\n";
        $stopped_reduction = $Aspeed * (1-((($task->{'sstopped'}-$task->{'sstart'})-$Tmin)/3600/sqrt($Tmin/3600))**(2/3));
        print "stopped_reduction=$stopped_reduction\n";
    }

    # Score each pilot now 
    my $kmarr;
    $kmarr = $taskt->{'kmmarker'};
    @tmarker = @$kmarr;
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
        #print "kmdiff=", $kmdiff->[floor($pil->{'distance'}/1000.0)], "\n";
        #print "$Pdist = $Adistance * (( pildist/maxdist", $pil->{'distance'}/$taskt->{'maxdist'}, " * lindist=", $formula->{'lineardist'}, " + kmdiff=" , $kmdiff->[floor($pil->{'distance'}/100.0)], " * lindist=", (1-$formula->{'lineardist'}), "\n";

        #$Pdist = $Adistance * (($pil->{'distance'}/$taskt->{'maxdist'}) * $formula->{'lineardist'}
        #        + $kmdiff->[floor($pil->{'distance'}/100.0)] * (1-$formula->{'lineardist'}));

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
            # Oz comps ...
            if ($task->{'sstopped'} == 0)
            {
                $Pspeed = 0;
            }
            $Parrival = 0;
        }

        if (($pil->{'result'} eq 'dnf') or ($pil->{'result'} eq 'abs'))
        {
            $Pdist = 0;
            $Pspeed = 0;
            $Parrival = 0;
            $Pdepart = 0;
        }

        # Penalties
        # $penalty = $self->pilot_penalty($formula, $task, $taskt, $pil, $Astart, $Aspeed);

        $Pscore = $Pdist + $Pspeed + $Parrival + $Pdepart - $penalty;

        # Store back into tblTaskResult ...
        if (defined($tarPk))
        {
            print "update $tarPk: dst:$Pdist, spd:$Pspeed, pen:$penalty, arr:$Parrival, dep:$Pdepart\n";
            $sth = $dbh->prepare("update tblTaskResult set
                tarDistanceScore=$Pdist, tarSpeedScore=$Pspeed, 
                tarArrival=$Parrival, tarDeparture=$Pdepart, tarScore=$Pscore
                where tarPk=$tarPk");
            $sth->execute();
        }
    }
}

1;

