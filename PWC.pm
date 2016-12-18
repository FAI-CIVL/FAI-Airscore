#!/usr/bin/perl -I/home/geoff/bin


#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2007
#

package PWC;

require Gap;
@ISA = ( "Gap" );

#require DBD::mysql;
#use POSIX qw(ceil floor);
#use Math::Trig;
#use Data::Dumper;
#use TrackLib qw(:all);

#
# Points weight
#

sub points_weight
{
    my ($self, $task, $taskt, $formula) = @_;
    my $quality;
    my $distweight;
    my $Adistance;
    my $Aspeed;
    my $Astart;
    my $Aarrival;
    my $x;
    my $dem;
    my $ess = 0;


    $quality = $taskt->{'quality'};

    #print "distweight=$distweight($Ngoal/$Nfly)\n";
    $x = $taskt->{'goal'} / $taskt->{'launched'};
    $distweight = 1-0.8*sqrt($x);

    $Adistance = 1000 * (0.9-1.665*$x+1.713*$x*$x-0.587*$x*$x*$x) * $quality;
    $Astart = 1000 * $quality * (1-$distweight) * 1.4/8;

    my $allpoints = scalar @$waypoints;
    for (my $i = 0; $i < $allpoints; $i++)
    {
        if ($waypoints->[$i]->{'type'} eq 'ess')
        {
            $ess = 1;
        }
    }
    if ($ess)
    {
        $Aarrival = 0;
    }
    else
    {
        $Aarrival = 1000 * $quality * (1-$distweight) * 1/8;
    }
    $Aspeed = 1000 - $Adistance - $Astart - $Aarrival;

}

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
    $x = ($taskt->{'landed'}/ $taskt->{'launched'});
    my $stopv = sqrt( ($taskt->{'maxdist'} - $avgdist) / ($distlaunchtoess - $taskt->{'maxdist'}+1) * sqrt($stddevdist / 5) + $x*$x*$x );
    $stopv = $self->min([1, $stopv]);

    return ($distance,$time,$launch,$stopv);
}

# Fix - need $stddevdest, $distlaunchess, $avgdist

1;

