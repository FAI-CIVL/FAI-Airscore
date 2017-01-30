#!/usr/bin/perl
#
# Export from Airscore to a FS compatible XML file
# 
# Since FS hasn't bothered to publish a specification for the .fsdb xml format
# This is an exercise in reverse engineering and isn't 100% correct. 
# 
# Geoff Wong 2009
#

use XML::Simple;
use Data::Dumper;
use POSIX qw(ceil floor);
use strict;

use TrackLib;
use LadderDB;

my $pi = atan2(1,1) * 4; 

sub empty
{
    my %h;
    return \%h;
}

sub emarr
{
    my @h;
    return \@h;
}

sub fs_time
{
    my ($dte,$off) = @_;

    if ($dte eq '')
    {
        return $dte;
    }

    $dte =~ s/ /T/;
    if ($off >= 0)
    {
        $dte = $dte . "+" . sprintf("%02d:00", $off);
    }
    else
    {
        $dte = $dte . "-" . sprintf("%02d:00", $off);
    }

    return $dte;
}

sub hms_time
{
    my ($secs) = @_;
    my ($h,$m,$s);

    $h = $secs / 3600;
    $m = ($secs / 60) % 60;
    $s = $secs % 60;

    return sprintf("%02d:%02d:%02d", $h, $m, $s);
}

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


my %dud;
my %fsx;
my $fsdb;
my %formula;
my %pilmap;
my %taskmap;
my @pilots;
my $task;
my @tasks;
my $count = 1;
my ($dbh, $sth, $ref);
my $comPk = 0 + $ARGV[0];
my $utc;
my ($comp, $pilots, $form, $formid, $fparam);

if (0+$comPk < 1)
{
    print "Bad comPk=$comPk\n";
    exit 1;
}

$fsdb = empty();
$fsdb->{'FsCompetition'} = empty();

$fsx{'Fs'} = $fsdb;
$fsx{'Fs'}->{'version'} = "3.4";
$fsx{'Fs'}->{'comment'} = "Supports only a single Fs element in a .fsdb file which must be the root element.";

$dbh = db_connect('%DATABASE%', '%MYSQLUSER%', '%MYSQLPASSWORD%');

$sth = $dbh->prepare("select * from tblCompetition where comPk=$comPk");
$sth->execute();
$ref = $sth->fetchrow_hashref();
if (defined($ref))
{
    $fsdb->{'FsCompetition'}->{'id'} = 0;
    $fsdb->{'FsCompetition'}->{'name'} = $ref->{'comName'};
    $fsdb->{'FsCompetition'}->{'location'} = $ref->{'comLocation'};
    $fsdb->{'FsCompetition'}->{'to'} = substr($ref->{'comDateTo'},0,10);
    $fsdb->{'FsCompetition'}->{'from'} = substr($ref->{'comDateFrom'},0,10);
    $utc = $ref->{'comTimeOffset'};
    $fsdb->{'FsCompetition'}->{'utc_offset'} = $utc;
}

$fsdb->{'FsCompetition'}->{'FsCompetitionNotes'} = empty();
$fsdb->{'FsCompetition'}->{'FsScoreFormula'} = \%formula;

$sth = $dbh->prepare("select * from tblFormula where comPk=$comPk");
$sth->execute();
$ref = $sth->fetchrow_hashref();
if (defined($ref))
{
    $formula{'id'} = 'GAP2007';
    $formula{'use_distance_points'} = '1';
    $formula{'use_time_points'} = '1';
    $formula{'use_departure_points'} = '0';
    $formula{'use_leading_points'} = '1';
    $formula{'nom_time'} = $ref->{'forNomTime'} / 60;
    $formula{'nom_goal'} = $ref->{'forNomGoal'} / 100;
    $formula{'time_points_if_not_in_goal'} = 1 - (0+$ref->{'forGoalSSPenalty'});
    $formula{'jump_the_gun_factor'} = '0';
    $formula{'use_1000_points_for_max_day_quality'} = '1';
    $formula{'time_validity_based_on_pilot_with_speed_rank'} = '1';
}

$fsdb->{'FsCompetition'}->{'FsParticipants'}->{'FsParticipant'} = \@pilots;
$sth = $dbh->prepare("select P.* from tblPilot P, tblTaskResult TR, tblTrack TK, tblTask T where P.pilPk=TK.pilPk and TK.traPk=TR.traPk and TR.tasPk=T.tasPk and T.comPk=$comPk group by P.pilPk");
$sth->execute();
$ref = $sth->fetchrow_hashref();
while (defined($ref))
{
    my $pilot;

    $pilot = empty();
    $pilot->{'FsParticipant'} = empty();
    $pilot->{'FsParticipant'}->{'id'} = $count;
    $pilot->{'FsParticipant'}->{'name'} = $ref->{'pilFirstName'} . ' ' . $ref->{'pilLastName'};
    $pilot->{'FsParticipant'}->{'nat_code_3166_a3'} = $ref->{'pilNationCode'};
    if ($ref->{'pilSex'} eq 'F')
    {
        $pilot->{'FsParticipant'}->{'female'} = 1;
    }
    else
    {
        $pilot->{'FsParticipant'}->{'female'} = 0;
    }
    $pilot->{'FsParticipant'}->{'birthday'} = $ref->{'pilBirthdate'};
    $pilot->{'FsParticipant'}->{'glider'} = '';
    $pilot->{'FsParticipant'}->{'color'} = '';
    $pilot->{'FsParticipant'}->{'sponsor'} = '';
    $pilot->{'FsParticipant'}->{'CIVLID'} = $ref->{'pilHGFA'};
    $pilot->{'FsParticipant'}->{'fai_license'} = $ref->{'pilHGFA'};
    $pilmap{$ref->{'pilPk'}} = $count;
    push @pilots, $pilot;
    $count++;
    $ref = $sth->fetchrow_hashref();
}

$count = 1;
$fsdb->{'FsCompetition'}->{'FsTasks'}->{'FsTask'} = \@tasks;

# Tasks
$sth = $dbh->prepare("select TK.* from tblTask TK where TK.comPk=$comPk order by TK.tasPk");
$sth->execute();
$ref = $sth->fetchrow_hashref();
while (defined($ref))
{
    my @tps;

    $task = empty();
    $task->{'id'} = $count;
    $task->{'name'} = $ref->{'tasName'};
    $task->{'tracklog_folder'} =  '';
    $task->{'FsScoreFormula'} = \%formula;
    #$task->{'FsParticipants'}->{'FsParticipant'} = \@pilots;
    #$task->{'FsTaskScoreParams'} = empty();
    #$task->{'FsTaskScoreParams'}->{'ss_distance'} = ''
    $task->{'FsTaskScoreParams'}->{'task_distance'} = sprintf("%.2f", $ref ->{'tasShortRouteDistance'});
    $task->{'FsTaskScoreParams'}->{'no_of_pilots_present'} = $ref->{'tasPilotsTotal'};
    $task->{'FsTaskScoreParams'}->{'no_of_pilots_flying'} = $ref->{'tasPilotsLaunched'};
    $task->{'FsTaskScoreParams'}->{'no_of_pilots_lo'} = $ref->{'tasPilotsLaunched'} - $ref->{'tasPilotsGoal'};
    $task->{'FsTaskScoreParams'}->{'no_of_pilots_reaching_nom_dist'} = '';
    $task->{'FsTaskScoreParams'}->{'no_of_pilots_reaching_es'} = '';
    $task->{'FsTaskScoreParams'}->{'no_of_pilots_reaching_goal'} = $ref->{'tasPilotsGoal'};
    $task->{'FsTaskScoreParams'}->{'no_of_pilots_in_competition'} = $ref->{'tasPilotsTotal'};
    $task->{'FsTaskScoreParams'}->{'sum_dist_over_min'} = sprintf("%.2f", $ref->{'tasTotalDistanceFlown'});
    $task->{'FsTaskScoreParams'}->{'max_time_to_get_time_points'} = '';
    #$task->{'FsTaskScoreParams'}->{'no_of_pilots_with_time_points'} = '';
    #$task->{'FsTaskScoreParams'}->{'k'} = '';
    #$task->{'FsTaskScoreParams'}->{'arrival_weight'} = '';
    #$task->{'FsTaskScoreParams'}->{'departure_weight'} = '';
    #$task->{'FsTaskScoreParams'}->{'leading_weight'} = '';
    #$task->{'FsTaskScoreParams'}->{'time_weight'} = '';
    #$task->{'FsTaskScoreParams'}->{'distance_weight'} = '';
    #$task->{'FsTaskScoreParams'}->{'smallest_leading_coefficient'} = '';
    #$task->{'FsTaskScoreParams'}->{'available_points_distance'} = '';
    #$task->{'FsTaskScoreParams'}->{'available_points_time'} = '';
    #$task->{'FsTaskScoreParams'}->{'available_points_departure'} = '';
    #$task->{'FsTaskScoreParams'}->{'available_points_leading'} = '';
    #$task->{'FsTaskScoreParams'}->{'available_points_arrival'} = '';
    #$task->{'FsTaskDistToTp'} = '';
    $task->{'FsTaskScoreParams'}->{'time_validity'} = $ref->{'tasTimeQuality'};
    $task->{'FsTaskScoreParams'}->{'launch_validity'} = $ref->{'tasLaunchQuality'}; 
    $task->{'FsTaskScoreParams'}->{'distance_validity'} = $ref->{'tasDistQuality'};
    $task->{'FsTaskScoreParams'}->{'day_quality'} = $ref->{'tasQuality'};
    $taskmap{$ref->{'tasPk'}} = $task;

    $count++;
    push @tasks, $task;
    $ref = $sth->fetchrow_hashref();
}


# Waypoints
my ($ss, $es);
my $tps = emarr();
my $sroute = emarr();
my $turn;
my $cnt = 1;
my $lastPk = 0;
my $p1;
my $p2;
my $disxml;
my $dist = 0;

$es = 0;
$sth = $dbh->prepare("select TK.*, TW.*, R.*, SR.* from tblTask TK, tblTaskWaypoint TW, tblRegionWaypoint R, tblShortestRoute SR where TW.tasPk=TK.tasPk and SR.tawPk=TW.tawPk and R.rwpPk=TW.rwpPk and TK.comPk=$comPk order by TK.tasPk,TW.tawNumber");
$sth->execute();
$ref = $sth->fetchrow_hashref();
while (defined($ref))
{
    if ($lastPk != $ref->{'tasPk'} && $lastPk != 0)
    {
        $task = $taskmap{$lastPk};
        $task->{'FsTaskDefinition'}->{'goal'} = 'CIRCLE';
        $task->{'FsTaskDefinition'}->{'ss'} = $ss;
        $task->{'FsTaskDefinition'}->{'es'} = $es;
        $task->{'FsTaskDefinition'}->{'FsTurnpoint'} = $tps;
        $task->{'FsTaskScoreParams'}->{'FsTaskDistToTp'} = $sroute;
        $tps = emarr();
        $sroute = emarr();
        $cnt = 1;
    }
    $lastPk = $ref->{'tasPk'};
    $turn = empty();
    $turn->{'id'} = $ref->{'rwpName'};
    $turn->{'lat'} = sprintf("%.5f", $ref->{'rwpLatDecimal'});
    $turn->{'lon'} = sprintf("%.5f", $ref->{'rwpLongDecimal'});
    $turn->{'radius'} = $ref->{'tawRadius'};
    $turn->{'open'} = '';
    $turn->{'close'} = '';
    if ($ref->{'tawType'} eq 'start')
    {
        $ss = $cnt;
    }
    if ($ref->{'tawType'} eq 'start')
    {
        $ss = $cnt;
    }
    if ($ref->{'tawType'} eq 'endspeed')
    {
        $es = $cnt;
    }
    if ($es == 0)
    {
        if ($ref->{'tawType'} eq 'goal')
        {
            $es = $cnt;
        }
    }
    push @$tps, $turn;

    if (defined($p1))
    {
        $p2->{'lat'} = $p1->{'lat'};
        $p2->{'long'} = $p1->{'long'};
    }
    $p1->{'lat'} = (0.0 + $ref->{'ssrLatDecimal'}) * $pi / 180;
    $p1->{'long'} = (0.0 + $ref->{'ssrLongDecimal'}) * $pi / 180;
    if (defined($p2))
    {
        $dist += (distance($p1, $p2) / 1000);
    }
    $disxml = empty();
    $disxml->{'tp_no'} = $cnt;
    $disxml->{'distance'} = $dist;
    push @$sroute, $disxml;

    $cnt++;
    $ref = $sth->fetchrow_hashref();
}
$task = $taskmap{$lastPk};
$task->{'FsTaskDefinition'}->{'goal'} = 'CIRCLE';
$task->{'FsTaskDefinition'}->{'ss'} = $ss;
$task->{'FsTaskDefinition'}->{'es'} = $es;
$task->{'FsTaskDefinition'}->{'FsTurnpoint'} = $tps;
$task->{'FsTaskScoreParams'}->{'FsTaskDistToTp'} = $sroute;

# Add start gates <FsStartGate open="">

# Results
my $taskr = empty();
my $rarr = emarr();
my $lastPk = 0;

$sth = $dbh->prepare("select TK.*, TR.*, TL.pilPk, TL.traStart, date_add(TK.tasDate, INTERVAL TR.tarSS SECOND) as Sss, date_add(TK.tasDate, INTERVAL TR.tarES SECOND) as Ess from tblTaskResult TR, tblTask TK, tblTrack TL  where TR.tasPk=TK.tasPk and TL.traPk=TR.traPk and TK.comPk=$comPk order by TK.tasPk");
$sth->execute();
$ref = $sth->fetchrow_hashref();
while (defined($ref))
{
    if (($lastPk != $ref->{'tasPk'}) && ($lastPk != 0))
    {
        # insert into tasks
        $task = $taskmap{$lastPk};
        $task->{'FsParticipants'}->{'FsParticipant'} = $rarr;
        $taskr = empty();
        $rarr = emarr();
    }
    $lastPk = $ref->{'tasPk'};
    $taskr = empty();
    $taskr->{'id'} = $pilmap{$ref->{'pilPk'}};
    $taskr->{'FsFlightData'} = empty();
    $taskr->{'FsFlightData'}->{'distance'} = sprintf("%.3f", $ref->{'tarDistance'} / 1000);
    $taskr->{'FsFlightData'}->{'started_ss'} = fs_time($ref->{'Sss'}, $utc);
    $taskr->{'FsFlightData'}->{'finished_ss'} = fs_time($ref->{'Ess'}, $utc);
    if ($ref->{'tarES'} > 0)
    {
        $taskr->{'FsFlightData'}->{'ss_time'} = hms_time($ref->{'tarES'} - $ref->{'tarSS'});
    }
    else
    {
        $taskr->{'FsFlightData'}->{'ss_time'} = '';
    }
    $taskr->{'FsFlightData'}->{'finished_task'} = $ref->{'tarGoal'};
    $taskr->{'FsFlightData'}->{'tracklog_filename'} = '';
    $taskr->{'FsFlightData'}->{'lc'} = sprintf("%.1f", $ref->{'tarLeadingCoeff'});
    $taskr->{'FsFlightData'}->{'iv'} = 0;
    $taskr->{'FsFlightData'}->{'ts'} = fs_time($ref->{'traStart'}, 0);
    $taskr->{'FsResult'} = empty();
    $taskr->{'FsResult'}->{'rank'} = $ref->{'tarPlace'};
    $taskr->{'FsResult'}->{'finished_ss_rank'} = $ref->{'tarPlace'};
    $taskr->{'FsResult'}->{'points'} = sprintf("%.0f", $ref->{'tarScore'});
    $taskr->{'FsResult'}->{'distance_points'} = sprintf("%.1f", $ref->{'tarDistanceScore'});
    $taskr->{'FsResult'}->{'time_points'} = sprintf("%.1f", $ref->{'tarSpeedScore'});
    $taskr->{'FsResult'}->{'arrival_points'} = sprintf("%.1f", $ref->{'tarArrival'});
    $taskr->{'FsResult'}->{'departure_points'} = 0;
    $taskr->{'FsResult'}->{'leading_points'} = sprintf("%.1f", $ref->{'tarDeparture'});;
    $taskr->{'FsResult'}->{'penalty'} = 0;
    $taskr->{'FsResult'}->{'penalty_points'} = $ref->{'tarPenalty'};
    $taskr->{'FsResult'}->{'penalty_reason'} = '';
    $taskr->{'FsResult'}->{'ss_time_dec_hours'} = '';
    $taskr->{'FsResult'}->{'ts'} = '';
    
    # push on tasks results
    push @$rarr, $taskr;

    $ref = $sth->fetchrow_hashref();
}
$task = $taskmap{$lastPk};
$task->{'FsParticipants'}->{'FsParticipant'} = $rarr;


#print Dumper(\%fsx);
#
#header("Content-type: text/fsdb");
#header("Content-Disposition: attachment; filename=\"" . $fsdb->{'FsCompetition'}->{'name'} . ".fsdb\"");
#header("Cache-Control: no-store, no-cache");

my $xml = XMLout(\%fsx,  XMLDecl => 1, KeyAttr=> [ 'id' ]);
print $xml;

