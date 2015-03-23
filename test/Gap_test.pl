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

is($gap->round(1.3), 1.0, "Rounding 1");
is($gap->round(1.5), 2.0, "Rounding 2");
is($gap->round(1.8), 2.0, "Rounding 3");

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

$formula->{'version'} = '2007';
$formula->{'mindist'} = 5000;
$formula->{'nomdist'} = 30000;
$formula->{'nomgoal'} = 0.5;
$formula->{'nomtime'} = 90 * 60;
$formula->{'diffcalc'} = 'lo';

is($gap->day_quality($taskt, $formula), (1.0, 1.0, 1.0), "Day Quality");

my @pw = $gap->points_weight($task, $taskt, $formula);
my $sum = 0.0;
for my $i (0..scalar @pw-1)
{
    $sum += $pw[$i];
    $pw[$i] = $gap->round($pw[$i]);
}
is_deeply(\@pw, [ 494, 354, 89, 63 ], "Points Weight");

$sum = $gap->round($sum);
is($sum, $taskt->{'quality'} * 1000, "Total Points Weight");


done_testing;

