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



