#!/usr/bin/perl -w
#
# Some track/database handling stuff
# And a bunch of big circle geometry stuff
#
# Notes: UTC is 13 seconds later than GPS time (!)
#        metres, kms, kms/h, DDMMYY HHMMSSsss, true north,
#        DDMM.MMMM (NSEW designators), hPascals
#

require Exporter;

# Add currect bin directory to @INC
use File::Basename;
use lib dirname (__FILE__) . '/';
require Vector;
require TrackDb;

use Math::Trig;
use Time::Local;
use Data::Dumper;
use Defines qw(:all);
use strict;
use GIS::Distance;
use GIS::Distance::Fast::ALT;

our @ISA       = qw(Exporter);
our @EXPORT = qw{:ALL};

*VERSION=\'0.99';

our $pi = atan2(1,1) * 4;    # accurate PI.

local * FD;

#
# Find the normal to the plane created by the two points ..
# Normal n = u X v = 
#       ( (uy*vz - uz*vy), (uz*vx - ux*vz), (ux*vy - uy*vx) ) 
#
sub plane_normal
{
    my ($c1, $c2) = @_;

    # Find the normal to the plane created by the two points ..
    # Normal n = u X v = 
    #       ( (uy*vz - uz*vy), (uz*vx - ux*vz), (ux*vy - uy*vx) ) 

    my $n = Vector->new(
        $c1->{'y'}*$c2->{'z'} - $c1->{'z'}*$c2->{'y'},
        $c1->{'z'}*$c2->{'x'} - $c1->{'x'}*$c2->{'z'}, 
        $c1->{'x'}*$c2->{'y'} - $c1->{'y'}*$c2->{'x'});

#    print "normal=$n{'x'},$n{'y'},$n{'z'}\n";

    return $n;
}

# rounding ..
sub round
{
    my ($number) = @_;
    return int($number + .5);
}

#
# Determine if the next point lies within the current track
#
# Fix: Should really find distance on greater circle rather
#   than directly .. but it's just an approximation so it'll do.
#
# $p1, $p2 - end points of middle line 
# $p3 - new point .. test if it's in range
#
# Probably needs to check all points in existing line to ensure they 
# still fall within it ... (for continuous curves etc).
#
# Finding the normal:
# u = vector from B to A = (A-B)
# v = vector from B to C = (C-B)
# Normal n = u X v = 
#       ( (uy*vz - uz*vy), (uz*vx - ux*vz), (ux*vy - uy*vx) ) 
#
# Distance between a point Pa & a plane (defined by a normal A,B,C & Pb)
#   minimum distance = (A (xa - xb) + B (ya - yb) + C (za - zb)) / 
#                               sqrt(A^2 + B^2 + C^2)
#

sub straight_on
{
    my ($seg, $end, $track_width) = @_;

    my $start;

    my $c1;
    my $c2;
    my $c3;

    my $u;
    my $n;

    my $dist;

    # Get the first point in the line segment
    $start = shift @$seg;
    $c1 = $start->{'centre'}->{'cart'};
    unshift @$seg, $start;

    # Get the new point  ...
    $c2 = $end->{'centre'}->{'cart'};

    # Start & end are the same point?
    if ( (($c2->{'x'}-$c1->{'x'}) == 0) and (($c2->{'y'}-$c1->{'y'}) == 0)) 
    {
        # just add the new one then ....
        #print "straight on - same point\n";
        return -1;
    }


    # Find the normal to the plane (so we can find dist from it)
    $n = plane_normal($c1, $c2);

    # Check if all the points are "on-track"
    foreach my $p3 (@$seg)
    {

        # get cartesian coords of each point and check it's "on" the track
        $c3 = $p3->{'centre'}->{'cart'};

# Distance between a point Pa & a plane (defined by a normal A,B,C & Pb)
#   minimum distance = (A (xa - xb) + B (ya - yb) + C (za - zb)) / 
#                               sqrt(A^2 + B^2 + C^2)

        $dist = ($n->{'x'} * ($c3->{'x'} - $c1->{'x'}) + 
                $n->{'y'} * ($c3->{'y'} - $c1->{'y'}) + 
                $n->{'z'} * ($c3->{'z'} - $c1->{'z'})) / 
                sqrt($n->{'x'}*$n->{'x'} + $n->{'y'}*$n->{'y'} 
                        + $n->{'z'}*$n->{'z'});

#        $u = abs(($c2->{'x'}-$c1->{'x'})*($c1->{'y'}-$c3->{'y'}) 
#            - ($c1->{'x'}-$c3->{'x'})*($c2->{'y'}-$c1->{'y'})) / 
#                sqrt(($c2->{'x'}-$c1->{'x'})^2 + ($c2->{'y'}-$c1->{'y'})^2);
#
#        # Substituting this into the equation of the line gives the point 
#        # of intersection (x,y) of the tangent as
#
#        $x = $c1->{'x'} + $u * ($c2->{'x'} - $c1->{'x'});
#        $y = $c1->{'y'} + $u * ($c2->{'y'} - $c1->{'y'});
#
#        # Now find distance between intersection (x,y) and c3
#        $dist = sqrt(($x - $c3->{'x'})^2 + ($y - $c3->{'y'})^2);

        #print "straight on=$dist\n";

        if (abs($dist) > $track_width)
        {
            return 0;
        }

    }

    # Now check the point is not turning back on track ...
    # $c1 ok still ..
    # $c2 from end of line ...
    my $lend = pop @$seg;
    $c2 = $lend->{'centre'}->{'cart'};
    push @$seg, $lend;
    # $c3 is the ne point ..
    $c3 = $end->{'centre'}->{'cart'};

    my $v = plane_normal($c1, $c2);
    my $w = plane_normal($c2, $c3);

    my $phi = acos2($v .$w);
    my $phideg = $phi * 180 / $pi;

    # turned around it seems .. make new seg..
    #print "phideg=$phideg\n";
    if ($phideg > 60)
    {
        return 0;
    }

    return 1;
}

#
# Distance between a point Pa & a plane (defined by a normal A,B,C & Pb)
# How to get the normal (A,B,C)?
#   minimum distance = (A (xa - xb) + B (ya - yb) + C (za - zb)) / 
#                               sqrt(A^2 + B^2 + C^2)
#


#
# Convert polar coords into cartesian ones ...
#
sub polar2cartesian
{
    my ($p1) = @_;
    
    # WGS84 info ..
    my $a = 6378137.0;
    my $b = 6356752.3142;
    my $f = 1/298.257223563;  

    my %cart;

    my $sinPhi = sin($p1->{'lat'});
    my $cosPhi = cos($p1->{'lat'});
    my $sinLambda = sin($p1->{'long'});
    my $cosLambda = cos($p1->{'long'});
    my $H = 0; # $p1->{'altitude'};
    
    my $eSq = ($a*$a - $b*$b) / ($a*$a);
    my $nu = $a / sqrt(1 - $eSq*$sinPhi*$sinPhi);
    
    my $cart = Vector->new(
        ($nu+$H) * $cosPhi * $cosLambda,
        ($nu+$H) * $cosPhi * $sinLambda,
        ((1-$eSq)*$nu + $H) * $sinPhi);

    #print 'cart=', $cart{'x'}, ' ', $cart{'y'}, ' ', $cart{'z'}, " alt=$H\n";
    return $cart;
}

sub cartesian2polar
{
    my ($c) = @_;
    my %pol;

    # WGS84 info ..
    my $a = 6378137.0;
    my $b = 6356752.3142;
    my $f = 1/298.257223563;  
    my $eSq = ($a*$a - $b*$b) / ($a*$a);

    # FIX: +/- determination?
    $pol{'long'} = atan2($c->{'y'}, $c->{'x'}); 
    $pol{'lat'} = asin(sqrt($c->{'z'} * $c->{'z'} / 
                ((1-$eSq)*$a*(1-$eSq)*$a + $c->{'z'}*$c->{'z'}*$eSq)));

    if ($c->{'z'} < 0)
    {
        $pol{'lat'} = -$pol{'lat'};
    }

    $pol{'dlat'} = $pol{'lat'} * 180 / $pi; 
    $pol{'dlong'} = $pol{'long'} * 180 / $pi;

    return \%pol;
}

sub ddequal
{
    my ($wp1, $wp2) = @_;

    if ($wp1->{'dlat'} == $wp2->{'dlat'} &&
        $wp1->{'dlong'} == $wp2->{'dlong'})
    {  
        return 1;
    }

    return 0;
}

#
# Angle (in degrees) between two line segments ...
#
sub angle
{
    my ($s1,$s2) = @_;
    my ($c1,$c2,$c3,$c4);
    my $phi;
    my $phideg;

    # FIX: get start / end of each seg
    $c1 = $s1->{'centre'}->{'cart'};
    $c2 = $s1->{'centre'}->{'cart'};
    $c3 = $s2->{'centre'}->{'cart'};
    $c4 = $s2->{'centre'}->{'cart'};

    my $v = plane_normal($c1, $c2);
    my $w = plane_normal($c3, $c4);
    $phi = acos2($v . $w);
    $phideg = $phi * 180 / $pi;

    return $phideg;
}

# subroutine acos2
#
# input: an angle in radians
#
# output: returns the arc cosine of the angle
# description: this is needed because perl does not provide an 
#   arc cosine function

sub acos2 
{
    my ($x) = @_;
    my $ret;

    if ($x >= 1 or $x <= -1)
    {
        return 0;
    }

    $ret = atan2(sqrt(1 - $x**2), $x);
    return $ret;
}

#
# Find distance between 2 coordinates (great circle distance)
#
# The great circle distance (D) between any two points 
#   P and A on the sphere is calculated with the following formula: 
#   cos D = (sin p sin a) + (cos p cos a cos |dl|)
#
# * p and a are the latitudes of P and A
# * |dl| is the absolute value of the difference in longitude between P and A
#
# dist = acos2(res) * 111.23km
#
# Other stuff:
# Length of a degree of longitude = cos (latitude) * 111.325 kilometers
# define an accurate value for PI
# $pi = atan2(1,1) * 4;
# perl uses radians:
# $radians = $degrees*($pi/180);
#
# radius of earth ~= 6378 km
#
# but should use wgs84 ellipsoid for earth's surface
#   WGS-84 
#       a = 6 378 137 m (±2 m)      
#       b = 6 356 752.3142 m    
#       f = 1 / 298.257223563
#
#   return &acos2(cos($a1)*cos($b1)*cos($a2)*cos($b2) + cos($a1)*sin($b1)*cos($a2)*sin($b2) + sin($a1)*sin($a2)) * $r;
#
#   Where:
#
#    $a1 = lat1 in radians
#    $b1 = lon1 in radians
#    $a2 = lat2 in radians
#    $b2 = lon2 in radians
#    $r = radius of the earth in whatever units you want
#


# using Andoyer-Lambert-Thomas (ALT) formula for ellipsoids
#
#

sub distance
{
    my ($p1, $p2) = @_;
    my $dist = 0;
    my ($d1, $d2);
    
    # Getting Cartesian Coords from Rad
    $d1->{'lat'} = rad2deg($p1->{'lat'});
    $d1->{'long'} = rad2deg($p1->{'long'});
    $d2->{'lat'} = rad2deg($p2->{'lat'});
    $d2->{'long'} = rad2deg($p2->{'long'});
    $dist = WGS84Distance($d1->{'lat'}, $d1->{'long'}, $d2->{'lat'}, $d2->{'long'});
    return $dist;
}

# Distance between two points over a WGS84 Ellipsoid
sub WGS84Distance
{
    my ($lat1, $lon1, $lat2, $lon2) = @_;
#    my $gis = GIS::Distance->new();
#   $gis->formula( 'GeoEllipsoid', { ellipsoid => 'WGS84' } );  # Optional, default is Haversine.
#    $gis->formula( 'GeoEllipsoid' );  # Optional, using WGS84. default is Haversine.

    my $gis = GIS::Distance->new( 'ALT' );
    
    my $wgsdist = $gis->distance( $lat1, $lon1, $lat2, $lon2 );
    return $wgsdist->meters();
}

#
# Returns a quick (but not 100% accurate) distance*distance
# (useful for sorting/grouping quickly)
# good for small distances
#
# R = 6,371.009
sub qckdist2
{
    my ($p1, $p2) = @_;
    my ($x, $y, $m);

    $x = ($p2->{'lat'} - $p1->{'lat'});
    $y = ($p2->{'long'} - $p1->{'long'}) * cos(($p1->{'lat'} + $p2->{'lat'})/2);

    $m = 6371009.0 * sqrt($x*$x + $y*$y);
    #print "qckdist2=$m (no sqrt=)",6371009.0*($x*$x+$y*$y), "\n";

    return $m;
}

#
# The area A of a simple polygon can be computed if the cartesian coordinates 
# (x1, y1), (x2, y2), ..., (xn, yn) of its vertices, listed in order as the area 
# is circulated in counter-clockwise fashion, are known. The formula is
#
#    A = 0.5 * (x1y2 - x2y1 + x2y3 - x3y2 + ... + xny1 - x1yn)
#        = 0.5 * (x1(y2 - yn) + x2(y3 - y1) + x3(y4 - y2) + ... + xn(y1 - yn-1)) 
# 
# Only works for simple polygons (which lines don't cross over)
#
# FIX: need to check it's a simple polygon!
#
sub polygon_area
{
    my ($track) = @_;
    my $totarea;
    my $first;
    my $seg;
    my $seg1;
    my $i;
    my $sz;

    $totarea = 0;
    $first = 0;
    $sz = scalar @$track;

    print "track sz=$sz\n";
    for ($i = 0; $i < $sz; $i++)
    {
        $seg = $track->[$i]->{'entry'}->{'centre'}->{'cart'};
        $seg1 = $track->[($i+1)%$sz]->{'entry'}->{'centre'}->{'cart'};

        #print Dumper($seg); print Dumper($seg1);
        $totarea = $totarea + 
            ($seg->{'x'}*$seg1->{'y'} - $seg1->{'x'}*$seg->{'y'})
    }

    # 'closing' segment (maybe 0)
    $seg = $track->[$sz-1]->{'centre'}->{'cart'};
    $seg1 = $track->[0]->{'centre'}->{'cart'};
    $seg->{'x'} //= 0;  # default of 0 if undef
    $seg->{'y'} //= 0;
    $seg1->{'x'} //= 0;
    $seg1->{'y'} //= 0;
    $totarea = $totarea + 
            ($seg->{'x'}*$seg1->{'y'} - $seg1->{'x'}*$seg->{'y'});

    $totarea = abs(0.5 * $totarea);

    return $totarea;
}

1;

