#!/usr/bin/perl

#
# Some track/database handling stuff
# And a bunch of big circle geometry stuff
#
# Notes: UTC is 13 seconds later than GPS time (!)
#        metres, kms, kms/h, DDMMYY HHMMSSsss, true north,
#        DDMM.MMMM (NSEW designators), hPascals
#
require      Exporter;
require DBD::mysql;

use Math::Trig;
use Time::Local;
use Data::Dumper;
use Defines qw(:all);

our @ISA       = qw(Exporter);
our @EXPORT = qw{:ALL};

*VERSION=\'%VERSION%';

$pi = atan2(1,1) * 4;    # accurate PI.

my $port = 3306;

local * FD;

#
# Database handling
#

my $dsn;
my $dbh;
my $drh;

sub db_connect
{
    $dsn = "DBI:mysql:database=$DATABASE;host=$MYSQLHOST;port=$port";
    $dbh = DBI->connect( $dsn, $MYSQLUSER, $MYSQLPASSWORD, { RaiseError => 1 } )
            or die "Can't connect: $!\n";
    $drh = DBI->install_driver("mysql");
    return $dbh;
}


sub insertup
{
    my ($table, $pkey, $clause, $pairs) = @_;
    my @keys;
    my @keystr;
    my $val;
    my $qmarks = '?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?';
    my $size;
    my $ref;
    my $sth;
    my $fields;

    @keys = keys %$pairs;

    if (defined($clause))
    {
        #print("select * from $table where $clause\n");
        $sth = $dbh->prepare("select * from $table where $clause");
        $sth->execute();
        $ref = $sth->fetchrow_hashref();
    }

    if (defined($ref))
    {
        # update fields
        for my $k ( @keys )
        {
            if ($pairs->{$k} ne '')
            {
                $ref->{$k} = $pairs->{$k};
            }

            push @keystr, $k . "=" . $dbh->quote($ref->{$k});
        }

        # create nice string
        $fields = join ",", @keystr;

        #print ("update $table set $fields where $clause\n");
        $dbh->do("update $table set $fields where $clause", undef);
        # return requested key value ..
        #print "insertup: ", $ref->{$pkey}, "\n";
        return $ref->{$pkey};
    }
    else
    {
        # else insert
        $fields = join(',', @keys);
        $size = scalar @keys;
        $qmarks = substr($qmarks, 0, $size*2-1);
        #print("INSERT INTO $table ($fields) VALUES ($qmarks)\n");
        #print Dumper($pairs);
        $dbh->do("insert into $table ($fields) VALUES ($qmarks)", undef, values %$pairs);
        # get last key insert for primary key value ..
        return $dbh->last_insert_id(undef,undef,$table,undef);
    }
}

#
# Store the tracklog in the database
# Take 'standard' form (see read_track) and save it
#

sub store_track
{
    my ($flight, $pilPk) = @_;
    my $traPk;
    my $coords;
    my $sth;
    my $num;
    my $rem;
    my $man;
    my $off = 0;
    my ($i, $j);

    # set to UTC since tracklogs record in UTC
    $dbh->do("set time_zone='+0:00'");
    $dbh->do("INSERT INTO tblTrack (pilPk, traDate, traStart, traDuration, traGlider) VALUES (?,?,from_unixtime(?),?,?)", undef, $pilPk, $flight->{'header'}->{'date'}, $flight->{'header'}->{'start'}, $flight->{'duration'}, $flight->{'glider'});
    $traPk = $dbh->last_insert_id(undef, undef, "tblTrack", undef);
    #print "max track=$traPk\n";

    $coords = $flight->{'coords'};
    $num = scalar @$coords;
    $rem = $num % 500;
    $man = int($num / 500);
    $i = 0;

    my $start;
    my $affected;
    my @arr;
    my $query = qq{INSERT INTO tblTrackLog (traPk, trlLatDecimal, trlLongDecimal, trlTime, trlAltitude) VALUES };
    my $rest;

    # blocks of 200 to speed it up
    for ($i = 0; $i < $man; $i++)
    {
        @arr = ();
        for ($j = 0; $j < 500; $j++)
        {
            push @arr, join(',', ( $traPk, $coords->[$off]->{'dlat'}, $coords->[$off]->{'dlong'}, $coords->[$off]->{'time'}, $coords->[$off]->{'altitude'} ));
            $off++;
        }

        $rest = '(' . join('),(', @arr) . ')';
        $affected = $dbh->do($query . $rest);
    }

    # the rest
    if ($rem > 0)
    {
        @arr = ();
        for ($j = 0; $j < $rem; $j++)
        {
            push @arr, join(',', ( $traPk, $coords->[$off]->{'dlat'}, $coords->[$off]->{'dlong'}, $coords->[$off]->{'time'}, $coords->[$off]->{'altitude'} ));
            $off++;
        }

        $rest = '(' . join('),(', @arr) . ')';
        $affected = $dbh->do($query . $rest);
    }

    return $traPk;
}

#
# Read a tracklog from the database 
# Return a dictionary with a coord array
#
sub read_track
{
    my ($traPk) = @_;
    my %track;
    my @coords;
    my %awards;
    my $ref;
    my $c1;
    my $rows;

    $sth = $dbh->prepare("select unix_timestamp(T.traDate) as udate,T.*,CTT.* from tblTrack T left outer join tblComTaskTrack CTT on T.traPk=CTT.traPk where T.traPk=$traPk");
    $sth->execute();

    $track{'traPk'} = $traPk;

    if ($ref = $sth->fetchrow_hashref())
    {
        $track{'traDate'} = $ref->{'traDate'};
        $track{'udate'} = $ref->{'udate'};
        $track{'traStart'} = $ref->{'traStart'};
        $track{'traGlider'} = $ref->{'traGlider'};
        $track{'traDHV'} = $ref->{'traDHV'};
        $track{'pilPk'} = $ref->{'pilPk'};
        $track{'traLength'} = $ref->{'traLength'};
        $track{'traDuration'} = $ref->{'traDuration'};
        if ($ref->{'comPk'} > 0)
        {
            $track{'comPk'} = $ref->{'comPk'};
            $track{'tasPk'} = $ref->{'tasPk'};
        }
    }

    $sth = $dbh->prepare("select trlLatDecimal, trlLongDecimal, trlAltitude, trlTime from tblTrackLog where traPk=$traPk order by trlTime");
    $sth->execute();
    $rows = $sth->fetchall_arrayref();

    for my $ref ( @$rows )
    {
        #print "Found a row: time = $ref->{'trlTime'}\n";
        my %coord;
        %coord = ();

        $coord{'dlat'} = $ref->[0];
        $coord{'dlong'} = $ref->[1];

        # radians
        $coord{'lat'} = $ref->[0] * $pi / 180;
        $coord{'long'} = $ref->[1] * $pi / 180;

        # alt / time  / pressure?
        $coord{'alt'} = $ref->[2];
        $coord{'time'} = $ref->[3];

        # and cartesian ..
        $c1 = polar2cartesian(\%coord);
        $coord{'cart'} = $c1;

        push @coords, \%coord;
    }

    $track{'coords'} = \@coords;

    # Also do awards ..
    $sth = $dbh->prepare("select * from tblTaskAward where traPk=$traPk");
    $sth->execute();
    while  ($ref = $sth->fetchrow_hashref()) 
    {
        $awards{$ref->{'tawPk'}} = $ref;
    }
    $track{'awards'} = \%awards;

    return \%track;
}


#
# Read a task from the database
#
sub read_task
{
    my ($tasPk) = @_;
    my @waypoints;
    my %task;

    if (0+$tasPk < 1)
    {
        print "No valid task for this track ($tasPk)\n";
        exit 1; 
    }
    $sth = $dbh->prepare("select unix_timestamp(T.tasStartTime) as ustime, unix_timestamp(T.tasFinishTime) as uftime,T.*, C.comTimeOffset from tblTask T, tblCompetition C where T.tasPk=$tasPk and T.comPk=C.comPk");
    $sth->execute();
    if  ($ref = $sth->fetchrow_hashref()) 
    {
        $task{'tasPk'} = $tasPk;
        $task{'date'} = $ref->{'tasDate'};
        $task{'region'} = $ref->{'regPk'};
        $task{'start'} = $ref->{'tasStartTime'};
        $task{'gmstart'} = $ref->{'ustime'} - $ref->{'comTimeOffset'} * 3600;
        $task{'sstart'} = (24*3600 + substr($ref->{'tasStartTime'},11,2) * 3600 +
                            substr($ref->{'tasStartTime'},14,2) * 60 +
                            substr($ref->{'tasStartTime'},17,2) - 
                            $ref->{'comTimeOffset'} * 3600) % (24*3600);
        $task{'finish'} = $ref->{'tasFinishTime'};
        $task{'sfinish'} = substr($ref->{'tasFinishTime'},11,2) * 3600 +
                        substr($ref->{'tasFinishTime'},14,2) * 60 +
                        substr($ref->{'tasFinishTime'},17,2) - 
                        $ref->{'comTimeOffset'}*3600;
        if (defined($ref->{'tasStartCloseTime'}))
        {
            $task{'startclose'} = $ref->{'tasStartCloseTime'};
            $task{'sstartclose'} = (24*3600 + substr($ref->{'tasStartCloseTime'},11,2) * 3600 +
                            substr($ref->{'tasStartCloseTime'},14,2) * 60 +
                            substr($ref->{'tasStartCloseTime'},17,2) - 
                            $ref->{'comTimeOffset'} * 3600) % (24*3600);
        }
        else
        {
            $task{'startclose'} = $task{'finish'};
            $task{'sstartclose'} = $task{'sfinish'};
        }
        $task{'gmfinish'} = $ref->{'uftime'} - $ref->{'comTimeOffset'} * 3600;
        if ($task{'sfinish'} < $task{'sstart'})
        {
            $task{'sfinish'} = $task{'sfinish'} + 24*3600;
        }
        if (defined($ref->{'tasStoppedTime'}))
        {
            $task{'stopped'} = $ref->{'tasStoppedTime'};
            $task{'sstopped'} = (24*3600 + substr($ref->{'tasStoppedTime'},11,2) * 3600 +
                            substr($ref->{'tasStoppedTime'},14,2) * 60 +
                            substr($ref->{'tasStoppedTime'},17,2) - 
                            $ref->{'comTimeOffset'} * 3600) % (24*3600);
            if ($task{'sstopped'} < $task{'sstart'})
            {
                $task{'sstopped'} = $task{'sstopped'} + 24*3600;
            }
        }
        $task{'interval'} = $ref->{'tasSSInterval'};
        $task{'type'} = $ref->{'tasTaskType'};
        $task{'distance'} = $ref->{'tasDistance'};
        $task{'short_distance'} = $ref->{'tasShortRouteDistance'};
        $task{'arrival'} = $ref->{'tasArrival'};
        $task{'departure'} = $ref->{'tasDeparture'};
        $task{'launchvalid'} = $ref->{'tasLaunchValid'};
    }

    $sth = $dbh->prepare("select T.*,R.*,S.ssrLatDecimal,S.ssrLongDecimal,S.ssrNumber from tblRegionWaypoint R, tblTaskWaypoint T left outer join tblShortestRoute S on S.tasPk=$tasPk and S.ssrNumber=T.tawNumber where T.tasPk=$tasPk and T.rwpPk=R.rwpPk order by T.tawNumber");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        my %wpt;
        %wpt = ();

        $wpt{'key'} = $ref->{'tawPk'};
        $wpt{'number'} = $ref->{'tawNumber'};
        $wpt{'time'} = $ref->{'tawTime'};
        $wpt{'type'} = $ref->{'tawType'};
        $wpt{'how'} = $ref->{'tawHow'};
        $wpt{'shape'} = $ref->{'tawShape'};
        $wpt{'angle'} = $ref->{'tawAngle'};
        $wpt{'radius'} = $ref->{'tawRadius'};

        # FAI allowable 'error' - should be configurable by Comp?
        #$wpt{'radius'} = $wpt{'radius'} + $wpt{'radius'};

        if ($wpt{'type'} ne 'speed')
        {
            if ($wpt{'how'} eq 'exit')
            {
                # FAI rules say 0.05% which is massive for large cylinders
                # Using 2m instead
                #$wpt{'radius'} = $wpt{'radius'} - $wpt{'radius'} * 0.005;
                $wpt{'radius'} = $wpt{'radius'};
            }
            else
            {
                #$wpt{'radius'} = $wpt{'radius'} + $wpt{'radius'} * 0.005;
                $wpt{'radius'} = $wpt{'radius'};
            }
        }
#
        $wpt{'name'} = $ref->{'rwpName'};
        $wpt{'dlat'} = $ref->{'rwpLatDecimal'};
        $wpt{'dlong'} = $ref->{'rwpLongDecimal'};
        $wpt{'lat'} = $ref->{'rwpLatDecimal'} * $pi / 180;
        $wpt{'long'} = $ref->{'rwpLongDecimal'} * $pi / 180;
        $wpt{'short_dlat'} = 0.0 + $ref->{'ssrLatDecimal'};
        $wpt{'short_dlong'} = 0.0 + $ref->{'ssrLongDecimal'};
        $wpt{'short_lat'} = (0.0 + $ref->{'ssrLatDecimal'}) * $pi / 180;
        $wpt{'short_long'} = (0.0 + $ref->{'ssrLongDecimal'}) * $pi / 180;
        $wpt{'alt'} = $ref->{'rwpAltitude'};

        push @waypoints, \%wpt;
    }

    $task{'waypoints'} = \@waypoints;

    # calculate shortest route distance ..
    #my (%s1, %s2);
    #my $dist;
    #for my $i (0 .. $#waypoints-1)
    #{
    #    $s1{'lat'} = $waypoints[$i]->{'short_lat'};
    #    $s1{'long'} = $waypoints[$i]->{'short_long'};
    #    $s2{'lat'} = $waypoints[$i+1]->{'short_lat'};
    #    $s2{'long'} = $waypoints[$i+1]->{'short_long'};
    #    $dist = $dist + distance(\%s1, \%s2);
    #}
    #print "short_distance=$dist\n";
    #$task{'short_distance'} = $dist;

    return \%task;
}

#
# Read a formula from DB
#
sub read_formula
{
    my ($task) = @_;
    my $mindist = 0;
    my %formula;

    # some sensible defaults 
    $formula{'mindist'} = 5000;
    $formula{'class'} = 'ozgap';
    $formula{'version'} = '2005';
    $formula{'sspenalty'} = 1.0;
    $formula{'nomgoal'} = 20;
    $formula{'mindist'} = 5000;
    $formula{'nomdist'} = 30000;
    $formula{'nomtime'} = 7200;
    $formula{'difframp'} = 'fixed';
    $formula{'diffdist'} = 1500;
    $formula{'diffcalc'} = 'all';
    $formula{'lineardist'} = 0.5;

    $sth = $dbh->prepare("select F.* from tblTask T, tblCompetition C, tblFormula F where T.tasPk=$task and C.comPk=T.comPk and F.forPk=C.forPk");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref()) 
    {
        $formula{'comPk'} = $ref->{'comPk'};
        $formula{'class'} = $ref->{'forClass'};
        $formula{'version'} = $ref->{'forVersion'};
        $formula{'sspenalty'} = $ref->{'forGoalSSpenalty'};
        $formula{'nomgoal'} = $ref->{'forNomGoal'};
        $formula{'mindist'} = $ref->{'forMinDistance'} * 1000;
        $formula{'nomdist'} = $ref->{'forNomDistance'} * 1000;
        $formula{'nomtime'} = $ref->{'forNomTime'} * 60;
        $formula{'lineardist'} = $ref->{'forLinearDist'};
        $formula{'difframp'} = $ref->{'forDiffRamp'};
        $formula{'diffdist'} = $ref->{'forDiffDist'} * 1000;
        $formula{'diffcalc'} = $ref->{'forDiffCalc'};
    }

    # FIX: add failsafe checking?
    if ($formula{'mindist'} <= 0)
    {
        print "WARNING: mindist <= 0, using 5000m instead\n";
        $formula{'mindist'} = 5000;
    }

    # print "Formula: ", $formula{'class'}, " ", $formula{'version'}, " sspenalty=", $formula{'sspenalty'}, " goal=", $formula{'nomgoal'}, " mindist=", $formula{'mindist'}, " nomdist=", $formula{'nomdist'}, " nomtime=", $formula{'nomtime'}, " linear=", $formula{'lineardist'}, " difframp=", $formula{'difframp'}, " diffdist=", $formula{'diffdist'}, " diffcalc=", $formula{'diffcalc'}, "\n";

    return \%formula;
}

sub read_region
{
    my ($regPk) = @_;
    my $centre = 0;
    my %region;
    my @waypoints;

    $sth = $dbh->prepare("select R.* from tblRegion R where R.regPk=$regPk");
    $sth->execute();
    if ($ref = $sth->fetchrow_hashref()) 
    {
        $region{'key'} = $ref->{'regPk'};
        $region{'centre'} = $ref->{'regCentre'};
        $region{'radius'} = $ref->{'regRadius'};
        $region{'desc'} = $ref->{'regDescription'};
    }

    $sth = $dbh->prepare("select RW.* from tblRegionWaypoint RW where RW.regPk=$regPk");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        my %wpt;

        %wpt = ();

        $wpt{'name'} = $ref->{'rwpName'};
        $wpt{'lat'} = $ref->{'rwpLatDecimal'} * $pi / 180;
        $wpt{'long'} = $ref->{'rwpLongDecimal'} * $pi / 180;
        $wpt{'alt'} = $ref->{'rwpAltitude'};
        $wpt{'desc'} = $ref->{'rwpDescription'};
        if ($ref->{'rwpPk'} == $region{'centre'})
        {
            $region{'centre'} = \%wpt;
        }
        push @waypoints, \%wpt;
    }

    $region{'waypoints'} = \@waypoints;

    return \%region;
}

sub store_result
{
    my ($track,$result) = @_;
    my $tasPk;
    my $traPk;
    my $dist;
    my $speed;
    my $start;
    my $goal;
    my $coeff;
    my $ss;
    my $endss;
    my $penalty;
    my $comment;
    my $turnpoints;
    my $stopalt;

    $tasPk = $track->{'tasPk'};
    $traPk = $track->{'traPk'};
    $dist = $result->{'distance'};
    $start = $result->{'start'};
    $goal = $result->{'goal'};
    $coeff = $result->{'coeff'};
    $penalty = 0 + $result->{'penalty'};
    $comment = $result->{'comment'};
    $stopalt = $result->{'stopalt'};
    if (!$goal)
    {
        $goal = 0;
    }
    $ss = $result->{'startSS'};
    $endss = $result->{'endSS'};
    if (!$endss)
    {
        $endss = 0;
    }
    if ($result->{'time'})
    {
        $speed = $dist * 3.6 / $result->{'time'};
    }
    else
    {
        $speed = 0;
    }
    $turnpoints = $result->{'waypoints_made'};

    #print "insert into tblTaskResult (tasPk,traPk,tarDistance,tarSpeed,tarStart,tarGoal,tarSS,tarES,tarTurnpoints) values ($tasPk,$traPk,$dist,$speed,$start,$goal,$ss,$endss,$turnpoints)";
    $dbh->do("delete from tblTaskResult where traPk=? and tasPk=?", undef, $traPk, $tasPk);
    print("insert into tblTaskResult (tasPk,traPk,tarDistance,tarSpeed,tarStart,tarGoal,tarSS,tarES,tarTurnpoints,tarLeadingCoeff,tarPenalty,tarComment) values ($tasPk,$traPk,$dist,$speed,$start,$goal,$ss,$endss,$turnpoints,$coeff,$penalty,'$comment')\n");
    $sth = $dbh->prepare("insert into tblTaskResult (tasPk,traPk,tarDistance,tarSpeed,tarStart,tarGoal,tarSS,tarES,tarTurnpoints,tarLeadingCoeff,tarPenalty,tarComment,tarLastAltitude) values ($tasPk,$traPk,$dist,$speed,$start,$goal,$ss,$endss,$turnpoints,$coeff,$penalty,'$comment',$stopalt)");
    $sth->execute();

    if (defined($result->{'kmtime'}))
    {
        my $count = 0;
        my @arr;
        my $tmarr;

        $dbh->do("delete from tblTrackMarker where traPk=?", undef, $traPk);
        $tmarr = $result->{'kmtime'};
        #print "KMTIME=", Dumper($tmarr);

        for my $ktm (@$tmarr)
        {
            # Build structure for insertion ..
            # traPk, dist(count), ktm
            $ktm = 0+$ktm;
            push @arr, "($traPk, $count, $ktm)";
            $count++;
        }
        $tmarr = join(",", @arr);
        $sth = $dbh->prepare("insert into tblTrackMarker (traPk,tmDistance,tmTime) values " . $tmarr);
        $sth->execute();
    }
    return;
}


#
# Find the normal to the plane created by the two points ..
# Normal n = u X v = 
#       ( (uy*vz - uz*vy), (uz*vx - ux*vz), (ux*vy - uy*vx) ) 
#
sub plane_normal
{
    my ($c1, $c2) = @_;
    my %n;

    # Find the normal to the plane created by the two points ..
    # Normal n = u X v = 
    #       ( (uy*vz - uz*vy), (uz*vx - ux*vz), (ux*vy - uy*vx) ) 

    $n{'x'} = $c1->{'y'}*$c2->{'z'} - $c1->{'z'}*$c2->{'y'}; 
    $n{'y'} = $c1->{'z'}*$c2->{'x'} - $c1->{'x'}*$c2->{'z'}; 
    $n{'z'} = $c1->{'x'}*$c2->{'y'} - $c1->{'y'}*$c2->{'x'}; 

#    print "normal=$n{'x'},$n{'y'},$n{'z'}\n";

    return \%n;
}


#
# simple absolute vector length
#
sub vector_length
{
    my ($v) = @_;

    return sqrt($v->{'x'}*$v->{'x'} + $v->{'y'}*$v->{'y'} 
                        + $v->{'z'}*$v->{'z'});

}

# rounding ..
sub round
{
    my ($number) = @_;
    return int($number + .5);
}



#
# 3d (euclidean) vector dot product
#
sub dot_product
{
    my ($v, $w) = @_;
    my $tl;

    $tl = $v->{'x'} * $w->{'x'} + $v->{'y'} * $w->{'y'} + $v->{'z'} * $w->{'z'};
    $bl = vector_length($v) * vector_length($w);

    if ($bl == 0) 
    {
        return 1.0;
    }

    return $tl/$bl;
}

#
# cartesian vector vector compare
#
sub vvequal
{
    my ($a, $b) = @_;

    if ($a->{'x'} == $b->{'x'} &&
        $a->{'y'} == $b->{'y'} &&
        $a->{'z'} == $b->{'z'})
    {
        return 1;
    }

    return 0;
}

#
# cartesian vector vector minus
#
sub vvminus
{
    my ($a, $b) = @_;
    my %cart;

    $cart{'x'} = $a->{'x'} - $b->{'x'};
    $cart{'y'} = $a->{'y'} - $b->{'y'};
    $cart{'z'} = $a->{'z'} - $b->{'z'};

    return \%cart;
}

sub vvplus
{
    my ($a, $b) = @_;
    my %cart;

    $cart{'x'} = $a->{'x'} + $b->{'x'};
    $cart{'y'} = $a->{'y'} + $b->{'y'};
    $cart{'z'} = $a->{'z'} + $b->{'z'};

    return \%cart;
}

sub cvmult
{
    my ($c, $b) = @_;
    my %cart;

    $cart{'x'} = $c * $b->{'x'};
    $cart{'y'} = $c * $b->{'y'};
    $cart{'z'} = $c * $b->{'z'};

    return \%cart;
}

sub vcdiv
{
    my ($b, $c) = @_;
    my %cart;

    $cart{'x'} = $b->{'x'} / $c;
    $cart{'y'} = $b->{'y'} / $c;
    $cart{'z'} = $b->{'z'} / $c;

    return \%cart;
}

#
# Determine if the next point lies within the current track
#
# Fix: Should really find distance on greater circle rather
#   than directly .. but it's just an approximation so it'll do.
#
# $p1, $p2 - end points of middle line 
# $p3 - new point .. test if it's in range
#
# Probably needs to check all points in existing line to ensure they 
# still fall within it ... (for continuous curves etc).
#
# Finding the normal:
# u = vector from B to A = (A-B)
# v = vector from B to C = (C-B)
# Normal n = u X v = 
#       ( (uy*vz - uz*vy), (uz*vx - ux*vz), (ux*vy - uy*vx) ) 
#
# Distance between a point Pa & a plane (defined by a normal A,B,C & Pb)
#   minimum distance = (A (xa - xb) + B (ya - yb) + C (za - zb)) / 
#                               sqrt(A^2 + B^2 + C^2)
#

sub straight_on
{
    my ($seg, $end, $track_width) = @_;

    my $start;

    my $c1;
    my $c2;
    my $c3;

    my $u;
    my $n;

    my $dist;

    # Get the first point in the line segment
    $start = shift @$seg;
    $c1 = $start->{'centre'}->{'cart'};
    unshift @$seg, $start;

    # Get the new point  ...
    $c2 = $end->{'centre'}->{'cart'};

    # Start & end are the same point?
    if ( (($c2->{'x'}-$c1->{'x'}) == 0) and (($c2->{'y'}-$c1->{'y'}) == 0)) 
    {
        # just add the new one then ....
        #print "straight on - same point\n";
        return -1;
    }


    # Find the normal to the plane (so we can find dist from it)
    $n = plane_normal($c1, $c2);

    # Check if all the points are "on-track"
    foreach my $p3 (@$seg)
    {

        # get cartesian coords of each point and check it's "on" the track
        $c3 = $p3->{'centre'}->{'cart'};

# Distance between a point Pa & a plane (defined by a normal A,B,C & Pb)
#   minimum distance = (A (xa - xb) + B (ya - yb) + C (za - zb)) / 
#                               sqrt(A^2 + B^2 + C^2)

        $dist = ($n->{'x'} * ($c3->{'x'} - $c1->{'x'}) + 
                $n->{'y'} * ($c3->{'y'} - $c1->{'y'}) + 
                $n->{'z'} * ($c3->{'z'} - $c1->{'z'})) / 
                sqrt($n->{'x'}*$n->{'x'} + $n->{'y'}*$n->{'y'} 
                        + $n->{'z'}*$n->{'z'});

#        $u = abs(($c2->{'x'}-$c1->{'x'})*($c1->{'y'}-$c3->{'y'}) 
#            - ($c1->{'x'}-$c3->{'x'})*($c2->{'y'}-$c1->{'y'})) / 
#                sqrt(($c2->{'x'}-$c1->{'x'})^2 + ($c2->{'y'}-$c1->{'y'})^2);
#
#        # Substituting this into the equation of the line gives the point 
#        # of intersection (x,y) of the tangent as
#
#        $x = $c1->{'x'} + $u * ($c2->{'x'} - $c1->{'x'});
#        $y = $c1->{'y'} + $u * ($c2->{'y'} - $c1->{'y'});
#
#        # Now find distance between intersection (x,y) and c3
#        $dist = sqrt(($x - $c3->{'x'})^2 + ($y - $c3->{'y'})^2);

        #print "straight on=$dist\n";

        if (abs($dist) > $track_width)
        {
            return 0;
        }

    }

    # Now check the point is not turning back on track ...
    my $v;
    my $w;
    my $lend;
    my $phi;
    my $phideg;

    # $c1 ok still ..
    # $c2 from end of line ...
    $lend = pop @$seg;
    $c2 = $lend->{'centre'}->{'cart'};
    push @$seg, $lend;
    # $c3 is the ne point ..
    $c3 = $end->{'centre'}->{'cart'};

    $v = plane_normal($c1, $c2);
    $w = plane_normal($c2, $c3);

    $phi = acos(dot_product($v,$w));

    $phideg = $phi * 180 / $pi;

    # turned around it seems .. make new seg..
    #print "phideg=$phideg\n";
    if ($phideg > 60)
    {
        return 0;
    }

    return 1;
}

#
# Distance between a point Pa & a plane (defined by a normal A,B,C & Pb)
# How to get the normal (A,B,C)?
#   minimum distance = (A (xa - xb) + B (ya - yb) + C (za - zb)) / 
#                               sqrt(A^2 + B^2 + C^2)
#


#
# Convert polar coords into cartesian ones ...
#
sub polar2cartesian
{
    my ($p1) = @_;
    
    # WGS84 info ..
    my $a = 6378137.0;
    my $b = 6356752.3142;
    my $f = 1/298.257223563;  

    my %cart;

    my $sinPhi = sin($p1->{'lat'});
    my $cosPhi = cos($p1->{'lat'});
    my $sinLambda = sin($p1->{'long'});
    my $cosLambda = cos($p1->{'long'});
    my $H = 0; # $p1->{'altitude'};
    
    my $eSq = ($a*$a - $b*$b) / ($a*$a);
    my $nu = $a / sqrt(1 - $eSq*$sinPhi*$sinPhi);
    
    $cart{'x'} = ($nu+$H) * $cosPhi * $cosLambda;
    $cart{'y'} = ($nu+$H) * $cosPhi * $sinLambda;
    $cart{'z'} = ((1-$eSq)*$nu + $H) * $sinPhi;

    #print 'cart=', $cart{'x'}, ' ', $cart{'y'}, ' ', $cart{'z'}, " alt=$H\n";
    return \%cart;
}

sub cartesian2polar
{
    my ($c) = @_;
    my %pol;

    # WGS84 info ..
    my $a = 6378137.0;
    my $b = 6356752.3142;
    my $f = 1/298.257223563;  
    my $eSq = ($a*$a - $b*$b) / ($a*$a);

    # FIX: +/- determination?
    $pol{'long'} = atan2($c->{'y'}, $c->{'x'}); 
    $pol{'lat'} = asin(sqrt($c->{'z'} * $c->{'z'} / 
                ((1-$eSq)*$a*(1-$eSq)*$a + $c->{'z'}*$c->{'z'}*$eSq)));

    if ($c->{'z'} < 0)
    {
        $pol{'lat'} = -$pol{'lat'};
    }

    $pol{'dlat'} = $pol{'lat'} * 180 / $pi; 
    $pol{'dlong'} = $pol{'long'} * 180 / $pi;

    return \%pol;
}

#
# Angle (in degrees) between two line segments ...
#
sub angle
{
    my ($s1,$s2) = @_;
    my ($c1,$c2,$c3,$c4);
    my ($v,$w);
    my $phi;
    my $phideg;

    # FIX: get start / end of each seg
    $c1 = $s1->{'centre'}->{'cart'};
    $c2 = $s1->{'centre'}->{'cart'};
    $c3 = $s2->{'centre'}->{'cart'};
    $c4 = $s2->{'centre'}->{'cart'};

    $v = plane_normal($c1, $c2);
    $w = plane_normal($c3, $c4);
    $phi = acos(dot_product($v,$w));
    $phideg = $phi * 180 / $pi;

    return $phideg;
}

# subroutine acos
#
# input: an angle in radians
#
# output: returns the arc cosine of the angle
# description: this is needed because perl does not provide an 
#   arc cosine function

sub acos 
{
    my ($x) = @_;
    my $ret;

    if ($x >= 1)
    {
        return 0;
    }

    $ret = atan2(sqrt(1 - $x**2), $x);
    return $ret;
}

#
# Find distance between 2 coordinates (great circle distance)
#
# The great circle distance (D) between any two points 
#   P and A on the sphere is calculated with the following formula: 
#   cos D = (sin p sin a) + (cos p cos a cos |dl|)
#
# * p and a are the latitudes of P and A
# * |dl| is the absolute value of the difference in longitude between P and A
#
# dist = acos(res) * 111.23km
#
# Other stuff:
# Length of a degree of longitude = cos (latitude) * 111.325 kilometers
# define an accurate value for PI
# $pi = atan2(1,1) * 4;
# perl uses radians:
# $radians = $degrees*($pi/180);
#
# radius of earth ~= 6378 km
#
# but should use wgs84 ellipsoid for earth's surface
#   WGS-84 
#       a = 6 378 137 m (±2 m)      
#       b = 6 356 752.3142 m    
#       f = 1 / 298.257223563
#
#   return &acos(cos($a1)*cos($b1)*cos($a2)*cos($b2) + cos($a1)*sin($b1)*cos($a2)*sin($b2) + sin($a1)*sin($a2)) * $r;
#
#   Where:
#
#    $a1 = lat1 in radians
#    $b1 = lon1 in radians
#    $a2 = lat2 in radians
#    $b2 = lon2 in radians
#    $r = radius of the earth in whatever units you want
#
# using Vincenty inverse formula for ellipsoids
#
#


sub distance
{
    my ($p1, $p2) = @_;

    # WGS-84 ellipsiod definitions
    my $a = 6378137.0;
    my $b = 6356752.3142;
    my $f = 1/298.257223563;  

    my $cosSqAlpha;
    my $sinSigma;
    my $cosSigma;
    my $sinLambda;
    my $sigma;
    my $sinAlpha;
    my $cos2SigmaM;
    my $C;

    my $L = $p2->{'long'} - $p1->{'long'};
    my $U1 = atan((1-$f) * tan($p1->{'lat'}));
    my $U2 = atan((1-$f) * tan($p2->{'lat'}));
    my $sinU1 = sin($U1);
    my $cosU1 = cos($U1);
    my $sinU2 = sin($U2);
    my $cosU2 = cos($U2);
  
    my $lambda = $L, $lambdaP = 2*$pi;
    my $iterLimit = 20;

    #print "U1=$U1 U2=$U2 L=$L\n";

    while (abs($lambda-$lambdaP) > 1e-12 && --$iterLimit>0) 
    {
        $sinLambda = sin($lambda);
        $cosLambda = cos($lambda);
        $sinSigma = sqrt(($cosU2*$sinLambda) * ($cosU2*$sinLambda) + 
                        ($cosU1*$sinU2-$sinU1*$cosU2*$cosLambda) *
                        ($cosU1*$sinU2-$sinU1*$cosU2*$cosLambda));

        # co-incident points
        if ($sinSigma==0) 
        {
            return 0.0;  
        }

        $cosSigma = $sinU1*$sinU2 + $cosU1*$cosU2*$cosLambda;
        $sigma = atan2($sinSigma, $cosSigma);
        $sinAlpha = $cosU1 * $cosU2 * $sinLambda / $sinSigma;
        $cosSqAlpha = 1.0 - $sinAlpha*$sinAlpha;

        $cos2SigmaM = $cosSigma - 2*$sinU1*$sinU2/$cosSqAlpha;
        # at equatorial line -  cosSqAlpha=0 
        if (!defined($cos2SigmaM)) 
        {
            $cos2SigmaM = 0;  
        }
        $C = $f/16*$cosSqAlpha*(4+$f*(4-3*$cosSqAlpha));
        $lambdaP = $lambda;
        $lambda = $L + (1-$C) * $f * $sinAlpha *
            ($sigma + $C*$sinSigma*($cos2SigmaM+$C*$cosSigma*
                (-1+2*$cos2SigmaM*$cos2SigmaM)));
    }

    # formula failed to converge
    if ($iterLimit==0) 
    {
        return undef;  
    }

    my $uSq = $cosSqAlpha * ($a*$a - $b*$b) / ($b*$b);
    my $A = 1.0 + $uSq/16384*(4096+$uSq*(-768+$uSq*(320-175*$uSq)));
    my $B = $uSq/1024 * (256+$uSq*(-128+$uSq*(74-47*$uSq)));
    my $deltaSigma = $B*$sinSigma*
        ($cos2SigmaM+$B/4*($cosSigma* (-1.0+2*$cos2SigmaM*$cos2SigmaM) - 
            $B/6*$cos2SigmaM*(-3+4*$sinSigma*$sinSigma)*
            (-3+4*$cos2SigmaM*$cos2SigmaM)));
    my $s = $b*$A*($sigma-$deltaSigma);
    
    #s = s.toFixed(3); # round to 1mm precision
#    printf "Finding distance (%.3f): (%s,%s) (%s,%s)\n", $s, $p1->{'dlat'}, $p1->{'dlong'}, $p2->{'dlat'}, $p2->{'dlong'};
#    printf "(same) distance (%.3f): (%s,%s) (%s,%s)\n", $s, $p1->{'lat'} * 180 / $pi, $p1->{'long'} * 180 / $pi, $p2->{'lat'} * 180 / $pi, $p2->{'long'} * 180 / $pi;

    return $s;
}

#
# Returns a quick (but not 100% accurate) distance*distance
# (useful for sorting/grouping quickly)
# good for small distances
#
# R = 6,371.009
sub qckdist2
{
    my ($p1, $p2) = @_;
    my ($x, $y, $m);

    $x = ($p2->{'lat'} - $p1->{'lat'});
    $y = ($p2->{'long'} - $p1->{'long'}) * cos(($p1->{'lat'} + $p2->{'lat'})/2);

    $m = 6371009.0 * sqrt($x*$x + $y*$y);
    #print "qckdist2=$m (no sqrt=)",6371009.0*($x*$x+$y*$y), "\n";

    return $m;
}


#
# i in range(len(track))
#   CX = Sum ((y(i) - y(i+1)) (x(i)2 + x(i)x(i+1) + x(i+1)2))/6A 
#   CY = Sum ((x(i+1) - x(i)) (y(i)2 + y(i)y(i+1) + y(i+1)2))/6A) 
# where A is the area of the polygon 
#
sub polygon_centroid
{
    my ($track) = @_;
    my $totarea;
    my $first;
    my $seg;
    my $seg1;
    my $i;
    my $sz;
    my ($cx,$cy);

    $totarea = 0;
    $first = 0;
    $sz = scalar @$track;

    # find area ..
    print "track sz=$sz\n";
    for ($i = 0; $i < $sz; $i++)
    {
        $seg = $track->[$i]->{'cart'};
        $seg1 = $track->[($i+1)%$sz]->{'cart'};

        #print Dumper($seg); print Dumper($seg1);
        $totarea = $totarea + 
            ($seg->{'x'}*$seg1->{'y'} - $seg1->{'x'}*$seg->{'y'})
    }

    # 'closing' segment (maybe 0)
    $seg = $track->[$sz-1]->{'cart'};
    $seg1 = $track->[0]->{'cart'};
    $totarea = $totarea + 
            ($seg->{'x'}*$seg1->{'y'} - $seg1->{'x'}*$seg->{'y'});

    $totarea = abs(0.5 * $totarea);

    # find sum of sides
    $cx = 0;
    $cy = 0;
    for ($i = 0; $i < $sz; $i++)
    {
        $seg = $track->[$i]->{'cart'};
        $seg1 = $track->[($i+1)%$sz]->{'cart'};
        $cx = $cx + ($seg->{'x'} - $seg1->{'x'}) * ($seg->{'x'} * $seg1->{'y'}  - $seg1->{'x'} * $seg->{'y'});
        $cy = $cy + ($seg->{'y'} - $seg1->{'y'}) * ($seg->{'x'} * $seg1->{'y'}  - $seg1->{'x'} * $seg->{'y'});
    }
    $cx = $cx / $totarea;
    $cy = $cy / $totarea;

    # also find max distance for (cx,cy) for a 'radius' from centroid
    return $totarea;
}

#
# The area A of a simple polygon can be computed if the cartesian coordinates 
# (x1, y1), (x2, y2), ..., (xn, yn) of its vertices, listed in order as the area 
# is circulated in counter-clockwise fashion, are known. The formula is
#
#    A = 0.5 * (x1y2 - x2y1 + x2y3 - x3y2 + ... + xny1 - x1yn)
#        = 0.5 * (x1(y2 - yn) + x2(y3 - y1) + x3(y4 - y2) + ... + xn(y1 - yn-1)) 
# 
# Only works for simple polygons (which lines don't cross over)
#
# FIX: need to check it's a simple polygon!
#
sub polygon_area
{
    my ($track) = @_;
    my $totarea;
    my $first;
    my $seg;
    my $seg1;
    my $i;
    my $sz;

    $totarea = 0;
    $first = 0;
    $sz = scalar @$track;

    print "track sz=$sz\n";
    for ($i = 0; $i < $sz; $i++)
    {
        $seg = $track->[$i]->{'entry'}->{'centre'}->{'cart'};
        $seg1 = $track->[($i+1)%$sz]->{'entry'}->{'centre'}->{'cart'};

        #print Dumper($seg); print Dumper($seg1);
        $totarea = $totarea + 
            ($seg->{'x'}*$seg1->{'y'} - $seg1->{'x'}*$seg->{'y'})
    }

    # 'closing' segment (maybe 0)
    $seg = $track->[$sz-1]->{'centre'}->{'cart'};
    $seg1 = $track->[0]->{'centre'}->{'cart'};
    $totarea = $totarea + 
            ($seg->{'x'}*$seg1->{'y'} - $seg1->{'x'}*$seg->{'y'});

    $totarea = abs(0.5 * $totarea);

    return $totarea;
}

# Vector / circle / poly? intersect ...
#
sub vc_intersect
{
    my ($v, $c) = @_;

    return 1;
}

#my (%p, $c, $p1);
#$p{'lat'} = -36.0 * $pi / 180;
#$p{'long'} = 147.0 * $pi / 180;
#print Dumper(\%p);
#$c = polar2cartesian(\%p);
#print Dumper($c);
#$p1 = cartesian2polar($c);
#print Dumper($p1);

1;
