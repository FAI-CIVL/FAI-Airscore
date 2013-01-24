#!/usr/bin/perl


#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2011
#

package NoGap;

use Data::Dumper;
require Gap;
@ISA = ( "Gap" );

#require DBD::mysql;
#use POSIX qw(ceil floor);
#use Math::Trig;
#use TrackLib qw(:all);


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

    $sth = $dbh->prepare("select count(tarPk) as TotalPilots, sum(tarDistance) as TotalDistance, sum((tarDistance > 0) or (tarResultType='lo')) as TotalLaunched FROM tblTaskResult where tasPk=$tasPk and tarResultType <> 'abs'");

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
#    
# Points Allocation:
#
# Directly allocate the distance points (+pen). 
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
    #print Dumper($taskt);

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
        $taskres{'distance'} = $ref->{'tarLeadingCoeff'};
        # set pilot to min distance if they're below that ..
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
        my $Pspeed = 0;
        my $Parrival = 0;
        my $Pdepart = 0;
        my $Pscore;
        my $tarPk;
        my $penalty;

        $tarPk = $pil->{'tarPk'};
        $penalty = $pil->{'penalty'};

        # Pilot distance score 
        $Pdist = $pil->{'distance'};

        if (($pil->{'result'} eq 'dnf') or ($pil->{'result'} eq 'abs'))
        {
            $Pdist = 0;
            $Pspeed = 0;
            $Parrival = 0;
            $Pdepart = 0;
        }

        $Pscore = $Pdist - $penalty;

        # Store back into tblTaskResult ...
        if (defined($tarPk))
        {
            print "update $tarPk: d:$Pdist, s:$Pspeed, p: $penalty, a:$Parrival, g:$Pdepart\n";
            print "update tblTaskResult set tarDistanceScore=$Pdist, tarSpeedScore=$Pspeed, tarScore=$Pscore where tarPk=$tarPk\n";
            $sth = $dbh->prepare("update tblTaskResult set tarDistanceScore=$Pdist, tarSpeedScore=$Pspeed, tarScore=$Pscore where tarPk=$tarPk");
            $sth->execute();
        }
    }
}


1;

