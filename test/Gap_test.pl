#!/usr/bin/perl -I..

#sub new
#sub round 
#sub spread
#sub task_totals
#sub day_quality
#sub points_weight
#sub calc_kmdiff
#sub points_allocation

require Gap;
use Test::More;
use Data::Dumper;
use strict;

my $gap;

$gap =  new_ok( "Gap" );

# Helper function tests

is($gap->round(1.3), 1.0, "Rounding 1");
is($gap->round(1.5), 2.0, "Rounding 2");
is($gap->round(1.8), 2.0, "Rounding 3");

is($gap->min([ 1.1, 2.3 ]), 1.1, "Min 1");
is($gap->min([ 2.5, 2.7 ]), 2.5, "Min 2");

# Define some actual GAP tests

my $task = {};
my $taskt = {};
my $formula = {};

$task->{'arrival'} = 'on';
$task->{'departure'} = 'on';

$taskt->{'pilots'} = 100.0;
$taskt->{'launched'} = 100.0;
$taskt->{'distance'} = 2000000;
$taskt->{'goal'} = 40.0;
$taskt->{'launchvalid'} = 1;
$taskt->{'tqtime'} = 90 * 60;
$taskt->{'quality'} = 1.0;

$formula->{'version'} = '2015';
$formula->{'mindist'} = 5000;
$formula->{'nomdist'} = 30000;
$formula->{'nomgoal'} = 0.5;
$formula->{'nomtime'} = 90 * 60;
$formula->{'diffcalc'} = 'lo';
$formula->{'weightstart'} = 0.125;
$formula->{'weightarrival'} = 0.175;
$formula->{'weightspeed'} = 0.7;
$formula->{'weightdist'} = 'pre2014';

is($gap->day_quality($taskt, $formula), (1.0, 1.0, 1.0, 1.0), "Day Quality");

# @todo more quality checks here ..

# Pre 2014 distance weight
my @pw = $gap->points_weight($task, $taskt, $formula);
my $sum = 0.0;
for my $i (0..scalar @pw-1)
{
    $sum += $pw[$i];
    $pw[$i] = $gap->round($pw[$i]);
}
is_deeply(\@pw, [ 494, 354, 63, 89 ], "Points Weight");

$sum = $gap->round($sum);
is($sum, $taskt->{'quality'} * 1000, "Total Points Weight");


# Post 2014 distance weight
$formula->{'weightdist'} = 'post2014';
my @pw = $gap->points_weight($task, $taskt, $formula);
my $sum = 0.0;
for my $i (0..scalar @pw-1)
{
    $sum += $pw[$i];
    $pw[$i] = $gap->round($pw[$i]);
}
is_deeply(\@pw, [ 471, 371, 66, 93 ], "Points Weight");

$sum = $gap->round($sum);
is($sum, $taskt->{'quality'} * 1000, "Total Points Weight");

my $pil = {};
$pil->{'timeafter'} = 300;
$pil->{'place'} = 5;
$taskt->{'fastest'} = 90*60;
$pil->{'time'} = $taskt->{'fastest'} + 300;
$taskt->{'ess'} = 10;
$formula->{'arrival'} = 'place';

# Allocated pilot arrival points (place, timed)
my $Parrival = $gap->round($gap->pilot_arrival($formula, $taskt, $pil, 93));
is($Parrival, 38, "Pilot arrival points - place");
$pil->{'place'} = 2;
$Parrival = $gap->round($gap->pilot_arrival($formula, $taskt, $pil, 93));
is($Parrival, 74, "Pilot arrival points - place");

$formula->{'arrival'} = 'timed';
$Parrival = $gap->round($gap->pilot_arrival($formula, $taskt, $pil, 93));
is($Parrival, 82, "Pilot arrival points - timed");
$pil->{'timeafter'} = 1200;
$Parrival = $gap->round($gap->pilot_arrival($formula, $taskt, $pil, 93));
is($Parrival, 56, "Pilot arrival points - timed");

# Allocated pilot departure/leadout points (departure, leadout, kmbonus, off)
$task->{'departure'} = 'leadout';
$taskt->{'mincoeff'} = 2.0;
$pil->{'coeff'} = 3.0;
my $Pdepart = $gap->round($gap->pilot_departure_leadout($formula, $task, $taskt, $pil, 66, 371));
is($Pdepart, 14, "Pilot departure points - leadout");

$task->{'departure'} = 'departure';
$pil->{'startSS'} = 36600;
$taskt->{'firstdepart'} = 36000;
$Pdepart = $gap->round($gap->pilot_departure_leadout($formula, $task, $taskt, $pil, 66, 371));
is($Pdepart, 24, "Pilot departure points (normal)");

done_testing;

