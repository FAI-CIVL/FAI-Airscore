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

require Exporter;
our @ISA       = qw(Exporter);
our @EXPORT = qw{:ALL};

use POSIX qw(ceil floor);
use strict;

my $pi = atan2(1,1) * 4; 

my $dbh;
my $sth;

#
# Input: Line segment P1 -> P2 -> P3
# Return: optimised P2 
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
    $C2 = polar2cartesian($P2);

    if ($P2->{'shape'} eq 'line')
    {
        return $P2;
    }

    if (!defined($P3))
    {
        # End of line case ..
        $O = $C1 - $C2;
        $vl = $O->length();
        if ($vl != 0)
        {
            $O = ($P2->{'radius'} / $vl) * $O;
            $CL = $O + $C2;
        }
        else
        {
            return $P2;
        }

        my $result = cartesian2polar($CL);
        #$result->{'radius'} = $P2->{'radius'};
        return $result;
    }

#    Same point repeated?
#    if (ddequal($P1, $P2))
#    {
#        # same centre .. just do a radius check ..
#        $a = vvminus($C1, $C3);
#        $vl = vector_length($a);
#        $O = vvminus($N, $C3);
#        $vl = vector_length($O);
#        $O = cvmult($P2->{'radius'} / $vl, $O);
#        $CL = vvplus($O, $C3);
#    }

    $C3 = polar2cartesian($P3);

    # What if they have the same centre?
    if ($C1 == $C3)
    {
        $O = $C1 - $C2;
        $vl = $O->length();
        if ($vl < 0.01)
        {
            # They're all the same point .. not much we can do until next iteration
            return $P2;
        }

        $O = ($P2->{'radius'} / $vl) * $O;
        $CL = $O + $C2;

        my $result = cartesian2polar($CL);
        # Keep radius for next iteration
        $result->{'radius'} = $P2->{'radius'};
        return $result;
    }


    # What if the 1st and 2nd have the same centre?
    $T = $C1 - $C2;
    if ($T->length() < 0.01)
    {
        $O = $C3 - $C2;
        $vl = $O->length();
        if ($vl > 0)
        {
            $O = ($P2->{'radius'} / $vl) * $O;
        }
        $CL = $O + $C2;

        my $result = cartesian2polar($CL);
        return $result;
    }

    $u = (($C2->{'x'} - $C1->{'x'})*($C3->{'x'} - $C1->{'x'}) 
            + ($C2->{'y'} - $C1->{'y'})*($C3->{'y'} - $C1->{'y'}) 
            + ($C2->{'z'} - $C1->{'z'})*($C3->{'z'} - $C1->{'z'})) / 
        (($C3->{'x'} - $C1->{'x'})*($C3->{'x'} - $C1->{'x'}) +
            + ($C3->{'y'} - $C1->{'y'})*($C3->{'y'} - $C1->{'y'}) 
            + ($C3->{'z'} - $C1->{'z'})*($C3->{'z'} - $C1->{'z'})); 
    #print "u=$u cart dist=", vector_length($T), " polar dist=", distance($P1, $P2), "\n";

    $N = $C1 + ($u * ($C3 - $C1));
    $CL = $N;
    $PR = cartesian2polar($CL);
    if (($u >= 0 && $u <= 1)
        && (distance($PR, $P2) < $P2->{'radius'}))
    {
        my $theta;
        my $db;
        my $vn;

        # Ok - we have a 180deg? connect
        print "180 deg connect: u=$u radius=", $P2->{'radius'}, "\n";
        return $P2;
    
#        if ($P2->{'how'} eq 'exit' && $u == 0)
#        {
#            $O = vvminus($C3, $C2);
#            $vl = vector_length($O);
#            print "short route point must be on the cylinder\n";
#            if ($vl > 0)
#            {
#                $O = cvmult($P2->{'radius'} / $vl, $O);
#            }
#            $CL = vvplus($O, $C2);
#            $PR = cartesian2polar($CL);
#        }

        # find the intersection points (maybe in cylinder)
        #$v = plane_normal($C1, $C2);
        #$w = plane_normal($C3, $C2);

        #print "dot_prod=",dot_product($a,$b), "\n";
        #print "theta=$theta\n";
        #$a = vvminus($C1, $C2);
        #$vl = vector_length($a);
        #if ($vl > 0)
        #{
        #    $a = vcdiv($a, $vl);
        #}
        #$b = vvminus($C3, $C2);
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
        #$CL = vvplus($O,$C2);
    }
    else
    {
        my $vla;
        my $vlb;

        # find the angle between in/out line
        $v = plane_normal($C1, $C2);
        $w = plane_normal($C3, $C2);
        $phi = acos($v . $w);
        $phideg = $phi * 180 / $pi;
        #print "    angle between in/out=$phideg\n";
        
        # div angle / 2 add to one of them to create new
        # vector and scale to cylinder radius for new point 
        $a = $C1 - $C2;
        $vla = $a->length();
        if ($vla > 0)
        {
            $a = $a / $vla;
        }
        $b = $C3 - $C2;
        $vlb = $b->length();
        if ($vlb > 0)
        {
            $b = $b / $vlb;
        }

        $O = $a + $b;
        $vl = $O->length();

        if ($phideg < 180)
        {
            #print "    p2->radius=", $P2->{'radius'}, "\n";
            $O = ($P2->{'radius'} / $vl) * $O;
        }
        else
        {
            #print "    -p2->radius=", $P2->{'radius'}, "\n";
            $O = (-$P2->{'radius'} / $vl) * $O;
        }

        $CL = $O + $C2;
    }

    #print "Centre=", Dumper($C2), "\n";
    #print "Closest=", Dumper($CL), "\n";
    my $result = cartesian2polar($CL);
    return $result;
}

#
# Find the task totals and update ..
#   tasTotalDistanceFlown, tasPilotsLaunched, tasPilotsTotal
#   tasPilotsGoal, tasPilotsLaunched, 
#
sub find_shortest_route
{
    my ($task) = @_;
    my $dist;
    my $i = 0;
    my @it1;
    my @it2;
    my @closearr;
    my $newcl;

    my $tasPk = $task->{'tasPk'};
    my $wpts = $task->{'waypoints'};
    my $num = scalar @$wpts;


    # Ok work out non-optimal distance for now
    print "task $tasPk with $num waypoints\n";
    #print Dumper($wpts);

    if ($num < 1)
    {
        return undef;
    }

    if ($num == 1)
    {
        my $first = cartesian2polar(polar2cartesian($wpts->[0]));
        push @closearr, $first;
        return \@closearr;
    }

    # Work out shortest route!
    # End points don't vary?
    push @it1, $wpts->[0];
    $newcl = $wpts->[0];
    for ($i = 0; $i < $num-2; $i++)
    {
        #print "From it1: $i: ", $wpts->[$i]->{'name'}, "\n";
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
    #print "From it1: $i: ", $wpts->[$i]->{'name'}, "\n";
    $newcl = find_closest($newcl, $wpts->[$num-1], undef);
    push @it1, $newcl;
    #print "IT1=", Dumper(\@it1);

    $num = scalar @it1;
    push @it2, $it1[0];
    $newcl = $it1[0];
    for ($i = 0; $i < $num-2; $i++)
    {
        #print "From it2: $i: ", $wpts->[$i]->{'name'}, "\n";
        $newcl = find_closest($newcl, $it1[$i+1], $it1[$i+2]);
        push @it2, $newcl;
    }
    push @it2, $it1[$num-1];
    #print "IT2=", Dumper(\@it2);

    $num = scalar @it2;
    push @closearr, $it2[0];
    $newcl = $it2[0];
    for ($i = 0; $i < $num-2; $i++)
    {
        #print "From it3: $i: ", $wpts->[$i]->{'name'}, "\n";
        $newcl = find_closest($newcl, $it2[$i+1], $it2[$i+2]);
        push @closearr, $newcl;
    }
    push @closearr, $it2[$num-1];
    #print "closearr=", Dumper(\@closearr);

    #for (my $i = 0; $i < scalar @closearr-1; $i++)
    #{
    #    my $dist = distance($wpts->[$i], $wpts->[$i+1]);
    #    my $cdist = distance($closearr[$i], $closearr[$i+1]);
    #    my $radius = 0 + $closearr[$i]->{'radius'};
    #    print "Dist wpt:$i ($radius) to wpt:", $i+1, "=$dist srdist=$cdist\n";
    #}

    return \@closearr;
}

sub store_short_route
{
    my ($dbh, $task, $closearr) = @_;
    my $totdist = 0.0;
    my $wpts = $task->{'waypoints'};
    my $tasPk = $task->{'tasPk'};
    my $num = scalar @$closearr;
    my $i = 0;
    my $dist;
    my $cdist;

    # Clean up
    $dbh->do("delete from tblShortestRoute where tasPk=$tasPk");

    # Insert each short route waypoint
    for ($i = 0; $i < $num-1; $i++)
    {
        $dist = distance($wpts->[$i], $wpts->[$i+1]);
        $cdist = distance($closearr->[$i], $closearr->[$i+1]);
        print "Dist wpt:$i to wpt:", $i+1, " dist=$dist short_dist=$cdist\n";
        $sth = $dbh->do("insert into tblShortestRoute (tasPk,tawPk,ssrLatDecimal,ssrLongDecimal,ssrCumulativeDist,ssrNumber) values (?,?,?,?,?,?)",
            undef,$tasPk,$wpts->[$i]->{'key'}, $closearr->[$i]->{'dlat'}, $closearr->[$i]->{'dlong'}, $totdist,  $wpts->[$i]->{'number'});
        $totdist = $totdist + $cdist;
    }

    $sth = $dbh->do("insert into tblShortestRoute (tasPk,tawPk,ssrLatDecimal,ssrLongDecimal,ssrCumulativeDist,ssrNumber) values (?,?,?,?,?,?)",
            undef, $tasPk,$wpts->[$i]->{'key'}, $closearr->[$i]->{'dlat'}, $closearr->[$i]->{'dlong'}, $totdist,  $wpts->[$i]->{'number'});

    # Store it in tblTask
    print "update tblTask set tasShortRouteDistance=$totdist where tasPk=$tasPk\n";
    $sth = $dbh->do("update tblTask set tasShortRouteDistance=? where tasPk=?", undef, $totdist, $tasPk);
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
# Returns a tuple containing:
#   $spt - index of start speed point
#   $ept - index of end speed point
#   $gpt - index of goal point
#   $ssdist - speed section distance
#   $startssdist - distance to start of speed section
#   $endssdist - distane to end of speed section
#   $totdist - total task distance
#
sub task_distance
{
    my ($task) = @_;
    my ($spt, $ept, $gpt);
    my $ssdist;
    my $endssdist;
    my $startssdist;

    my $waypoints = $task->{'waypoints'};
    my $allpoints = scalar @$waypoints;
    my $cwdist = 0;
    for (my $i = 0; $i < $allpoints; $i++)
    {
        # Margins
        my $margin = $waypoints->[$i]->{'radius'} * 0.005;  # I created input variable margin in Formula, already inserted in $Task should change to use that
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
            if ($startssdist < 1 && ($waypoints->[$i]->{'how'} eq 'exit'))
            {
                $startssdist += $waypoints->[$i]->{'radius'};
            }
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
            if (ddequal($waypoints->[$i], $waypoints->[$i+1]) && $waypoints->[$i+1]->{'how'} eq 'exit')
            {
                $cwdist = $cwdist + $waypoints->[$i+1]->{'radius'};
                if ($waypoints->[$i]->{'type'} ne 'start')
                {
                    $cwdist = $cwdist - $waypoints->[$i]->{'radius'};
                }
            }
            else
            {
                $cwdist = $cwdist + short_dist($waypoints->[$i], $waypoints->[$i+1]);
            }
        }
        print "wpt $i: $cwdist\n";
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

    return ($spt, $ept, $gpt, $ssdist, $startssdist, $endssdist, $cwdist);
}

sub in_semicircle
{
    my ($waypoints, $wmade, $coord) = @_;
    my ($bvec, $pvec);
    my $wpt = $waypoints->[$wmade];

    my $prev = $wmade - 1;
    while ($prev > 0 and ddequal($wpt, $waypoints->[$prev]))
    {
        $prev--;
    }
    
    my $c = polar2cartesian($wpt); 
    my $p = polar2cartesian($waypoints->[$prev]); 

    # vector that bisects the semi-circle pointing into occupied half plane
    $bvec = $c - $p;
    $pvec = $coord->{'cart'} - $c;

    # dot product 
    my $dot = $bvec . $pvec;
    if ($dot > 0)
    {
        return 1;
    }

    return 0;
}

1;
