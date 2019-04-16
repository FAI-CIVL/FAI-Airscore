#!/usr/bin/perl -w
#
# Determines how much of a task (and time) is completed
# given a particular competition / task 
# 
# Geoff Wong 2007
#

# require Exporter;
# our @ISA       = qw(Exporter);
# our @EXPORT = qw(:all);

require DBD::mysql;
use POSIX qw(ceil floor);
use Math::Trig;
use Data::Dumper;
use strict;

# Add currect bin directory to @INC
use File::Basename;
use lib '/home/ubuntu/perl5/lib/perl5';
use lib dirname (__FILE__) . '/';
use TrackLib qw(:all);

sub round 
{
    my ($self, $number) = @_;
    return int($number + .5);
}

sub min
{
    my ($self, $list) = @_;
    my $x = ~0 >> 1;

    foreach my $y (@$list)
    {
        $x = $y if $y < $x;
    }
    return $x;
}

sub max
{
    my ($self, $list) = @_;
    my $x = 0;

    foreach my $y (@$list)
    {
        $x = $y if $y > $x;
    }
    return $x;
}

sub spread
{
    my ($self, $buc) = @_;
    my $nbuc = [];
    my $sz;

    $sz = scalar @$buc - 1;
    #print "spread: $sz\n";
    $nbuc->[0] = 0.0 + $buc->[0];
    $nbuc->[1] = 0.0 + $buc->[1];
    for my $j ( 1 .. $sz )
    {
        $nbuc->[$j-1] = $nbuc->[$j-1] + $buc->[$j] / 3;
        $nbuc->[$j] = $nbuc->[$j] + $buc->[$j] * 2 / 3;
        #$nbuc->[$j+1] = $buc->[$j] / 3;
    }

    return $nbuc;
}

sub calc_kmdiff
{
    my ($self, $task, $taskt, $formula) = @_;
    my $tasPk;
    my $kmdiff = [];
    my $Nlo;
    my $distspread;
    my $difdist;
    my $debc = 0;

    $tasPk = $task->{'tasPk'};
    $Nlo = $taskt->{'launched'}-$taskt->{'goal'};

    # KM difficulty
    for my $it ( 0 .. floor($taskt->{'maxdist'} / 100.0) )
    {
        $kmdiff->[$it] = 0;
    }

    $distspread = $taskt->{'distspread'};
    for my $ref ( @$distspread )
    {
        # populate kmdiff
        # At half the difficulty dist back they get all the points
        $difdist = 0 + $ref->{'Distance'} - ($formula->{'diffdist'}/200);
        if ($difdist < 0) 
        {
            $difdist = 0;
        }
        $kmdiff->[$difdist] = 0 + $kmdiff->[$difdist] + $ref->{'Difficulty'};
        $debc = $debc + $ref->{'Difficulty'};
        #print "dist($difdist): ", $ref->{'Distance'}, " diff: ", $kmdiff->[$difdist], "\n";
        #$kmdiff->[(0+$ref->{'Distance'})] = 0+$ref->{'Difficulty'};
    }

    # Then smooth it out (non-linearly) for the other half
    #print Dumper($kmdiff);
    for my $it ( 0 .. ($formula->{'diffdist'}/200))
    {
        $kmdiff = $self->spread($kmdiff);
    }
    #print Dumper($kmdiff);

    # Determine cumulative distance difficulty 
    my $x = 0.0;
    for my $dif (0 .. scalar @$kmdiff-1)
    {
        my $rdif;

        $rdif = 0.0;

        $x = $x + $kmdiff->[$dif];
        # Use only landed-out pilots or all pilots for difficulty?
        if ($formula->{'diffcalc'} eq 'lo' && $Nlo > 0)
        {
            $rdif = $x/$Nlo;
        }
        else
        {
            $rdif = $x/$taskt->{'launched'};
        }
        $kmdiff->[$dif] = ($rdif);
    }
    # print "debc=$debc x=$x (vs $Nlo)\n";

    return $kmdiff;
}

sub pilot_distance
{
    my ($self, $formula, $task, $taskt, $pil, $Adistance) = @_;

    my $kmdiff = $self->calc_kmdiff($task, $taskt, $formula);
    my $Pdist = $Adistance * 
            (($pil->{'distance'}/$taskt->{'maxdist'}) * $formula->{'lineardist'}
            + $kmdiff->[floor($pil->{'distance'}/100.0)] * (1-$formula->{'lineardist'}));

    # print $pil->{'tarPk'}, " Adist=$Adistance pil->dist=", $pil->{'distance'}, " maxdist=", $taskt->{'maxdist'}, " kmdiff=", $kmdiff->[floor($pil->{'distance'}/100.0)], "\n";
    print $pil->{'traPk'}, " lin dist: ", $Adistance * ($pil->{'distance'}/$taskt->{'maxdist'}) * $formula->{'lineardist'}, " dif dist: ", $Adistance * $kmdiff->[floor($pil->{'distance'}/100.0)] * (1-$formula->{'lineardist'}), "\n";

    return $Pdist;
}

sub pilot_penalty
{
    my ($self, $formula, $task, $taskt, $pil, $astart, $aspeed) = @_;
    my $penalty = 0;
    my $penspeed;
    my $pendist;

    return $penalty;
}

1;