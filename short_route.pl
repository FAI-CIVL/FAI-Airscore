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

require DBD::mysql;

use POSIX qw(ceil floor);
#use Math::Trig;
#use Data::Dumper;
use TrackLib qw(:all);
use strict;

my $pi = atan2(1,1) * 4; 

my $dbh;
my $sth;

sub round 
{
    my ($number) = @_;
    return int($number + .5);
}


#
# Line segment P1 to P3
# P2 is centre of circle ..
#
sub find_closest
{
    my ($P1, $P2, $P3) = @_;
    my ($C1, $C2, $C3, $PR);
    my ($N, $CL);
    my ($v, $w, $phi, $phideg);
    my ($T, $O, $vl, $wl);
    my ($a, $b, $c);
    my $u;

    $C1 = polar2cartesian($P1);
    $C3 = polar2cartesian($P2);

    if ($P2->{'shape'} eq 'line')
    {
        return $P2;
    }

    if (!defined($P3))
    {
        # End of line case ..
        $O = vvminus($C1, $C3);
        $vl = vector_length($O);
        if ($vl != 0)
        {
            $O->{'x'} = $O->{'x'} * $P2->{'radius'} / $vl;
            $O->{'y'} = $O->{'y'} * $P2->{'radius'} / $vl;
            $O->{'z'} = $O->{'z'} * $P2->{'radius'} / $vl;
            $CL = vvplus($O, $C3);
        }
        else
        {
            return $P2;
        }

        return cartesian2polar($CL);
    }

#    Same point repeated?
#    if ($P1->{'dlat'} == $P2->{'dlat'} &&
#        $P1->{'dlong'} == $P2->{'dlong'})
#    {
#        # same centre .. just do a radius check ..
#        $a = vvminus($C1, $C2);
#        $vl = vector_length($a);
#        $O = vvminus($N, $C2);
#        $vl = vector_length($O);
#        $O->{'x'} = $O->{'x'} * $P2->{'radius'} / $vl;
#        $O->{'y'} = $O->{'y'} * $P2->{'radius'} / $vl;
#        $O->{'z'} = $O->{'z'} * $P2->{'radius'} / $vl;
#        $CL = vvplus($O, $C2);
#
#    }

    $C2 = polar2cartesian($P3);

    # What if they have the same centre?
    if (vvequal($C1,$C2) == 1)
    {
        $O = vvminus($C1, $C3);
        $vl = vector_length($O);
        if ($vl > 0)
        {
            $O->{'x'} = $O->{'x'} * $P2->{'radius'} / $vl;
            $O->{'y'} = $O->{'y'} * $P2->{'radius'} / $vl;
            $O->{'z'} = $O->{'z'} * $P2->{'radius'} / $vl;
        }
        $CL = vvplus($O, $C3);

        return cartesian2polar($CL);
    }

    $u = (($C3->{'x'} - $C1->{'x'})*($C2->{'x'} - $C1->{'x'}) 
            + ($C3->{'y'} - $C1->{'y'})*($C2->{'y'} - $C1->{'y'}) 
            + ($C3->{'z'} - $C1->{'z'})*($C2->{'z'} - $C1->{'z'})) / 
        (($C2->{'x'} - $C1->{'x'})*($C2->{'x'} - $C1->{'x'}) +
            + ($C2->{'y'} - $C1->{'y'})*($C2->{'y'} - $C1->{'y'}) 
            + ($C2->{'z'} - $C1->{'z'})*($C2->{'z'} - $C1->{'z'})); 

    print "u=$u\n";
    $T = vvminus($C1,$C3);
    print "cart dist=", vector_length($T), "\n";
    print "polar dist=", distance($P1, $P2), "\n";

    $N = vvplus($C1, cvmult($u, vvminus($C2, $C1)));
    $CL = $N;
    $PR = cartesian2polar($CL);
    if (($u >= 0 && $u <= 1)
        && (distance($PR, $P2) < $P2->{'radius'}))
    {
        my $theta;
        my $db;
        my $vn;

        # Ok - we have a 90deg connect
        print "90 connect\n";
        # find the intersection points (maybe in cylinder)
        #$v = plane_normal($C1, $C3);
        #$w = plane_normal($C2, $C3);

        #print "dot_prod=",dot_product($a,$b), "\n";
        #print "theta=$theta\n";
        #$a = vvminus($C1, $C3);
        #$vl = vector_length($a);
        #if ($vl > 0)
        #{
        #    $a = vcdiv($a, $vl);
        #}
        #$b = vvminus($C2, $C3);
        #$vl = vector_length($b);
        #if ($vl > 0)
        #{
        #    $b = vcdiv($b, $vl);
        #}
        #$theta = acos(dot_product($a,$b));

        #$vn = vvplus($a,$b);
        #$vl = vector_length($vn);
        #$vn = vcdiv($vn,$vl);
        #$O = cvmult($P2->{'radius'},$vn);
        #print "vec_len=", vector_length($O), "\n";
        #$CL = vvplus($O,$C3);
    }
    else
    {
        # find the angle between in/out line

        $v = plane_normal($C1, $C3);
        $w = plane_normal($C2, $C3);
        $phi = acos(dot_product($v,$w));
        $phideg = $phi * 180 / $pi;
        print "angle between in/out=$phideg\n";
        
        # div angle / 2 add to one of them to create new
        # vector and scale to cylinder radius for new point 
        $a = vvminus($C1, $C3);
        $vl = vector_length($a);
        if ($vl > 0)
        {
            $a = vcdiv($a, $vl);
        }
        $b = vvminus($C2, $C3);
        $vl = vector_length($b);
        if ($vl > 0)
        {
            $b = vcdiv($b, $vl);
        }

        $O = vvplus($a, $b);
        $vl = vector_length($O);

        if ($phideg < 180)
        {
            $O->{'x'} = $O->{'x'} * $P2->{'radius'} / $vl;
            $O->{'y'} = $O->{'y'} * $P2->{'radius'} / $vl;
            $O->{'z'} = $O->{'z'} * $P2->{'radius'} / $vl;
        }
        else
        {
            $O->{'x'} = -$O->{'x'} * $P2->{'radius'} / $vl;
            $O->{'y'} = -$O->{'y'} * $P2->{'radius'} / $vl;
            $O->{'z'} = -$O->{'z'} * $P2->{'radius'} / $vl;
        }

        $CL = vvplus($O, $C3);
    }

    #print "Centre=", Dumper($C3), "\n";
    #print "Closest=", Dumper($CL), "\n";
    return cartesian2polar($CL);
}

#
# Find the task totals and update ..
#   tasTotalDistanceFlown, tasPilotsLaunched, tasPilotsTotal
#   tasPilotsGoal, tasPilotsLaunched, 
#
sub task_update
{
    my ($tasPk) = @_;
    my $wpts;
    my $dist;
    my $totdist;
    my $i = 0;
    my $num;
    my @it1;
    my @it2;
    my @closearr;
    my $newcl;
    my $task;

    $totdist = 0.0;
    $dbh->do("delete from tblShortestRoute where tasPk=$tasPk");
    $task = read_task($tasPk);

    $wpts = $task->{'waypoints'};

    # Ok work out non-optimal distance for now
    $num = scalar @$wpts;
    print "task $tasPk with $num waypoints\n";

    if ($num < 2)
    {
        if ($num == 1)
        {
            $sth = $dbh->prepare("insert into tblShortestRoute (tasPk,tawPk,ssrLatDecimal,ssrLongDecimal,ssrNumber) values ($tasPk,".  $wpts->[0]->{'key'}. ",". $wpts->[0]->{'dlat'}. ",". $wpts->[0]->{'dlong'}. ",". $wpts->[0]->{'number'}. ")");
            $sth->execute();
        }
        return 0;
    }

    # Work out shortest route!
    # End points don't vary?
    push @it1, $wpts->[0];
    $newcl = $wpts->[0];
    for ($i = 0; $i < $num-2; $i++)
    {
        print "From $i: ", $wpts->[$i]->{'name'}, "\n";
        if (ddequal($wpts->[$i+1], $wpts->[$i+2]))
        {
            $newcl = find_closest($newcl, $wpts->[$i+1], undef);
        }
        else
        {
            $newcl = find_closest($newcl, $wpts->[$i+1], $wpts->[$i+2]);
        }
        push @it1, $newcl;
    }
    # FIX: special case for end point ..
    #print "newcl=", Dumper($newcl);
    $newcl = find_closest($newcl, $wpts->[$num-1], undef);
    push @it1, $newcl;

    print "Iteration 2\n";
    $num = scalar @it1;
    push @it2, $it1[0];
    $newcl = $it1[0];
    for ($i = 0; $i < $num-2; $i++)
    {
        $newcl = find_closest($newcl, $it1[$i+1], $it1[$i+2]);
        push @it2, $newcl;
    }
    push @it2, $it1[$num-1];

    print "Iteration 3\n";
    $num = scalar @it2;
    push @closearr, $it2[0];
    $newcl = $it2[0];
    for ($i = 0; $i < $num-2; $i++)
    {
        $newcl = find_closest($newcl, $it2[$i+1], $it2[$i+2]);
        push @closearr, $newcl;
    }
    push @closearr, $it2[$num-1];

    for ($i = 0; $i < $num-1; $i++)
    {
        $dist = distance($wpts->[$i], $wpts->[$i+1]);
        print "Dist wpt:$i to wpt:", $i+1, "=$dist\n";
        $dist = distance($closearr[$i], $closearr[$i+1]);
        print "Dist cls:$i to cls:", $i+1, "=$dist\n";
        $sth = $dbh->prepare("insert into tblShortestRoute (tasPk,tawPk,ssrLatDecimal,ssrLongDecimal,ssrCumulativeDist,ssrNumber) values ($tasPk,".
           $wpts->[$i]->{'key'}. ",". $closearr[$i]->{'dlat'}. ",". $closearr[$i]->{'dlong'}. ",". $totdist . "," . $wpts->[$i]->{'number'}. ")");
        $totdist = $totdist + $dist;
        $sth->execute();
    }

    $sth = $dbh->prepare("insert into tblShortestRoute (tasPk,tawPk,ssrLatDecimal,ssrLongDecimal,ssrCumulativeDist,ssrNumber) values ($tasPk,".  $wpts->[$i]->{'key'}. ",". $closearr[$i]->{'dlat'}. ",". $closearr[$i]->{'dlong'}. ",". $totdist . "," . $wpts->[$i]->{'number'}. ")");
    $sth->execute();

    # Store it in tblTask
    print "update tblTask set tasShortRouteDistance=$totdist where tasPk=$tasPk\n";
    $sth = $dbh->prepare("update tblTask set tasShortRouteDistance=$totdist where tasPk=$tasPk");
    $sth->execute();

    return $totdist;
}

sub short_dist
{
    my ($w1, $w2) = @_;
    my $dist;
    my (%s1, %s2);

    $s1{'lat'} = $w1->{'short_lat'};
    $s1{'long'} = $w1->{'short_long'};
    $s2{'lat'} = $w2->{'short_lat'};
    $s2{'long'} = $w2->{'short_long'};

    $dist = distance(\%s1, \%s2);
    return $dist;
}
#
# Determine the distances to startss / endss / ss distance
#
sub determine_distances
{
    my ($task) = @_;
    my $waypoints;
    my $cwdist;
    my ($spt, $ept, $gpt);
    my $ssdist;
    my $allpoints;
    my $endssdist;
    my $startssdist;
    my $tasPk;

    $waypoints = $task->{'waypoints'};
    $tasPk = $task->{'tasPk'};
    $allpoints = scalar @$waypoints;
    $cwdist = 0;
    for (my $i = 0; $i < $allpoints; $i++)
    {
        # Margins
        my $margin = $waypoints->[$i]->{'radius'} * 0.0005;
        if ($margin < 5.0)
        {
            $margin = 5.0;
        }
        $waypoints->[$i]->{'margin'} = $margin;

        if (( $waypoints->[$i]->{'type'} eq 'start') or 
             ($waypoints->[$i]->{'type'} eq 'speed') )
        {
            $spt = $i;
            $startssdist = $cwdist;
            if ($startssdist == 0 && ($waypoints->[$i]->{'how'} eq 'exit'))
            {
                $startssdist += $waypoints->[$i]->{'radius'};
            }
        }
        if ($waypoints->[$i]->{'type'} eq 'speed') 
        {
            $cwdist = 0;
        }
        if ($waypoints->[$i]->{'type'} eq 'endspeed') 
        {
            $ept = $i;
            $endssdist = $cwdist;
            if ($waypoints->[$i]->{'how'} eq 'exit')
            {
                $endssdist += $waypoints->[$i]->{'radius'};
            }
        }
        if ($waypoints->[$i]->{'type'} eq 'goal') 
        {
            $gpt = $i;
        }
        if ($i < $allpoints-1)
        {
            $cwdist = $cwdist + short_dist($waypoints->[$i], $waypoints->[$i+1]);
        }
    }
    if (!defined($gpt))
    {
        $gpt = $allpoints;
    }
    if (!defined($ept))
    {
        $ept = $gpt;
    }
    if (!defined($endssdist)) 
    {
        $endssdist = $cwdist;
        if ($waypoints->[$gpt]->{'how'} eq 'exit')
        {   
            $endssdist += $waypoints->[$gpt]->{'radius'};
        }   
    }

    $ssdist = $endssdist - $startssdist;
    print "spt=$spt ept=$ept gpt=$gpt ssdist=$ssdist startssdist=$startssdist endssdist=$endssdist\n";
    print "update tblTask set tasSSDistance=$ssdist, tasEndSSDistance=$endssdist, tasStartSSDistance=$startssdist where tasPk=$tasPk\n";
    $sth = $dbh->prepare("update tblTask set tasSSDistance=$ssdist, tasEndSSDistance=$endssdist, tasStartSSDistance=$startssdist where tasPk=$tasPk");
    $sth->execute();

    return ($spt, $ept, $gpt, $ssdist, $startssdist, $endssdist);
}

#
# Main program here ..
#

my $dist;
my $taskno;
my $task;

$dbh = db_connect();

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
determine_distances($task);

#print "Task dist=$dist\n";


