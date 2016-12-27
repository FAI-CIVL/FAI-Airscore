#!/usr/bin/perl 
##!/usr/bin/perl -I/home/geoff/bin
#
# Determine the shortest route using cartesian coords
# 
# Geoff Wong 2008
#
# Determine closest points on cylinders using line segments (P1,P3) to find P2,
# then (P2,P4) to find (new) P3, etc. Then repeat until change each time is reduced below a threshold
# (or just repeat a fixed number of times?).
# 
# Determining intersection / closest point sphere / line (3d)
# 
# Points P (x,y,z) on a line defined by two points P1 (x1,y1,z1) and P2 (x2,y2,z2) is described by
# P = P1 + u (P2 - P1)
# 
# or in each coordinate
# x = x1 + u (x2 - x1)
# y = y1 + u (y2 - y1)
# z = z1 + u (z2 - z1)
# 
# A sphere centered at P3 (x3,y3,z3) with radius r is described by
# (x - x3)2 + (y - y3)2 + (z - z3)2 = r2
# 
# Substituting the equation of the line into the sphere gives a quadratic equation of the form
# a u2 + b u + c = 0
# 
# where:
# 
# a = (x2 - x1)2 + (y2 - y1)2 + (z2 - z1)2
# b = 2[ (x2 - x1) (x1 - x3) + (y2 - y1) (y1 - y3) + (z2 - z1) (z1 - z3) ]
# c = x32 + y32 + z32 + x12 + y12 + z12 - 2[x3 x1 + y3 y1 + z3 z1] - r2
# 
# The solutions to this quadratic are described by
# 
# The exact behaviour is determined by the expression within the square root
# 
# b * b - 4 * a * c
# 
#     * If this is less than 0 then the line does not intersect the sphere.
#     * If it equals 0 then the line is a tangent to the sphere intersecting it at one point, namely at u = -b/2a.
#     * If it is greater then 0 the line intersects the sphere at two points. 
# 
# To apply this to two dimensions, that is, the intersection of a line and a circle simply remove the z component from the above mathematics. 
# When dealing with a line segment it may be more efficient to first determine whether the line actually intersects the sphere or circle. This is achieved by noting that the closest point on the line through P1P2 to the point P3 is along a perpendicular from P3 to the line. In other words if P is the closest point on the line then
# 
# (P3 - P) dot (P2 - P1) = 0
# 
# Substituting the equation of the line into this
# 
# [P3 - P1 - u(P2 - P1)] dot (P2 - P1) = 0
# 
# Solving the above for u =
# (x3 - x1)(x2 - x1) + (y3 - y1)(y2 - y1) + (z3 - z1)(z2 - z1)
# -----------------------------------------------------------
# (x2 - x1)(x2 - x1) + (y2 - y1)(y2 - y1) + (z2 - z1)(z2 - z1)
# 
# If u is not between 0 and 1 then the closest point is not between P1 and P2
# 
# Given u, the intersection point can be found, it must also be less than the radius r. 
# If these two tests succeed then the earlier calculation of the actual intersection point can be applied. 
# 

use POSIX qw(ceil floor);
use Route qw(:all);
use strict;

#
# Main program here ..
#

my $dist;
my $taskno;
my $task;

my $dbh = db_connect();

if (scalar @ARGV == 0)
{
    print "short_route.pl <tasPk>\n";
    exit(0);
}
$taskno = $ARGV[0];

# Work out the shortest route through task
$dist = task_update($taskno);

# Work out some distances
$task = read_task($taskno);
my ($spt, $ept, $gpt, $ssdist, $startssdist, $endssdist) = task_distance($task);
print "spt=$spt ept=$ept gpt=$gpt ssdist=$ssdist startssdist=$startssdist endssdist=$endssdist\n";
print "update tblTask set tasSSDistance=$ssdist, tasEndSSDistance=$endssdist, tasStartSSDistance=$startssdist where tasPk=$taskno\n";
my $sth = $dbh->prepare("update tblTask set tasSSDistance=$ssdist, tasEndSSDistance=$endssdist, tasStartSSDistance=$startssdist where tasPk=$taskno");
$sth->execute();


#print "Task dist=$dist\n";


