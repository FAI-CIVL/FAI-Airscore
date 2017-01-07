#!/usr/bin/perl -I..

#sub new
#sub round 
#sub spread
#sub task_totals
#sub day_quality
#sub points_weight
#sub calc_kmdiff
#sub points_allocation

use Test::More;
use Data::Dumper;
use strict;
use Tracklib qw(:all);

# Helper function tests

my $pi = atan2(1,1) * 4;

is(round(1.3), 1.0, "Rounding 1");
is(round(1.5), 2.0, "Rounding 2");
is(round(1.8), 2.0, "Rounding 3");

my $p1 = { 'dlat' => -36.0, 'dlong' => 110.0 };
$p1->{'lat'} = -36.0 *  $pi / 180;
$p1->{'long'} = 110.0 * $pi / 180;

my $c1 = polar2cartesian($p1);
my $p2 = cartesian2polar($c1);

is_deeply($p2, $p1, "polar2cartesian2polar");

my $p2 = { 'lat' => -36.0 * $pi / 180, 'long' => 110.0 * $pi / 180 };
my $p3 = { 'lat' => -36.2 * $pi / 180, 'long' => 110.2  * $pi / 180};
my $p4 = { 'lat' => -36.0001 * $pi / 180, 'long' => 110.0001  * $pi / 180};
my $p5 = { 'lat' => -36.001 * $pi / 180, 'long' => 110.001  * $pi / 180};

is(sprintf("%.2f", distance($p2, $p3)), "28580.58", "Distance 1");
is(distance($p3, $p2), distance($p2, $p3), "Distance 2");
is(sprintf("%.2f", distance($p2, $p4)), "14.30", "Distance 3");
is(sprintf("%.0f", qckdist2($p3, $p2)), "28591", "Quick Distance 1");
is(sprintf("%.2f", distance($p2, $p4)), sprintf("%.2f", qckdist2($p2, $p4)), "Quick Distance 2");
is(sprintf("%.0f", distance($p2, $p5)), sprintf("%.0f", qckdist2($p2, $p5)), "Quick Distance 3");

done_testing


#is($gap->min([ 1.1, 2.3 ]), 1.1, "Min 1");
#is_deeply(\@pw, [ 494, 354, 63, 89 ], "Points Weight");

#is_deeply(plane_normal(p1, p2),  [x,y,z], "Plane normal");
#
#is(vector_length(), 1);
#is(vector_length(), 3);
#
#dot_product
#
#vvequal
#
#vvminus
#
#vvplus
#
#cvmult
#
#vcdiv
#
#polar2cartesian
#
#cartesian2polar
#
#ddequal
#
#angle
#
#distanc
#
#qckdist2



