#!/usr/bin/perl 

#
# Populate handicap scores from competition results (distance/speed), AUS tasks 3 years prior
# 
# Geoff Wong 2016
#

require DBD::mysql;

use POSIX qw(ceil floor);
use Math::Trig;
use Data::Dumper;
use TrackLib qw(:all);


# Handicap is a 5 year depreciating average
#
sub do_hgfa_handicaps
{
    
    my ($dbh,$comPk) = @_;
    my $sth;
    my %res;

    $dbh->do("delete from tblHandicap where comPk=$comPk");

    $dbh->do("insert into tblHandicap (comPk, pilPk, hanTasks, hanHandicap) 
        select  ?, TP.pilPk, count(*)/2, round((sum(if (tarES > 0, ((TR.tarES - TR.tarSS - 3600) / (TK.tasFastestTime - 3600)), (TK.tasMaxDistance / TR.tarDistance)))+4)/(count(*)+4),1) as Handicap
from    tblLadderComp LC
        join tblLadder L on L.ladPk=LC.ladPk
        join tblCompetition C on LC.comPk=C.comPk
        join tblTask TK on C.comPk=TK.comPk
        join tblTaskResult TR on TR.tasPk=TK.tasPk
        join tblTrack TT on TT.traPk=TR.traPk
        join tblPilot TP on TP.pilPk=TT.pilPk
WHERE
    LC.lcValue=450 and C.comDateFrom between date_sub(now(),interval 3 year) and now()
    and L.ladNationCode = 'AUS'
    and C.comPk <> ?
    and TR.tarDistance > 5000.0
group by
        TP.pilPk", undef, $comPk, $comPk);
}


# (7200 * TK.tasSSDistance / (TR.tarES - tarSS)) / (7200 * TK.tasSSDistance / TK.tasFastestTime)  


sub store_handicaps
{
    my ($pils,$comPk) = @_;

    for my $pilPk (keys %$pils)
    {
        $dbh->do("insert into tblHandicap (pilPk,comPk,hanHandicap,hanTasks) values (?,?,?,?,?)", undef, $pilPk, $comPk, $pils->{'handicap'}, $pils->{'numTasks'});
    }
}

#
# Get HGFA scores where I have them
# Otherwise get nearby WPRS results and average for non aus pilots
# Else give them a nominal score (0.5?)
#

if ($#ARGV == -1)
{
    print "handicap_speed.pl <comPk>\n";
    exit 1;
}

my $comPk;

$comPk = 0 + $ARGV[0];
print "Calculating handicaps comPk=$comPk\n";

$dbh = db_connect();

$res = do_hgfa_handicaps($dbh,$comPk);
#get_wprs_handicaps($res)
#award_nominal_handicaps($res)

#store_handicaps($res,$comPk);

