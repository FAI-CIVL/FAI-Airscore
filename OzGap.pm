#!/usr/bin/perl 


#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2007
#

package OzGap;

require Gap;
@ISA = ( "Gap" );

#require DBD::mysql;
#use POSIX qw(ceil floor);
#use Math::Trig;
#use Data::Dumper;
#use TrackLib qw(:all);

sub points_weight
{
    my ($self, $task, $taskt, $formula) = @_;
    my $Fversion;
    my $quality;
    my $distweight;
    my $Adistance;
    my $Aspeed;
    my $Astart;
    my $Aarrival;
    my $x;
    my $dem;


    $quality = $taskt->{'quality'};

    #print "distweight=$distweight($Ngoal/$Nfly)\n";
    $x = $taskt->{'goal'} / $taskt->{'launched'};
    $distweight = 1-0.8*sqrt($x);
    $Adistance = 1000 * $quality * $distweight;

    $Fversion = $formula->{'version'};
    if ($Fversion eq '2005')
    {
        #
        $Astart = 0;
        $Aspeed = 1000 * $quality * (1-$distweight) * 3/4;
        $Aarrival = 1000 * $quality * (1-$distweight) * 1/4;
    }
    elsif ($Fversion eq '2000')
    {
        #
        $Aspeed = 1000 * $quality * (1-$distweight) * 2/4;
        $Astart = 1000 * $quality * (1-$distweight) * 1/4;
        $Aarrival = 1000 * $quality * (1-$distweight) * 1/4;
    }
    else
    {
        # Allocate some to leadout
        $Aspeed = 1000 * $quality * (1-$distweight) * 4.6/8;
        $Astart = 1000 * $quality * (1-$distweight) * 1.4/8;
        $Aarrival = 1000 * $quality * (1-$distweight) * 2/8;
    }

    print "points_weight (0): ($Fversion) Quality=$quality Adist=$Adistance, Aspeed=$Aspeed, Astart=$Astart, Aarrival=$Aarrival\n";

    # need to rescale if depart / arrival are "off"
    if (($task->{'arrival'} eq 'off') and ($task->{'departure'} eq 'off'))
    {
        $dem = $Adistance + $Aspeed;
        if ($dem > 0)
        {
            $Adistance = 1000 * $quality * ($Adistance / $dem);
            $Aspeed = 1000 * $quality * ($Aspeed / $dem);
        }
        $Astart = 0;
        $Aarrival = 0; 
    }
    elsif ($task->{'arrival'} eq 'off')
    {
        $dem = $Adistance + $Aspeed + $Astart;
        if ($dem > 0)
        {
            $Adistance = 1000 * $quality *($Adistance / $dem);
            $Aspeed = 1000 * $quality * ($Aspeed / $dem);
            $Astart =  1000 * $quality * ($Astart / $dem);
        }
        $Aarrival = 0; 
    }
    elsif ($task->{'departure'} eq 'off')
    {
        $dem = $Adistance + $Aspeed + $Aarrival;
        if ($dem > 0)
        {
            $Adistance = 1000 * $quality * ($Adistance / $dem);
            $Aspeed = 1000 * $quality * ($Aspeed / $dem);
            $Aarrival = 1000 * $quality * ($Aarrival / $dem);
        }
        $Astart = 0;
    }


    print "points_weight (1): ($Fversion) Quality=$quality Adist=$Adistance, Aspeed=$Aspeed, Astart=$Astart, Aarrival=$Aarrival\n";

    return ($Adistance, $Aspeed, $Astart, $Aarrival);

}

1;

