#!/usr/bin/perl

#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2007
#

require DBD::mysql;

use POSIX qw(ceil floor);
use Math::Trig;
use Data::Dumper;
use TrackLib qw(:all);

sub round 
{
    my ($number) = @_;
    return int($number + .5);
}

#
# work out task validity
#
sub day_quality
{
    my ($task) = @_;
    my $launch;
    my $distance;
    my $time;
    my $quality;
    my $topspeed;
    my $x;

    $sth = $dbh->prepare("SELECT TK.*, F.* FROM tblTask TK, tblFormula F, tblCompetition C WHERE TK.comPk=C.comPk AND F.forPk=C.forPk and TK.tasPk=$task");

    $launch = 0;
    $distance = 0;
    $time = 0;
    $quality = 0;

    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        $x = $ref->{'tasPilotsLaunched'}/$ref->{'tasPilotsTotal'};
        $launch  = 0.028*$x + 2.917*$x*$x - 1.944*$x*$x*$x;
        print "launch quality=$launch\n";
        if ($launch > 1) 
        {
            $launch = 1;
        }
        if ($launch < 0) 
        {
            $launch = 0;
        }

        $distance = 2*($ref->{'tasTotalDistanceFlown'}-$ref->{'tasPilotsLaunched'}*$ref->{'forMinDistance'}*1000) / ($ref->{'tasPilotsLaunched'}*(1+$ref->{'forNomGoal'}/100)*($ref->{'forNomDistance'}-$ref->{'forMinDistance'})) / 1000;
        print "distance quality=$distance\n";
        if ($distance > 1) 
        {
            $distance = 1;
        }
        if ($distance < 0) 
        {
            $distance = 0;
        }
            
        if ($ref->{'tasPilotsGoal'} > 0)
        {
            $tmin = $ref->{'tasFastestTime'};
            $x = $tmin / ($ref->{'forNomTime'} * 60);
        }
        else
        {
            $x = $ref->{'forNomTime'} * $ref->{'tasMaxDistance'} / $ref->{'forNomDistance'};
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

        $quality = $launch * $distance * $time;
        if ($quality > 1.0) 
        {
            $quality = 1.0;
        }
    }

    # FIX: TeamTask perhaps?
    #$sth = $dbh->prepare("update tblTask set tasQuality=$quality, tasDistQuality=$distance, tasTimeQuality=$time, tasLaunchQuality=$launch where tasPk=$task");
    #$sth->execute();


    return $quality;
}

#
# Aggregate Individual Results into a team result for scoring
# FIX: complicated by needing to select 3 scoring pilots only ...
# 
sub aggregate_team
{
    my ($tasPk) = @_;
    my $comPk;
    my %teams;
    my $lastteam;
    my ($dist, $start, $speed, $goal, $ss, $es, $tps, $rest);
    my $count;
    my ($numscoring,$method,$over);
    my $row;

    # find max scoring per team ..
    $count = 0;
    $dist = 0;
    $tps = 0;
    $es = 1;
    $ss = 99999999;
    $goal = -1;
    $start = 99999999;

    $sth = $dbh->prepare("select * from tblCompetition C, tblTask T where C.comPk=T.comPk and tasPk=$tasPk");
    $sth->execute();
    $ref = $sth->fetchrow_hashref();
    $comPk = $ref->{'comPk'};
    $numscoring = $ref->{'comTeamSize'};
    $over = $ref->{'comTeamOver'};
    $how = $ref->{'comTeamScoring'};

    #"select R.*,T.*,P.* FROM tblTaskResult R, tblTrack TR, tblTeam T, tblTeamPilot P where R.traPk=TR.traPk and R.tasPk=$tasPk and T.comPk=$comPk and T.teaPk=P.teaPk and TR.pilPk=P.pilPk order by T.teaPk,P.tepPreference");
    $sth = $dbh->prepare(
    "select * from tblTrack T join tblTaskResult TR on T.traPk=TR.traPk join tblTask TK on TK.tasPk=TR.tasPk join tblTeam M on M.comPk=TK.comPk join tblTeamPilot TP on TP.teaPk=M.teaPk where TR.tasPk=$tasPk and TP.pilPk=T.pilPk order by M.teaPk,TP.tepPreference");
    # Find aggregate for the N scoring pilots (based on pref / how about 'best?)
    $sth->execute();
    $lastteam = -1;
    while ($ref = $sth->fetchrow_hashref()) 
    {
        print "Team=", $ref->{'teaPk'}, " Pilot=", $ref->{'pilPk'}, "\n";
        if ($ref->{'teaPk'} != $lastteam)
        {
            # store the previous team?
            if ($lastteam > -1)
            {
                $row = {};

                print "count=$count numscoring=$numscoring\n";
                if ($count < $numscoring)
                {
                    $goal = 0;
                    $es = 0;
                }
                $row->{'goal'} = $goal;
                $row->{'start'} = $start;
                $row->{'ss'} = $ss;
                $row->{'es'} = $es;
                $row->{'dist'} = $dist;
                $row->{'tps'} = $tps;
                #$row->{'speed'} = $dist * 3.6 / $row->{'time'};
                $row->{'speed'} = 0;
                $rest = 'lo';
                if ($goal > 0)
                {
                    $rest = 'goal';
                }
                $row->{'rest'} = $rest;
                $teams{$lastteam} = $row;
            }
            
            # clear variables for next ..
            $lastteam = $ref->{'teaPk'};
            $dist = 0;
            $count = 0;
            $tps = 0;
            $goal = -1;
            $es = 1;
            $ss = 99999999;
            $start = 99999999;
        }

        $count++;
        if ($count > $numscoring)
        {
            next;
        }

        $dist = $dist + $ref->{'tarDistance'};
        if (0+$ref->{'tarGoal'} == 0)
        {
            $goal = 0;
        }
        else
        {
            if ($goal == -1)
            {
                $goal = $ref->{'tarGoal'};
            }
            elsif ($goal != 0)
            {
                $goal = $goal + $ref->{'tarGoal'};
            }
        }
        #print "goal=$goal\n";

        if ($ref->{'tarSS'} ne '' && $ref->{'tarSS'} < $ss)
        {
            $ss = $ref->{'tarSS'};
        }
        if ($ref->{'tarStart'} ne '' && $ref->{'start'} < $start)
        {
            $start = $ref->{'tarStart'};
        }
        #print "tarES=", $ref->{'tarES'}, "\n";
        if (0+$ref->{'tarES'} > $es)
        {
            if ($es > 0)
            {
                $es = $ref->{'tarES'};
            }
        }
        if (0+$ref->{'tarES'} == 0)
        {
            $es = 0;
        }
        print "es=$es\n";
        $tps = $tps + $ref->{'tarTurnpoints'};
    }
    $row = {};
    print "count=$count numscoring=$numscoring\n";
    if ($count < $numscoring)
    {
        $goal = 0;
        $es = 0;
    }
    $row->{'goal'} = $goal;
    $row->{'ss'} = $ss;
    $row->{'es'} = $es;
    $row->{'dist'} = $dist;
    $row->{'tps'} = $tps;
    $row->{'speed'} = 0;
    $row->{'start'} = $start;
    $rest = 'lo';
    if ($goal > 0)
    {
        $rest = 'goal';
    }
    $row->{'rest'} = $rest;
    $teams{$lastteam} = $row;

    # Now store them in TeamResult ..
    #terDistance ,    terStart ,      terGoal,
    #terResultType   enum ( 'abs', 'dnf', 'lo', 'goal' ) default 'lo',
    #terSS, terES, terTurnpoints,
    $dbh->do("delete from tblTeamResult where tasPk=$tasPk");

    foreach my $tot (keys %teams)
    {
        my $foo;
        $foo  = $teams{$tot};
        #print "insert into tblTeamResult (tasPk,teaPk,tarDistance,tarSpeed,tarStart,tarGoal,tarSS,tarES,tarTurnpoints) values (?,?,?,?,?,?,?,?,?)", $tasPk, " ", $tot, " ", $foo->{'dist'}, " ", $foo->{'speed'}, " ", $foo->{'start'}, " ", $foo->{'goal'}, " ", $foo->{'ss'}, " ", $foo->{'es'}, " ", $foo->{'tps'}, "\n";
        $dbh->do("insert into tblTeamResult (tasPk,teaPk,terDistance,terSpeed,terStart,terGoal,terSS,terES,terTurnpoints,terResultType) values (?,?,?,?,?,?,?,?,?,?)", undef, $tasPk, $tot, $foo->{'dist'}, $foo->{'speed'}, $foo->{'start'}, $foo->{'goal'}, $foo->{'ss'}, $foo->{'es'}, $foo->{'tps'}, $foo->{'rest'});
    }
}


#
# Find the task totals and update ..
#   tasTotalDistanceFlown, tasPilotsLaunched, tasPilotsTotal
#   tasPilotsGoal, tasPilotsLaunched, 
#
sub task_totals
{
    my ($task) = @_;
    my $totdist;
    my $launched;
    my $pilots;
    my $goal;
    my %taskt;
    my ($minarr, $fastest, $firstdep, $mincoeff);
    my ($teamsize, $over, $how);

    $sth = $dbh->prepare("select count(terPk) as TotalPilots, sum(terDistance) as TotalDistance, sum(terDistance > 0) as TotalLaunched FROM tblTeamResult where tasPk=$task and terResultType <> 'abs'");

    $sth->execute();
    $ref = $sth->fetchrow_hashref();
    $totdist = $ref->{'TotalDistance'};
    $launched = $ref->{'TotalLaunched'};
    $pilots = $ref->{'TotalPilots'};

    # pilots in goal?
    $sth = $dbh->prepare("select count(terPk) as GoalPilots from tblTeamResult where tasPk=$task and terGoal > 0");
    $sth->execute();
    $goal = 0;
    if ($ref = $sth->fetchrow_hashref())
    {
        $goal = $ref->{'GoalPilots'};
    }

    # fastest?
    $sth = $dbh->prepare("select min(terES-terSS) as MinTime, min(terES) as MinArr from tblTeamResult where tasPk=$task and terES > 0");
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
    $sth = $dbh->prepare("select min(terLeadingCoeff) as MinCoeff from tblTeamResult where tasPk=$task and terLeadingCoeff is not NULL");
    $sth->execute();
    $mincoeff = 0;
    if ($ref = $sth->fetchrow_hashref())
    {
        $mincoeff = $ref->{'MinCoeff'};
    }

    $maxdist = 0;
    $mindept = 0;
    $sth = $dbh->prepare("select max(terDistance) as MaxDist from tblTeamResult where tasPk=$task");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref())
    {
        $maxdist = $ref->{'MaxDist'};
    }

    $sth = $dbh->prepare("select min(terSS) as MinDept from tblTeamResult where tasPk=$task and terSS > 0 and terGoal > 0");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref())
    {
        $mindept = $ref->{'MinDept'};
    }

    # Give placings to pilots ...
    #update tblTeamResult t, (select @x:=@x+1 as rownum, tblTeamResult.tarPk 
    #from tblTeamResult order by tarDistance desc, tarES) r 
    #set t.tarPlace=r.rownum where t.tarPk = r.tarPk;

    # FIX: Store it in tblTask - TeamTask perhaps?

    #$sql = "update tblTask set tasTotalDistanceFlown=$totdist, tasPilotsTotal=$pilots, tasPilotsLaunched=$launched, tasPilotsGoal=$goal, tasFastestTime=$fastest, tasMaxDistance=$maxdist where tasPk=$task";
    ##print $sql;
    #$sth = $dbh->prepare($sql);
    #$sth->execute();
    #print "update tblTask set tasTotalDistanceFlown=$totdist, tasPilotsTotal=$pilots, tasPilotsLaunched=$launched, tasPilotsGoal=$goal where tasPk=$task\n";

    # task quality 
    $quality = day_quality($task);
    print "quality=$quality\n";

    $sth = $dbh->prepare("select * from tblCompetition C, tblTask T where tasPk=$task");
    $sth->execute();
    $ref = $sth->fetchrow_hashref();
    $teamsize = $ref->{'comTeamSize'};
    $over = $ref->{'comTeamOver'};
    $how = $ref->{'comTeamScoring'};

    $taskt{'pilots'} = $pilots;
    $taskt{'maxdist'} = $maxdist;
    $taskt{'distance'} = $totdist;
    #$taskt{'taskdist'} = $taskdist;
    $taskt{'launched'} = $launched;
    $taskt{'quality'} = $quality;
    $taskt{'goal'} = $goal;
    $taskt{'fastest'} = $fastest;
    $taskt{'firstdepart'} = $mindept;
    $taskt{'firstarrival'} = $minarr;
    $taskt{'mincoeff'} = $mincoeff;
    $taskt{'teamsize'} = $teamsize;
    $taskt{'teamover'} = $over;
    $taskt{'teamscoring'} = $how;

    return \%taskt;
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
    my ($task, $taskt) = @_;
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
    my $Aarrival;

    my @pilots;
    my @kmdiff;

    # Find fastest pilot into goal and calculate leading coefficients
    # for each track .. (GAP2002 only?)

    $tasPk = $task->{'tasPk'};
    $quality = $taskt->{'quality'};
    $Ngoal = $taskt->{'goal'};
    $Nfly = $taskt->{'launched'};
    $Tmin = $taskt->{'fastest'};
    $Tfarr = $taskt->{'firstarrival'};
    $Cmin = $taskt->{'mincoeff'};
    $Dmax = $taskt->{'maxdist'}/1000.0;

    $sth = $dbh->prepare("select T.*, F.* from tblTask T, tblCompetition C, tblFormula F where T.tasPk=$tasPk and C.comPk=T.comPk and F.forPk=C.forPk");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        $Tnom = $ref->{'forNomTime'} * 60;
        $Tmindist = $ref->{'forMinDistance'} * $taskt->{'teamsize'};
        #$Dmax = int($ref->{'tasMaxDistance'}/1000.0);
        $Fclass = $ref->{'forClass'};
        $Fversion = $ref->{'forVersion'};
    }
    print "Tnom=$Tnom Tmindist=$Tmindist Dmax=$Dmax Flcass=$Fclass Fversion=$Fversion\n";

    # Some GAP basics
    $x = $Ngoal/$Nfly;
    $distweight = 1-0.8*sqrt($x);
    print "distweight=$distweight($Ngoal/$Nfly)\n";
    $Adistance = 1000 * $quality * $distweight;

    # GAP 2000 - default
    $Aspeed = 1000 * $quality * (1-$distweight) * 5.6/8;
    $Astart = 1000 * $quality * (1-$distweight) * 1.4/8;
    $Aarrival = 1000 * $quality * (1-$distweight) * 1/8;

    if ($Fclass eq 'gap')
    {
        if ($Fversion eq '1998')
        {
            $Aspeed = 1000 * $quality * (1-$distweight) * 6/8;
            $Astart = 1000 * $quality * (1-$distweight) * 1/8;
            $Aarrival = 1000 * $quality * (1-$distweight) * 1/8;
        }
        elsif ($Fversion eq '2002')
        {
            $Aspeed = 1000 * $quality * (1-$distweight) * 5.6/8;
            $Astart = 1000 * $quality * (1-$distweight) * 1.4/8;
            $Aarrival = 1000 * $quality * (1-$distweight) * 1/8;
        }
        elsif ($Fversion eq '2007')
        {
            # FIX: can turn on/off start points
            $Aspeed = 1000 * $quality * (1-$distweight) * 5.6/8;
            $Astart = 1000 * $quality * (1-$distweight) * 1.4/8;
            $Aarrival = 1000 * $quality * (1-$distweight) * 1/8;
        }
    }

    if ($Fclass eq 'ozgap')
    {
        # OZGAP 2000
        $Aspeed = 1000 * $quality * (1-$distweight) * 2/4;
        $Astart = 1000 * $quality * (1-$distweight) * 1/4;
        $Aarrival = 1000 * $quality * (1-$distweight) * 1/4;

        # OZGAP 2005
        if ($Fversion eq '2005')
        {
            $Astart = 0;
            $Aspeed = 1000 * $quality * (1-$distweight) * 3/4;
            $Aarrival = 1000 * $quality * (1-$distweight) * 1/4;
        }

        if ($Fversion eq '2007')
        {
            # NB: this is timed arrival gap 2007 really ..
            # FIX: can turn on/off start points
            $Aspeed = 1000 * $quality * (1-$distweight) * 4.6/8;
            $Astart = 1000 * $quality * (1-$distweight) * 1.4/8;
            $Aarrival = 1000 * $quality * (1-$distweight) * 2/8;
        }
    }

    #print "premod: $Fclass:$Fversion Adist=$Adistance, Aspeed=$Aspeed, Astart=$Astart, Aarrival=$Aarrival, quality=$quality\n";

    # need to rescale if depart / arrival are "off"
    if ($task->{'arrival'} eq 'off' && $task->{'departure'} eq 'off')
    {
        $Adistance = 1000 * $quality * ($Adistance / ($Adistance+$Aspeed));
        $Aspeed = 1000 * $quality * ($Aspeed / ($Adistance+$Aspeed));
        $Astart = 0;
        $Aarrival = 0; 
    }
    elsif ($task->{'arrival'} eq 'off')
    {
        $Adistance = 1000 * $quality *($Adistance / ($Adistance+$Aspeed+$Astart));
        $Aspeed = 1000 * $quaity * ($Aspeed / ($Adistance+$Aspeed+$Astart));
        $Astart =  1000 * $quaity * ($Astart / ($Adistance+$Aspeed+$Astart));
        $Aarrival = 0; 
    }
    elsif ($task->{'departure'} eq 'off')
    {
        $Adistance = 1000 * $quality * ($Adistance / ($Adistance+$Aspeed+$Aarrival));
        $Aspeed = 1000 * $quality * ($Aspeed / ($Adistance+$Aspeed+$Aarrival));
        $Aarrival = 1000 * $quality * ($Aarrival / ($Adistance+$Aspeed+$Aarrival));
        $Astart = 0;
    }

    print "$Fclass:$Fversion Adist=$Adistance, Aspeed=$Aspeed, Astart=$Astart, Aarrival=$Aarrival, quality=$quality\n";
    print "Nfly=$Nfly\n";

    #

    # KM difficulty
    $sth = $dbh->prepare("select truncate(terDistance/1000,0) as Distance, count(truncate(terDistance/1000,0)) as Difficulty from tblTeamResult where tasPk=$tasPk and terResultType not in ('abs','dnf') group by truncate(terDistance/1000,0)");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        # populate kmdiff
        $kmdiff[(0+$ref->{'Distance'})] = 0+$ref->{'Difficulty'};
    }
    $x = 0;
    for my $dif (0 .. scalar @kmdiff-1)
    {
        my $sdif;
        my $landed;
        my $rdif;
        my $range;
        my $ddif;

        # FIX: currently assuming a range of 1km
        # not using this
        # $range = round($Dmax/($Nfly-$Ngoal));

        $landed = $kmdiff[$dif];
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
        $kmdiff[$dif] = ($sdif + $rdif) / 2;
        #print "$dif - sdif=$sdif rdif=$rdif kmdif = ", $kmdiff[$dif], "\n";
    }

    # Get all pilots and process each of them 
    # pity it can't be done as a single update ...
    $dbh->do('set @x=0;');
    $sth = $dbh->prepare("select \@x:=\@x+1 as Place, terPk, terDistance, terSS, terES, terPenalty, terResultType from tblTeamResult where tasPk=$tasPk and terResultType <> 'abs' order by terDistance desc, terES");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        my %taskres;

        %taskres = ();
        $taskres{'terPk'} = $ref->{'terPk'};
        $taskres{'penalty'} = $ref->{'terPenalty'};
        $taskres{'distance'} = $ref->{'terDistance'};
        # set pilot to min distance if they're below that ..
        if ($taskres{'distance'} < $Tmindist * 1000.0)
        {
            $taskres{'distance'} = $Tmindist * 1000.0;
        }
        $taskres{'result'} = $ref->{'terResultType'};
        $taskres{'startSS'} = $ref->{'terSS'};
        $taskres{'endSS'} = $ref->{'terES'};
        # OZGAP2005 
        $taskres{'timeafter'} = $ref->{'terES'} - $Tfarr;
        $taskres{'place'} = $ref->{'Place'};
        $taskres{'time'} = $taskres{'endSS'} - $taskres{'startSS'};
        if ($taskres{'time'} < 0)
        {
            $taskres{'time'} = 0;
        }
        # Leadout Points
        $taskres{'coeff'} = $ref->{'terLeadingCoeff'};
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
        my $terPk;
        my $penalty;

        $terPk = $pil->{'terPk'};
        $penalty = $pil->{'penalty'};

        # Pilot distance score 
        #print "task->maxdist=", $taskt->{'maxdist'}, "\n";
        #print "pil->distance/(2*maxdist)=", $pil->{'distance'}/(2*$taskt->{'maxdist'}), "\n";
        #print "kmdiff=", $kmdiff[floor($pil->{'distance'}/1000.0)], "\n";
        $Pdist = $Adistance * ($pil->{'distance'}/(2*$taskt->{'maxdist'}) 
                    + $kmdiff[floor($pil->{'distance'}/1000.0)]);

        # Pilot speed score
        print "$terPk speed: ", $pil->{'time'}, ", $Tmin\n";
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

        # Pilot departure score
        print "$terPk team->startSS=", $pil->{'startSS'}, "\n";
        print "$tarPk team->endSS=", $pil->{'endSS'}, "\n";
        print "$tarPk task->first=", $taskt->{'firstdepart'}, "\n";

        $Pdepart = 0;
        if ($task->{'departure'} eq 'leadout')
        {
            # Leadout point (instead of departure)
            if ($pil->{'startSS'} > $taskt->{'firstdepart'})
            {
                # adjust for late starters
                $pil->{'coeff'} = $pil->{'coeff'} + ($pil->{'startSS'} - $taskt->{'firstdepart'});
            }
            print "$terPk leadout: ", $pil->{'coeff'}, ", $Cmin\n";
            if ($pil->{'coeff'} > 0 && $Cmin > 0)
            {
                $Pdepart = $Astart * (1-(($pil->{'coeff'}-$Cmin)/sqrt($Cmin))**(2/3));
            }
        }
        else
        {
            # Normal departure points ..
            $x = ($pil->{'startSS'} - $taskt->{'firstdepart'})/$Tnom;
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
            # OzGAP 2005
            if (($Fclass eq 'ozgap') && ($Fversion eq '2005'))
            {
                print "$terPk time arrival ", $pil->{'timeafter'}, ", $Ngoal\n";
                $x = 1-$pil->{'timeafter'}/(90*60);
            }
            else
            {
                print "$terPk place arrival ", $pil->{'place'}, ", $Ngoal\n";
                $x = 1-($pil->{'place'}-1)/($Ngoal);
            }

            $Parrival = $Aarrival*(0.2+0.037*$x+0.13*($x*$x)+0.633*($x*$x*$x));
            print "x=$x parrive=$Parrival\n";
        }
        if ($Parrival < 0)
        {
            $Parrival = 0;
        }

        if ($pil->{'result'} eq 'dnf' or $pil->{'result'} eq 'abs')
        {
            $Pdist = 0;
            $Pspeed = 0;
            $Parrival = 0;
            $Pdepart = 0;
        }

        $Pscore = $Pdist + $Pspeed + $Parrival + $Pdepart - $penalty;

        # Store back into tblTeamResult ...
        if (defined($terPk))
        {
            print "update $terPk: d:$Pdist, s:$Pspeed, a:$Parrival, g:$Pdepart\n";
            $sth = $dbh->prepare("update tblTeamResult set
                terDistanceScore=$Pdist, terSpeedScore=$Pspeed,
                terArrival=$Parrival, terDeparture=$Pdepart, terScore=$Pscore
                where terPk=$terPk");
            $sth->execute();
        }
    }
}


#
# Main program here ..
#

my $taskt;
my $task;
my $tasPk;
my $quality;

$dbh = db_connect();

# Get the tasPk 
$tasPk = $ARGV[0];

# aggregate individual results into teamresult
aggregate_team($tasPk);

# Work out all the task totals from task results
$taskt = task_totals($tasPk);

# Read the task itself ..
$task = read_task($tasPk);

# Now allocate points to pilots ..
points_allocation($task,$taskt);

