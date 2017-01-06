#!/usr/bin/perl -I..

use TrackLib qw(:all);
use Test::More;
use Data::Dumper;
use strict;

# Helper function tests

my $pi = atan2(1,1) * 4;

is(round(1.3), 1.0, "Rounding 1");
is(round(1.5), 2.0, "Rounding 2");
is(round(1.8), 2.0, "Rounding 3");

my $p1 = { 'dlat' => -36.0, 'dlong' => 110.0, 
            'lat' => -36.0 * PI() / 180, 'long' => 110.0 * PI() / 180 };

my $c1 = polar2cartesian($p1);
my $p2 = cartesian2polar($c1);

is_deeply($p2, $p1, "polar2cartesian2polar");

my $p2 = { 'lat' => -36.002 * PI() / 180, 'long' => 110.002 * PI() / 180 };

my $accurate_dist = distance($p1, $p2);
is(sprintf("%.3f", $accurate_dist), "285.945", "Accurate Distance");
my $qdist = qckdist2($p1, $p2);
is(sprintf("%.0f", $qdist), "286", "Quick Distance");

my $p3 = { 'lat' => -36.0005 * PI() / 180, 'long' => 110.0008 * PI() / 180 };
my $adist13 = distance($p1, $p3);
my $qdist13 = qckdist2($p1, $p3);
is(sprintf("%.0f",$adist13),sprintf("%.0f",$qdist13),"Short distance comparison");

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



