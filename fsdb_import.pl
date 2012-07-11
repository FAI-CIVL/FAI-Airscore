#!/usr/bin/perl
#
# An attempt to import a .fsdb xml into Airscore
# Unfortunately the fsdb format isn't published so much of this is simply an
# exercise in reverse engineering.
#
# Geoff Wong
#

use XML::Simple;
use Data::Dumper;
use POSIX qw(ceil floor);
use strict;

use LadderDB;


sub conv_time
{
    my ($tm) = @_;
    my $h;
    my $res;

    if (length($tm) == 0)
    {
        return "1970-01-01 00:00:00";
    }

    $h = 0 + int(substr($tm,11,2));
    $h = $h - int(substr($tm,20,2));

    $res =  sprintf("%s %02d%s", substr($tm,0,10), $h, substr($tm,13,6));
    #print "conv_time=$res\n";
    return $res;
}

my $config = XMLin($ARGV[0]);
my ($comp, $pilots, $tasks, $form, $formid, $fparam);
my $comPk;

my %pilmap;
my $dbh;

$dbh = db_connect('hgfa_ladder', 'ladder', 'password');

# Add a competition ..
#'location', 'to' => '2008-09-23', 'utc_offset' => '10', 'from' => '2008-04-16',

$comp = $config->{'FsCompetition'};
$tasks = $comp->{'FsTasks'}->{'FsTask'};    # weird but all tasks are under 'FsTask'
$form = $comp->{'FsScoreFormula'};

# Add FormulaCompetition ..
$fparam = 'xxxx ' . $form->{'min_dist'} . '; ' . $form->{'nom_dist'} . '; ' . 
                   $form->{'nom_goal'} . '; ' . $form->{'nom_time'} . '; 1; ' . $form->{'id'};
$formid = insertup('tblFormulaCompetition', 'forPk', "forParameter='$fparam'",
    {
        'forParameter'     => $fparam,
        'forNomGoal'       => $form->{'nom_goal'} * 100,
        'forMinDistance'   => $form->{'min_dist'},
        'forNomDistance'   => $form->{'nom_dist'},
        'forNomTime'       => $form->{'nom_time'},
    });

#
$comPk = insertup('tblCompetition', 'comPk', "comName='".$comp->{'name'}."'",
    { 
        'comName' => $comp->{'name'},
        'comLocation' => $comp->{'location'},
        'comDateTo' => $comp->{'to'} . ' 23:59:59',
        'comDateFrom' => $comp->{'from'} . ' 00:00:00',
        'comFormulaID' => $formid
    }
    );

print "comPk=$comPk\n";

if (0+$comPk < 1)
{
    print "Bad comPk=$comPk\n";
    exit 1;
}



# compute: comNat, comTopNatScore, comQuality

# Find/update/insert the pilots
$pilots = $comp->{'FsParticipants'}->{'FsParticipant'};

for my $name ( keys %$pilots )
{
    my $pil;
    my $id;
    my $pilPk;
    my $gliPk;
    my $manPk;
    my @arr;
    my @gli;
    my $gliname;
    my $manu;
    my $bday;
    my $pilcl;

    $pil = $pilots->{$name};
    @arr = split(/ /, $name);

    # Do glider insert first ..
    @gli = split(/ /, $pil->{'glider'});
    $manu = $gli[0];
    $manPk = insertup('tblManufacturer', 'manPk', "manName='$manu'",  
        {
            'manName' => $manu
        });

    splice @gli, 0, 1;
    $gliname = join ' ', @gli;
    $gliPk = insertup('tblGlider', 'gliPk', "gliName='$gliname'", 
        { 
            'gliName' => $gliname,
            'gliFAIClass' => 3,
            'manPk' => $manPk
        });

    print "pilot=$name\n";
    $id = $pil->{'fai_license'};
    if ($id eq ''&& (0+$pil->{'id'} > 10000) && (0+$pil->{'id'} < 500000)) 
    {
        $id = $pil->{'id'};
    }

    $bday = $pil->{'birthday'};
    if ($bday ne '')
    {
        $bday = $bday . ' 00:00:00';
    }

    my $oriPk;
    my $nat;
    my ($sth,$ref);

    $pilcl = "pilLastName=" . $dbh->quote($arr[scalar(@arr)-1]) . " and pilFirstName=" . $dbh->quote($arr[0]);
    $sth = $dbh->prepare("select pilIDGlobal from tblPilot where $pilcl");
    $sth->execute();
    $ref = $sth->fetchrow_hashref();
    if (defined($ref))
    {
        $id = $ref->{'pilIDGlobal'};
    }

    if ($id eq '')
    {
        $id = 10000000 + $pil->{'CIVLID'};
    }
    else
    {
        $pilcl = "pilIDGlobal='$id'";     
    }

    # 'nat_code_3166_a3' => convert => oriPk

    $nat = $pil->{'nat_code_3166_a3'};
    $sth = $dbh->prepare("select oriPk from tblNation N, tblOrigin O where O.natPk=N.natPk and N.natCode3='$nat'");
    $sth->execute();
    $ref = $sth->fetchrow_hashref();
    $oriPk = 0 + $ref->{'oriPk'};

    $pilPk = insertup('tblPilot', 'pilPk', $pilcl,
        {
            'pilIDGlobal' => $id,
            'pilLastName' => $arr[scalar(@arr)-1],
            'pilFirstName' => $arr[0],
            'oriPk' => $oriPk,
            'pilSex' => !($pil->{'female'}),
            'gliPk' => $gliPk,
            'pilBirthday' => $bday
        });

    # keep track of them all by id?
    $pilmap{$pil->{'id'}} = $pilPk;
}


if (!defined($comPk) || (0+$comPk < 1))
{
    exit 1;
}

# Delete all existing tasks & results 
$dbh->do("delete from tblTaskTurnpoint where tasPk in (select tasPk from tblTask where comPk=$comPk)");
$dbh->do("delete from tblTask where comPk=$comPk");
$dbh->do("delete from tblResult where comPk=$comPk");



for my $tname ( keys %$tasks )
{
    my $task;
    my $tasPk;
    my $tasDate;
    my $trnPk;
    my $ttpPk;
    my $turnpoints;
    my $count;
    my $results;
    my ($ssopen, $esclose);
    my ($topscore, $topozscore, $topspeed);
    my $score;

    $task = $tasks->{$tname};

    # walk the results for values
    $results = $task->{'FsParticipants'}->{'FsParticipant'};

    for my $r ( keys %$results )
    {
        my $res;

        $res = $results->{$r}->{'FsResult'};

        if ($res->{'points'} > $topscore)
        {
            $topscore = $res->{'points'};
            # FIX: check pilot origin ..
            $topozscore = $topscore;
        }
    }


    # walk the turnpoints for values ..
    $turnpoints = $task->{'FsTaskDefinition'}->{'FsTurnpoint'};
    if (defined($turnpoints->{'id'}))
    {
        # Hacky fix for spastic database internals
        $turnpoints = {
                $turnpoints->{'id'} => $turnpoints
            };
    }
    
    #print Dumper($turnpoints);
    $count = 1;
    for my $tp ( keys %$turnpoints )
    {
        if (defined($turnpoints->{$tp}->{'open'}))
        {
            $tasDate = substr($turnpoints->{$tp}->{'open'},0,10) . ' 00:00:00';
        }

        if ($task->{'ss'} == $count)
        {
            $ssopen = $turnpoints->{$tp}->{'open'};
        }

        if ($task->{'es'} == $count)
        {
            $esclose= $turnpoints->{$tp}->{'close'};
        }

        $count++;
    }

    # add a formula ..
    $score = $task->{'FsTaskScoreParams'};

    #print Dumper($score);

    # add the task
    my $typemap = 
        {
            "OPENDISTANCE" => "FREE",
            "CIRCLE" => "RACE",
            "SPEEDRUN" => "SPEEDRUN"
        };

    $topspeed = 0;
    if ($score->{'best_time'} != 0)
    {
        $topspeed = $score->{'best_dist'} / $score->{'best_time'};
    }

    $tasPk = insertup('tblTask', 'tasPk', undef, 
        { 
            'tasName' => $tname,
            'comPk' => $comPk,
            'tasDate' => $tasDate,
            'tasDistance' => $score->{'task_distance'},
            'tasTaskType' => $typemap->{$task->{'FsTaskDefinition'}->{'goal'}},
            'tasPilotsLaunched' => $score->{'no_of_pilots_flying'},
            'tasPilotsTotal' => $score->{'no_of_pilots_present'},
            'tasPilotsGoal' => $score->{'no_of_pilots_reaching_goal'},
            'tasTopScore' => $topscore,
            'tasTopOzScore' => $topozscore,
            'tasTopSpeed' => $topspeed,
            'tasTopDistance' => $score->{'best_dist'},
            'tasSSOpen' => $ssopen,
            'tasESClose' =>  $esclose,
            'tasTotalDistanceFlown' => $score->{'sum_flown_distance'},
            'tasQuality' => $score->{'day_quality'}
        });

    # insert the turnpoints 
    $count = 1;
    for my $tp ( keys %$turnpoints )
    {
        my @larr;
        my $lat;
        my $lon;
        my $radius;
        my $latd;
        my $lond;

        # open, close, lat, lon, radius '2008-05-11T08:00:00+10:00'
        #'-28 07 05.48'
        @larr = split(/ /, $turnpoints->{$tp}->{'lat'});  
        if (scalar(@larr) > 1)
        {
            $lat = 0.0 + abs($larr[0]) + $larr[1] / 60 + $larr[2] / 3600;
            if ($larr[0] < 0) 
            {
                $lat = -$lat;
            }
            @larr = split(/ /, $turnpoints->{$tp}->{'lon'});  
            $lon = 0.0 + abs($larr[0]) + $larr[1] / 60 + $larr[2] / 3600;
            if ($larr[0] < 0) 
            {
                $lon = -$lon;
            }
        }
        else
        {
            $lat = 0.0 + ($turnpoints->{$tp}->{'lat'});
            $lon = 0.0 + ($turnpoints->{$tp}->{'lon'});
        }
        print "lat=$lat\n";
        print "lon=$lon\n";

        $radius = $turnpoints->{$tp}->{'radius'};

        $latd = 'N';
        if ($lat < 0)
        {
            $latd = 'S';
        }

        $lond = 'E';
        if ($lon < 0)
        {
            $lond = 'W';
        }
        $trnPk = insertup('tblTurnpoint', 'trnPk', "trnPositionLatitudeDecimal=$lat and trnPositionLongitudeDecimal=$lon",
            {
                'trnID' => $tp,
                'trnName' => $tp,
                'trnPositionLatitudeDecimal' => $lat,
                'trnPositionLatitudeDirection' => $latd,
                'trnPositionLatitudeDegree' => floor(abs($lat)),
                'trnPositionLatitudeMinute' => floor(abs($lat-floor($lat))*60),
                'trnPositionLatitudeSecond' => abs($lat-floor($lat))*3600%60,
                'trnPositionLongitudeDecimal' => $lon,
                'trnPositionLongitudeDirection' => $lond,
                'trnPositionLongitudeDegree' => floor(abs($lon)),
                'trnPositionLongitudeMinute' => floor(abs($lon-floor($lon))*60),
                'trnPositionLongitudeSecond' => abs($lat-floor($lat))*3600%60, 
#                'trnPositionAltitude' =>
            });
            
        $ttpPk = insertup('tblTaskTurnpoint', 'ttpPk', undef,
            {
                'tasPk' => $tasPk,
                'trnPk' => $trnPk,
                'ttpNr' => $count,
#                'ttpTimeGateType' =>,
#                'ttpCircle' =>,
            });

        $count++;
    }


    # add the results
    for my $r ( keys %$results )
    {
        my $res;
        my $pilPk;
        my $status;
        my ($ss,$es);

        $pilPk = $pilmap{$r};
        $res = $results->{$r}->{'FsResult'};
        print "RESULT for ($r) comPk=$comPk tasPk=$tasPk pilPk=$pilPk\n";
        print Dumper($res), "\n";
        $status = 'LO';
        #if (0.0 + $res->{'ss_time_dec_hours'} > 0)
        if (int($res->{'time_points'}) > 0)
        {
            # true for oz comps anyway ...
            $status = 'GOAL';
        }
        $ss = conv_time($res->{'started_ss'});
        $es = conv_time($res->{'finished_ss'});

        # fix resSSTime, resESTime, resTime
        insertup('tblResult', 'resPk', undef, { 
            'comPk' => $comPk,
            'pilPk' => $pilPk,
            'tasPk' => $tasPk,
            'resComment' => $res->{'penalty_reason'},
            'resPenaltyType' => $res->{'penalty'},
            'resLeadingCoeff' => $res->{'leading_points'},
            'resDistance' => $res->{'distance'},
            #$res->{'ts'},
            'resStatus' => $status,
            'resScore' => $res->{'points'},
            'resArrivalScore' => $res->{'arrival_points'},
            'resDepartureScore' => $res->{'departure_points'},
            'resDistanceScore' => $res->{'distance_points'},
            'resSpeedScore' => $res->{'time_points'},
            'resSSTime' => $ss,
            'resESTime' => $es,
            'resPlace' => $res->{'finished_ss_rank'},
            #$res->{'ss_time_dec_hours'},
            'resTime' => $res->{'ss_time'},
            'resPenaltyValue' => $res->{'penalty_points'},
            #$res->{'rank'},
            });

    }
}


#print Dumper($config);
