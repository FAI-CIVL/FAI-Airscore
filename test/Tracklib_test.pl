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

my $gap;

$gap =  new_ok( "Gap" );

# Helper function tests

is(round(1.3), 1.0, "Rounding 1");
is(round(1.5), 2.0, "Rounding 2");
is(round(1.8), 2.0, "Rounding 3");

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



