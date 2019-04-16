#!/usr/bin/perl -w
#
# "NoGap"
# Pilot score is the distance flown
# 
# Geoff Wong 2013
#

package NoGap;

use Data::Dumper;
require Gap;
@ISA = ( "Gap" );

#require DBD::mysql;
#use POSIX qw(ceil floor);
#use Math::Trig;

# Add currect bin directory to @INC
#use lib '/var/www/cgi-bin';
#use TrackLib qw(:all);

sub day_quality
{
    return (1,1,1,1);
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
    my $comPk;
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

    $comPk = $task->{'comPk'};
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
    #$sth = $dbh->prepare("select \@x:=\@x+1 as Place, tarPk, tarDistance, tarSS, tarES, tarPenalty, tarResultType, tarLeadingCoeff, tarGoal from tblTaskResult where tasPk=$tasPk and tarResultType <> 'abs' order by tarDistance desc, tarES");
    $sth = $dbh->prepare("select \@x:=\@x+1 as Place, TR.tarPk, TR.tarDistance, TR.tarSS, TR.tarES, TR.tarPenalty, TR.tarResultType, TR.tarLeadingCoeff, TR.tarGoal, H.hanHandicap from tblTaskResult TR join tblTrack T on TR.traPk=T.traPk left outer join tblHandicap H on H.pilPk=T.pilPk and H.comPk=$comPk where tasPk=$tasPk and tarResultType <> 'abs' order by tarDistance desc, tarES");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        my %taskres;

        %taskres = ();
        $taskres{'tarPk'} = $ref->{'tarPk'};
        $taskres{'penalty'} = $ref->{'tarPenalty'};
        $taskres{'distance'} = $ref->{'tarDistance'} / 1000;
        # set pilot to min distance if they're below that ..
        $taskres{'result'} = $ref->{'tarResultType'};
        $taskres{'startSS'} = $ref->{'tarSS'};
        $taskres{'endSS'} = $ref->{'tarES'};
        # OZGAP2005 
        $taskres{'timeafter'} = $ref->{'tarES'} - $Tfarr;
        $taskres{'place'} = $ref->{'Place'};
        $taskres{'time'} = $taskres{'endSS'} - $taskres{'startSS'};
        $taskres{'goal'} = $ref->{'tarGoal'};
        $taskres{'handicap'} = 0 + $ref->{'hanHandicap'};
        if ($taskres{'handicap'} == 0)
        {
            $taskres{'handicap'} = 1;
        }
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
        $Pdist = $pil->{'distance'} * $pil->{'handicap'};

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

