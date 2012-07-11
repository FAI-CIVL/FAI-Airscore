#!/usr/bin/perl
#
# Export from Airscore to a FS compatible XML file
# 
# Geoff Wong 2009
#

use XML::Simple;
use Data::Dumper;
use POSIX qw(ceil floor);
use strict;

use LadderDB;


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

$dbh = db_connect('xcdb', 'xc', 'x323c');

# <?xml version="1.0" encoding="utf-8"?>
#<Fs version="3.4" comment="Supports only a single Fs element in a .fsdb file which must be the root element.">
#<FsCompetition id="0" name="Canungra Cup 2008" location="Canungra, Australia" from="2008-10-11" to="2008-10-18" utc_offset="10">
#<FsCompetitionNotes><![CDATA[]]></FsCompetitionNotes>
#<FsScoreFormula id="GAP2007" use_distance_points="1" use_time_points="1" use_departure_points="0" use_leading_points="1" use_arrival_position_points="0" use_arrival_time_points="1" min_dist="5" nom_dist="35" nom_time="1.5" nom_goal="0.2" time_points_if_not_in_goal="0.8" jump_the_gun_factor="0" use_1000_points_for_max_day_quality="0" time_validity_based_on_pilot_with_speed_rank="1" />
# etc

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
    $fsdb->{'FsCompetition'}->{'utc_offset'} = $ref->{'comTimeOffset'};
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
    $pilot->{'FsParticipant'}->{'birthday'} = $ref->{'Birthdate'};
    $pilot->{'FsParticipant'}->{'glider'} = '';
    $pilot->{'FsParticipant'}->{'color'} = '';
    $pilot->{'FsParticipant'}->{'sponsor'} = '';
    $pilot->{'FsParticipant'}->{'CIVLID'} = '';
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
    $task->{'FsTaskDefinition'}->{'goal'} = 'CIRCLE';
    $task->{'FsTaskDefinition'}->{'ss'} = '0';
    $task->{'FsTaskDefinition'}->{'es'} = '0';
    # $task->{'FsTaskDefinition'}->{'es'} = \@tps;
    # FSParicipants -> [FSParticipant -> FsResult]*
    #$task->{'FsParticipants'}->{'FsParticipant'} = \@pilots;
    $taskmap{$ref->{'tasPk'}} = $task;

    $count++;
    push @tasks, $task;
    $ref = $sth->fetchrow_hashref();
}


# Waypoints
my ($ss, $es);
my $tps = emarr();
my $turn;
my $lastPk = 0;
$sth = $dbh->prepare("select TK.*, TW.*, R.* from tblTask TK, tblTaskWaypoint TW, tblRegionWaypoint R where TW.tasPk=TK.tasPk and R.rwpPk=TW.rwpPk and TK.comPk=$comPk order by TK.tasPk,TW.tawNumber");
$sth->execute();
$ref = $sth->fetchrow_hashref();
while (defined($ref))
{
    if ($lastPk != $ref->{'tasPk'} && $lastPk != 0)
    {
        $task = $taskmap{$lastPk};
        $task->{'FsTurnpoint'} = $tps;
    }
    $lastPk = $ref->{'tasPk'};
    $turn = empty();
    $turn->{'id'} = $ref->{'rwpName'};
    $turn->{'lat'} = sprintf("%.3f", $ref->{'rwpLatDecimal'});
    $turn->{'lon'} = sprintf("%.3f", $ref->{'rwpLongDecimal'});
    $turn->{'radius'} = $ref->{'tawRadius'};
    $turn->{'open'} = '';
    $turn->{'close'} = '';
    $ref = $sth->fetchrow_hashref();
    push @$tps, $turn;
}
# Add start gates <FsStartGate open="">

# Results
my $taskr = empty();
my $rarr = emarr();
my $lastPk = 0;

$sth = $dbh->prepare("select TK.*, TR.*, TL.pilPk from tblTaskResult TR, tblTask TK, tblTrack TL  where TR.tasPk=TK.tasPk and TL.traPk=TR.traPk and TK.comPk=$comPk order by TK.tasPk");
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
    $taskr->{'FsFlightData'}->{'started_ss'} = $ref->{'tarSS'};
    $taskr->{'FsFlightData'}->{'finished_ss'} = $ref->{'tarES'};
    $taskr->{'FsFlightData'}->{'finished_task'} = $ref->{'tarGoal'};
    $taskr->{'FsFlightData'}->{'tracklog_filename'} = '';
    $taskr->{'FsFlightData'}->{'lc'} = sprintf("%.1f", $ref->{'tarLeadingCoeff'});
    $taskr->{'FsFlightData'}->{'iv'} = 0;
    $taskr->{'FsFlightData'}->{'ts'} = 0;
    $taskr->{'FsResult'} = empty();
    $taskr->{'FsResult'}->{'rank'} = $ref->{'tarPlace'};
    $taskr->{'FsResult'}->{'finished_ss_rank'} = '';
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

my $xml = XMLout(\%fsx,  XMLDecl => 1);
print $xml;
