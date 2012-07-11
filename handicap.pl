#!/usr/bin/perl 

#
# Populate handicap scores from competition results
# 
# Geoff Wong 2009
#

require DBD::mysql;

use POSIX qw(ceil floor);
use Math::Trig;
use Data::Dumper;
use TrackLib qw(:all);


#
# Handicap is a 5 year depreciating average
#
sub do_hgfa_handicaps
{
    
    my ($dbh,$comPk) = @_;
    my $sth;
    my %res;

    $dbh->do("insert into tblHandicap (comPk, pilPk, hanTasks, hanHandicap) select ?, PM.pilPk,  count(*) as numTasks, sum((R.resScore/T.tasTopOzScore)*pow(0.8, floor((unix_timestamp(now()) - unix_timestamp(T.tasDate))/31536000)))/sum(pow(0.8, floor((unix_timestamp(now()) - unix_timestamp(T.tasDate))/31536000))) as handicap from hgfa_ladder.tblResult R, hgfa_ladder.tblTask T, hgfa_ladder.tblPilot P, tblPilMap PM, hgfa_ladder.tblCompetition C where PM.ladderPk=P.pilPk and C.comPk=T.comPk and C.sanValue=450 and C.comDateFrom between date_sub(now(),interval 5 year) and now() and P.pilPk=R.pilPk and R.tasPk=T.tasPk group by R.pilPk", undef, $comPk);

#    $sth = $dbh->prepare("select PM.pilPk, PM.ladderPk, count(*) as numTasks, sum((R.resScore/T.tasTopOzScore)*pow(0.8, floor((unix_timestamp(now()) - unix_timestamp(T.tasDate))/31536000)))/sum(pow(0.8, floor((unix_timestamp(now()) - unix_timestamp(T.tasDate))/31536000))) as handicap from hgfa_ladder.tblResult R, hgfa_ladder.tblTask T, hgfa_ladder.tblPilot P, tblPilMap PM, hgfa_ladder.tblCompetition C where PM.ladderPk=P.pilPk and C.comPk=T.comPk and C.sanValue=450 and C.comDateFrom between date_sub(now(),interval 5 year) and now() and P.pilPk=R.pilPk and R.tasPk=T.tasPk group by R.pilPk");
#    $sth->execute();
#    while ($ref = $sth->fetchrow_hashref()) 
#    {
#        $res{$ref->{'pilPk'}} = $ref;
#    }

#    return \%res;
}

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

my $comPk;

$comPk = 0 + $ARGV[0];
print "Calculating handicaps comPk=$comPk\n";

$dbh = db_connect();

$res = do_hgfa_handicaps($dbh,$comPk);
#get_wprs_handicaps($res)
#award_nominal_handicaps($res)

store_handicaps($res,$comPk);

