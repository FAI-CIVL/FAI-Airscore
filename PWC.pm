#!/usr/bin/perl -I/home/geoff/bin


#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2016
#
# PWC differences
# 1. No arrival points (go to time) if ESS != Goal
# 1a. Altitude Arrival points if ESS == Goal (wtf?) (@todo)
# 2. LC2 - lead coeff^2
# 3. Launch validity altered?
# 4. Stopped task different
#       - if in goal - subtract time points == goal at ESS task stop time
#       - if pilot has made ESS, then complete flight is scored even after task stop time
#       - if not a race, then every pilot scored for the time in the air of the last pilot to start

package PWC;

require Gap;
@ISA = ( "Gap" );

#require DBD::mysql;
#use POSIX qw(ceil floor);
#use Math::Trig;
use Data::Dumper;
#use TrackLib qw(:all);


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

    # Launch Validity
    $x = $taskt->{'launched'}/$taskt->{'pilots'};
    $launch  = 0.028*$x + 2.917*$x*$x - 1.944*$x*$x*$x;
    $launch = $self->min([1, $launch]);
    if ($taskt->{'launchvalid'} == 0 or $launch < 0)
    {
        print "Launch invalid - dist quality set to 0\n";
        $launch = 0;
    }
    print "launch quality=$launch\n";

    # Distance Validity
    $distance = 2*($taskt->{'distance'}-$taskt->{'launched'}*$formula->{'mindist'}) / ($taskt->{'launched'}*(1+$formula->{'nomgoal'}/100)*($formula->{'nomdist'}-$formula->{'mindist'}))*($formula->{'nomgoal'}*($taskt->{'maxdist'}-$formula{'nomdist'}));
    $distance = $self->min([1, $distance]);
    print "distance validity=$distance\n";

    # Time Validity
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

    $time = 1;
    if ($x < 1)
    {
        $time = -0.271 + 2.912*$x - 2.098*$x*$x + 0.457*$x*$x*$x;
        $time = $self->min([1, $time]);
    }
    if ($time < 0.1) 
    {
        $time = 0.1;
    }
    print "time quality (tmin=$tmin x=$x)=$time\n";

    # Stop Validity
    # Fix - need $distlaunchtoess, $landed
    my $avgdist = $taskt->{'distance'} / $taskt->{'launched'};
    my $distlaunchtoess = $taskt->{'endssdistance'};
    # when calculating $stopv, to avoid dividing by zero when max distance is greater than distlaunchtoess i.e. when someone reaches goal if statement added.
    my $maxSSdist = 0;
    if (0<($distlaunchtoess - $taskt->{'maxdist'}))
    {
	$maxSSdist = ($distlaunchtoess - $taskt->{'maxdist'});
    }

    $x = ($taskt->{'landed'} / $taskt->{'launched'});
    print "sqrt( ($taskt->{'maxdist'} - $avgdist) / ($distlaunchtoess - $taskt->{'maxdist'}+1) * sqrt($taskt->{'stddev'} / 5) + $x*$x*$x )\n";
    my $stopv = sqrt( ($taskt->{'maxdist'} - $avgdist) / ($maxSSdist+1) * sqrt($taskt->{'stddev'} / 5) + $x*$x*$x );
    $stopv = $self->min([1, $stopv]);

    return ($distance,$time,$launch,$stopv);
}

sub ordered_results
{
    my ($self, $dbh, $task, $taskt, $formula) = @_;
    my @pilots;

    # Get all pilots and process each of them 
    # pity it can't be done as a single update ...
    $dbh->do('set @x=0;');
    $sth = $dbh->prepare("select \@x:=\@x+1 as Place, tarPk, tarDistance, tarSS, tarES, tarPenalty, tarResultType, tarLeadingCoeff2, tarGoal, tarLastAltitude from tblTaskResult where tasPk=? and tarResultType <> 'abs' order by case when (tarGoal=0 or tarES is null) then -999999 else tarLastAltitude end, tarDistance desc");
    $sth->execute($task->{'tasPk'});
    while ($ref = $sth->fetchrow_hashref()) 
    {
        my %taskres;

        %taskres = ();
        $taskres{'tarPk'} = $ref->{'tarPk'};
        $taskres{'penalty'} = $ref->{'tarPenalty'};
        $taskres{'distance'} = $ref->{'tarDistance'};
        $taskres{'stopalt'} = $ref->{'tarLastAltitude'};
        # set pilot to min distance if they're below that ..
        print "sstopped=", $task->{'sstopped'}, " stopalt=", $taskres{'stopalt'}, " glidebonus=", $formula->{'glidebonus'}, "\n";
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
        $taskres{'coeff'} = $ref->{'tarLeadingCoeff2'};
        # FIX: adjust against fastest ..
        if ((($ref->{'tarES'} - $ref->{'tarSS'}) < 1) and ($ref->{'tarSS'} > 0)) #only pilots that started and didn't make ESS
        {
            # Fix - busted if no one is in goal?
            if ($taskt->{'goal'} > 0)
            {
                # adjust for late starters
                print "No goal, adjust pilot coeff from: ", $ref->{'tarLeadingCoeff2'};
                $taskres{'coeff'} = $ref->{'tarLeadingCoeff2'} - ($task->{'sfinish'} - $taskt->{'lastarrival'}) * ($task->{'endssdistance'} - $ref->{'tarDistance'}) / 1800 / $task->{'ssdistance'} ;
            
                print " to: ", $taskres{'coeff'}, "\n";
                # adjust mincoeff?
                if ($taskres{'coeff'} < $task->{'mincoeff2'})
                {
                    $task->{'mincoeff2'} = $taskres{'coeff'};
                }
            }
        }

        push @pilots, \%taskres;
    }

    return \@pilots;
}

1;

