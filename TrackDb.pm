#!/usr/bin/perl -I/home/geoff/bin

#
# Some track/database handling stuff
# And a bunch of big circle geometry stuff
#
# Notes: UTC is 13 seconds later than GPS time (!)
#        metres, kms, kms/h, DDMMYY HHMMSSsss, true north,
#        DDMM.MMMM (NSEW designators), hPascals
#
require Exporter;
require DBD::mysql;

use Time::Local;
use Data::Dumper;
use Defines qw(:all);
#use strict;

our @ISA       = qw(Exporter);
our @EXPORT = qw{:ALL};

my $port = 3306;

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

sub PI
{
    return $pi;
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

    my $sth = $dbh->prepare("select unix_timestamp(T.traDate) as udate,T.*,CTT.* from tblTrack T left outer join tblComTaskTrack CTT on T.traPk=CTT.traPk where T.traPk=$traPk");
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
    my $goalalt = 0;
    my $ref;

    if (0+$tasPk < 1)
    {
        print "No valid task for this track ($tasPk)\n";
        exit 1; 
    }
    my $sth = $dbh->prepare("select unix_timestamp(T.tasStartTime) as ustime, unix_timestamp(T.tasFinishTime) as uftime,T.*, C.comTimeOffset from tblTask T, tblCompetition C where T.tasPk=$tasPk and T.comPk=C.comPk");
    $sth->execute();
    if  ($ref = $sth->fetchrow_hashref()) 
    {
        $task{'tasPk'} = $tasPk;
        $task{'comPk'} = $ref->{'comPk'};
        $task{'date'} = $ref->{'tasDate'};
        $task{'region'} = $ref->{'regPk'};
        $task{'launchopen'} = $ref->{'tasTaskStart'};
        $task{'slaunch'} = (24*3600 + substr($ref->{'tasTaskStart'},11,2) * 3600 +
                            substr($ref->{'TaskStart'},14,2) * 60 +
                            substr($ref->{'TaskStart'},17,2) - 
                            $ref->{'comTimeOffset'} * 3600) % (24*3600);
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
        if ($task{'sstartclose'} < $task{'sstart'})
        {
            $task{'sstartclose'} += 24*3600;
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
            if ($task{'sstopped'} < $task{'slaunch'})
            {
                $task{'sstopped'} = $task{'sstopped'} + 24*3600;
            }
        }
        $task{'interval'} = $ref->{'tasSSInterval'};
        $task{'type'} = $ref->{'tasTaskType'};
        $task{'distance'} = $ref->{'tasDistance'};
        $task{'ssdistance'} = $ref->{'tasSSDistance'};
        $task{'endssdistance'} = $ref->{'tasEndSSDistance'};
        $task{'startssdistance'} = $ref->{'tasStartSSDistance'};
        $task{'short_distance'} = $ref->{'tasShortRouteDistance'};
        $task{'arrival'} = $ref->{'tasArrival'};
        $task{'departure'} = $ref->{'tasDeparture'};
        $task{'launchvalid'} = $ref->{'tasLaunchValid'};
        $task{'heightbonus'} = $ref->{'tasHeightBonus'};

        $task{'laststart'} = $task{'sstart'};
        if (defined($ref->{'tasLastStartTime'}))
        {
            if ($task{'type'} ne 'race')
            {
                $task{'laststart'} = (24*3600 + substr($ref->{'tasLastStartTime'},11,2) * 3600 +
                            substr($ref->{'tasLastStartTime'},14,2) * 60 +
                            substr($ref->{'tasLastStartTime'},17,2) - 
                            $ref->{'comTimeOffset'} * 3600) % (24*3600);
            }
        }

    }

    $sth = $dbh->prepare("select T.*,R.*,S.ssrLatDecimal,S.ssrLongDecimal,S.ssrNumber from tblRegionWaypoint R, tblTaskWaypoint T left outer join tblShortestRoute S on S.tasPk=$tasPk and S.ssrNumber=T.tawNumber where T.tasPk=$tasPk and T.rwpPk=R.rwpPk group by T.tawNumber order by T.tawNumber");
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
        if ($ref->{'tawType'} eq 'goal')
        {
            $goalalt = $wpt{'alt'};
        }

        push @waypoints, \%wpt;
    }
    $task{'goalalt'} = $goalalt;

    $task{'waypoints'} = \@waypoints;

    return \%task;
}

sub read_competition
{
    my ($comPk) = @_;
    my @tasks;
    my %comp;
    my $ref;

    if (0+$comPk < 1)
    {
        print "No valid competition ($comPk)\n";
        exit 1; 
    }
    my $sth = $dbh->prepare("select C.* from tblCompetition C where C.comPk=$comPk");
    $sth->execute();
    if  ($ref = $sth->fetchrow_hashref()) 
    {
        $comp{'comPk'} = $ref->{'comPk'};
        $comp{'name'} = $ref->{'comName'};
        $comp{'location'} = $ref->{'comLocation'};
        $comp{'region'} = $ref->{'regPk'};
        $comp{'datefrom'} = $ref->{'comDateFrom'};
        $comp{'dateto'} = $ref->{'comDateTo'};
        $comp{'meetdirname'} = $ref->{'comMeetDirName'};
        $comp{'contact'} = $ref->{'comContact'};
        $comp{'forPk'} = $ref->{'forPk'};
        $comp{'sanction'} = $ref->{'comSanction'};
        $comp{'type'} = $ref->{'comType'};
        $comp{'code'} = $ref->{'comCode'};
        $comp{'entryrestrict'} = $ref->{'comEntryRestrict'};
        $comp{'timeoffset'} = $ref->{'comTimeOffset'};
        $comp{'overallscore'} = $ref->{'comOverallScore'};
        $comp{'overallparam'} = $ref->{'comOverallParam'};
        $comp{'teamsize'} = $ref->{'comTeamSize'};
        $comp{'teamscoring'} = $ref->{'comTeamScoring'};
        $comp{'teamover'} = $ref->{'comTeamOver'};
        $comp{'class'} = $ref->{'comClass'};
        $comp{'stylesheet'} = $ref->{'comStyleSheet'};
        $comp{'locked'} = $ref->{'comLocked'};
    }

    return \%comp;
}

#
# Read a formula from DB
#
sub read_formula
{
    my ($comPk) = @_;
    my $mindist = 0;
    my %formula;
    my $ref;

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

    my $sth = $dbh->prepare("select F.* from tblCompetition C, tblFormula F where C.comPk=$comPk and F.forPk=C.forPk");
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
        $formula{'distmeasure'} = $ref->{'forDistMeasure'};
        $formula{'olcpoints'} = $ref->{'forOLCPoints'};
        $formula{'olcbase'} = $ref->{'forOLCBase'};
        $formula{'weightstart'} = $ref->{'forWeightStart'};
        $formula{'weightspeed'} = $ref->{'forWeightSpeed'};
        $formula{'weightarrival'} = $ref->{'forWeightArrival'};
        $formula{'weightdist'} = $ref->{'forWeightDist'};
        $formula{'scaletovalidity'} = $ref->{'forScaleToValidity'};
        $formula{'glidebonus'} = $ref->{'forStoppedGlideBonus'};
        $formula{'arrival'} = $ref->{'forArrival'};
        $formula{'stoppedelapsedcalc'} = $ref->{'forStoppedElapsedCalc'};
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
    my $ref;

    my $sth = $dbh->prepare("select R.* from tblRegion R where R.regPk=$regPk");
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
    my $coeff2;
    my $ss;
    my $endss;
    my $penalty;
    my $comment;
    my $turnpoints;
    my $stopalt;
    my $stoptime;

    $tasPk = $track->{'tasPk'};
    $traPk = $track->{'traPk'};
    $dist = $result->{'distance'};
    $start = $result->{'start'};
    $goal = $result->{'goal'};
    $coeff = $result->{'coeff'};
    $coeff2 = 0+$result->{'coeff2'};
    $penalty = 0 + $result->{'penalty'};
    $comment = $result->{'comment'};
    $stopalt = 0 + $result->{'stopalt'};
    $stoptime = 0 + $result->{'stoptime'};
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
    print("insert into tblTaskResult (tasPk,traPk,tarDistance,tarSpeed,tarStart,tarGoal,tarSS,tarES,tarTurnpoints,tarLeadingCoeff,tarLeadingCoeff2,tarPenalty,tarComment,tarLastAltitude,tarLastTime) values ($tasPk,$traPk,$dist,$speed,$start,$goal,$ss,$endss,$turnpoints,$coeff,$coeff2,$penalty,'$comment',$stopalt,$stoptime)\n");
    my $sth = $dbh->prepare("insert into tblTaskResult (tasPk,traPk,tarDistance,tarSpeed,tarStart,tarGoal,tarSS,tarES,tarTurnpoints,tarLeadingCoeff,tarLeadingCoeff2,tarPenalty,tarComment,tarLastAltitude,tarLastTime) values ($tasPk,$traPk,$dist,$speed,$start,$goal,$ss,$endss,$turnpoints,$coeff,$coeff2,$penalty,'$comment',$stopalt,$stoptime)");
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

1;

