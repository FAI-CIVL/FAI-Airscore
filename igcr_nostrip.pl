#!/usr/bin/perl

#
# Reads in an IGC file
#
#
# Notes: UTC is 13 seconds later than GPS time (!)
#        metres, kms, kms/h, DDMMYY HHMMSSsss, true north,
#        DDMM.MMMM (NSEW designators), hPascals
#
# Geoff Wong 2007
#
require DBD::mysql;

use Math::Trig;
use Data::Dumper;

my $min_dist = 10;
my $first_time = 0;
my $last_time = 0;

my $track_width = 200;      # metres either side of middle lines
my $pi = atan2(1,1) * 4;    # accurate PI.

my $bucket_radius = 200;    # aggregation of points radius

my $database = 'xcdb';
my $hostname = 'localhost';
my $port = 3306;

local * FD;


#
# Database handles
#

my $dsn;
my $dbh;
my $drh;

sub db_connect
{
    $dsn = "DBI:mysql:database=$database;host=$hostname;port=$port";
    $dbh = DBI->connect( $dsn, 'xc', '%MYSQLPASSWORD%', { RaiseError => 1 } )
            or die "Can't connect: $!\n";
    $drh = DBI->install_driver("mysql");
}

#
# Extract header info ...
#
sub extract_header
{
    my ($header,$row) = @_;
    my $rowtype;

    $rowtype = substr $row, 1, 4;

    if ($rowtype eq "FDTE")
    {
        # date
        $header->{'date'} = substr($row, 9, 2) . substr($row, 7, 2) . substr($row, 5, 2);
    }
    elsif ($rowtype eq "FPLT")
    {
        # pilot
        $header->{'pilot'} = substr($row, 5);
    }
    elsif ($rowtype eq "FTZO")
    {
        # timezone
        $header->{'timezone'} = substr($row, 5);
    }
    elsif ($rowtype eq "FSIT")
    {
        # site
        $header->{'site'} = substr($row, 5);
    }
    elsif ($rowtype eq "FDTM")
    {
        # datum (WGS-1984?)
        $header->{'datum'} = substr($row, 5);
    }
    elsif ($rowtype eq "PGTY")
    {
        # glider type
        $header->{'glider'} = substr($row, 5);
    }
    elsif ($rowtype eq "PGID")
    {
        # glider id
        $header->{'gliderid'} = substr($row, 5);
    }
}

#
# Extract 'fix' data into a nice record
#
sub extract_fix
{
    my ($row) = @_;
    my %loc;
    my $ns;
    my $ew;
    my $h;
    my $m;
    my $s;

    $h = 0 + substr $row, 1, 2;
    $m = 0 + substr $row, 3, 2;
    $s = 0 + substr $row, 5, 2;
    $loc{'time'}= $h * 3600 + $m * 60 + $s;
    if ($first_time == 0)
    {
        $first_time = $loc{'time'};
    }
    if ($loc{'time'} < $first_time)
    {
        # in case track log goes over 24/00 time boundary
        $loc{'time'} = $loc{'time'} + 24 * 3600;
    }
    if ($loc{'time'} <= $last_time)
    {
        $loc{'time'} = $last_time + 1;
    }
    $last_time = $loc{'time'};

    $loc{'lat'} = 0 + substr $row, 7, 2;
    $m = (((0 + substr $row, 9, 5) / 1000) / 60);
    $loc{'lat'} = $loc{'lat'} + $m;
    $ns = substr $row, 14, 1;
    if ($ns eq "S")
    {
        $loc{'lat'} = -$loc{'lat'};
    }
    $loc{'dlat'} = $loc{'lat'};
    $loc{'lat'} = $loc{'lat'} * $pi / 180;

    $loc{'long'} = 0 + substr $row, 15, 3;
    $m = (((0 + substr $row, 18, 5) / 1000) / 60);
    $loc{'long'} = $loc{'long'} + $m;
    $ew = substr $row, 23, 1;
    if ($ns eq "W")
    {
        $loc{'long'} = -$loc{'long'};
    }
    $loc{'dlong'} = $loc{'long'};
    $loc{'long'} = $loc{'long'} * $pi / 180;

    $loc{'fix'} = substr $row, 24, 1;
    $loc{'pressure'} = 0 + substr $row, 25, 5;
    $loc{'altitude'} = 0 + substr $row, 30, 5;
    # dodgy XC trainer fix 
    if ($loc{'altitude'} == 0 and $loc{'pressure'} != 0)
    {
        $loc{'altitude'} = $loc{'pressure'};
    }

    $c1 = polar2cartesian(\%loc);
    $loc{'cart'} = $c1;

    return \%loc;
}

sub read_igc
{
    my ($f) = @_;
    my %flight;
    my %header;
    my @coords;
    my $rowtype;

    print "reading: $f\n";
    open(FD, "$f") or die "can't open $f: $!";

    while (<FD>)
    {
        $row = $_;
        $rowtype = substr $row, 0, 1;
        #print "rowtype=#$rowtype#\n";

        if ($rowtype eq "A")
        {
            # manafacturer & identification of recorder (1st record)
        }
        elsif ($rowtype eq "B")
        {
            # "fix"
            #print "found fix: $rowtype\n";
            # UTC (6), Lat (8), Long (9), Fix (1), Pressure (5), Altitude (5)
            $crd = extract_fix($row);
            push @coords, $crd;
        }
        elsif ($rowtype eq "C")
        {
            # task & declaration
        }
        elsif ($rowtype eq "D")
        {
            # differential GPS
        }
        elsif ($rowtype eq "E")
        {
            # event
        }
        elsif ($rowtype eq "F")
        {
            # satellite constellation (change)
        }
        elsif ($rowtype eq "G")
        {
            # Security (last record)
        }
        elsif ($rowtype eq "H")
        {
            # header (2nd)
            extract_header(\%header, $row);
        }
        elsif ($rowtype eq "I")
        {
            # list of extension data included at end of each B record
        }
        elsif ($rowtype eq "J")
        {
            # list of extension data included at end of each K record
        }
        elsif ($rowtype eq "K")
        {
            # extension data
        }
        elsif ($rowtype eq "L")
        {
            # Log book / comments (3rd)
        }
    }

    $flight{'coords'} = \@coords;
    $flight{'header'} = \%header;

    return \%flight;
}

#
# Store the tracklog in the database
#
sub store_track
{
    my ($flight, $pilPk) = @_;
    my $traPk;
    my $coords;
    my $sth;

        
    $dbh->do("INSERT INTO tblTrack (pilPk, traGlider) VALUES (?,?)", undef, $pilPk,1);
    $sth = $dbh->prepare("select max(traPk) from tblTrack");
    $sth->execute();
    $traPk  = $sth->fetchrow_array();
    print "max track=$traPk\n";

    $coords = $flight->{'coords'};
    foreach $pla (@$coords)
    {
        $dbh->do("INSERT INTO tblTrackLog (traPk, trlLatDecimal, trlLongDecimal, trlTime) VALUES (?,?,?,?)", undef, $traPk, $pla->{'dlat'}, $pla->{'dlong'}, $pla->{'time'});
    }

    return $traPk;
}

#
# Store waypoints associated with track
#
sub store_waypoints
{
    my ($traPk,$flight) = @_;
    my $coords;
    my $sth;
    my $seg;
    my $i;
    my $sz;

    #$sth = $dbh->prepare("select max(traPk) from tblTrack");
    #$sth->execute();
    #$traPk  = $sth->fetchrow_array();

    $sz = scalar @$flight;
    for ($i = 0; $i < $sz; $i++)
    {
        $seg = $flight->[$i];
        $dbh->do("INSERT INTO tblWaypoint (traPk, wptLatDecimal, wptLongDecimal, wptTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'entry'}->{'centre'}->{'dlat'}, $seg->{'entry'}->{'centre'}->{'dlong'}, $seg->{'entry'}->{'centre'}->{'time'});
        #$dbh->do("INSERT INTO tblWaypoint (traPk, wptLatDecimal, wptLongDecimal, wptTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'exit'}->{'centre'}->{'dlat'}, $seg->{'exit'}->{'centre'}->{'dlong'}, $seg->{'exit'}->{'centre'}->{'time'});
    }

    $i = $sz - 1;
    $seg = $flight->[$i];
    # Add the exit of the last segment too ...
    $dbh->do("INSERT INTO tblWaypoint (traPk, wptLatDecimal, wptLongDecimal, wptTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'exit'}->{'centre'}->{'dlat'}, $seg->{'exit'}->{'centre'}->{'dlong'}, $seg->{'exit'}->{'centre'}->{'time'});
}

sub store_segments
{
    my ($traPk,$flight) = @_;
    my $coords;
    my $sth;
    my $seg;
    my $i;
    my $sz;

    #$sth = $dbh->prepare("select max(traPk) from tblTrack");
    #$sth->execute();
    #$traPk  = $sth->fetchrow_array();

    $sz = scalar @$flight;
    for ($i = 0; $i < $sz; $i++)
    {
        $seg = $flight->[$i];
        $dbh->do("INSERT INTO tblSegment (traPk, wptLatDecimal, wptLongDecimal, wptTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'entry'}->{'centre'}->{'dlat'}, $seg->{'entry'}->{'centre'}->{'dlong'}, $seg->{'entry'}->{'centre'}->{'time'});
        #$dbh->do("INSERT INTO tblSegment (traPk, wptLatDecimal, wptLongDecimal, wptTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'exit'}->{'centre'}->{'dlat'}, $seg->{'exit'}->{'centre'}->{'dlong'}, $seg->{'exit'}->{'centre'}->{'time'});
    }

    $i = $sz - 1;
    $seg = $flight->[$i];
    # Add the exit of the last segment too ...
    $dbh->do("INSERT INTO tblSegment (traPk, wptLatDecimal, wptLongDecimal, wptTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'exit'}->{'centre'}->{'dlat'}, $seg->{'exit'}->{'centre'}->{'dlong'}, $seg->{'exit'}->{'centre'}->{'time'});
}

#
# Store waypoints associated with track
#
sub store_buckets
{
    my ($traPk,$flight) = @_;
    my $coords;
    my $sth;
    my $seg;
    my $i;
    my $sz;

    #$sth = $dbh->prepare("select max(traPk) from tblTrack");
    #$sth->execute();
    #$traPk  = $sth->fetchrow_array();

    $sz = scalar @$flight;
    for ($i = 0; $i < $sz; $i++)
    {
        $seg = $flight->[$i];
        $dbh->do("INSERT INTO tblBucket (traPk, bucLatDecimal, bucLongDecimal, bucTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'centre'}->{'dlat'}, $seg->{'centre'}->{'dlong'}, $seg->{'centre'}->{'time'});
    }

    #$i = $sz - 1;
    #$seg = $flight->[$i];
    # Add the exit of the last segment too ...
    #$dbh->do("INSERT INTO tblWaypoint (traPk, wptLatDecimal, wptLongDecimal, wptTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'exit'}->{'centre'}->{'dlat'}, $seg->{'exit'}->{'centre'}->{'dlong'}, $seg->{'exit'}->{'centre'}->{'time'});
}

#
# determine if we're flying ...
#
sub is_flying
{
    my ($c1, $c2) = @_;
    my $dist;
    my $altdif;
    my $timdif;

    $dist = abs(distance($c1, $c2));
    $altdif = $c2->{'altitude'} - $c1->{'altitude'};
    $timdif = $c2->{'time'} - $c1->{'time'};

    #print "is flying dist=$dist altdif=$altdif timdif=$timdif\n";
    # allow breaks of up to 5 mins ..
    if ($timdif > 300)
    {
        # print "time not flying\n";
        #print "not flying: time gap=$timdif\n";
        return 0;
    }

    # 
    if ($dist > (50.0*($timdif)))
    {
        # strange distance ....
        # print "dist not flying\n";
        #print "not flying: teleported=$dist\n";
        return 0;
    }

    if ($dist < 3.0 and abs($altdif) < 4)
    {
        #print "c1->lat=", $c1->{'lat'}, "c1->long=", $c1->{'long'}, "\n";
        #print "c2->lat=", $c2->{'lat'}, "c2->long=", $c2->{'long'}, "\n";
        #print "c2->alt=", $c2->{'altitude'}, "\n";
        #print "not flying: didn't move: time=$timdif horiz=$dist vert=$altdif\n";
        return 0;
    }

    return 1;
}

sub trim_flight
{
    my ($flight, $pilPk) = @_;
    my $full;
    my @reduced;
    my $dist;
    my $max;
    my $next;
    my $last;
    my $timdif;
    my $count = 0;
    my $i;

    $full = $flight->{'coords'};

    # trim crap off the end of the flight ..
    #print "trim end\n";
    $coord = pop @$full;
    $next = pop @$full; 
    while (defined($next) && !is_flying($next, $coord))
    {
        $coord = $next;
        $next = pop @$full; 
    }
    # put the last two on again ...
    push @$full, $next;
    push @$full, $coord;

    # trim crap off the front of the flight ..
    #print "trim start\n";
    $coord = shift @$full;
    $next = shift @$full; 
    while (defined($next) && !is_flying($coord, $next))
    {
        $coord = $next;
        $next = shift @$full; 
    }

    # TODO: only take "latest" track if "broken"?
    # work backwards .. look for a !flying
    #print "trim for last flying segment\n";
    $timdif = 0;

    # look for a segment of at least 10 mins ..
#    $max = scalar @$full;
#    while ($timdif < 400 and $max > 2)
#    {
#        $max = scalar @$full;
#        $count = 0;
#        $last = $full->[$max-1];
#        for ($i = $max-1; $i > 0; $i--)
#        {
#            if ($last->{'time'} - $full->[$i-1]->{'time'} < 10)
#            {
#                next;
#            }
#            if (!is_flying($full->[$i-1], $last))
#            {
#                #print "max pt: $max, not flying at $i\n";
#                if ($last->{'time'} - $full->[$i-1]->{'time'} > 60)
#                {
#                    last;
#                }
#                $count++;
#            }
#            if ($count > 3)
#            {
#                # only "not" flying after 3?
#                last;
#            }
#            $last = $full->[$i-1];
#        }
#        $timdif = $full->[$max-1]->{'time'} - $full->[$i-1]->{'time'};
#        if (($timdif < 400) and ($i > 1))
#        {
#            @$full = splice(@$full, 0, $i-1);
#        }
#        elsif (($timdif >= 400) and ($i > 1))
#        {
#            @$full = splice(@$full, $i, $max-$i);
#        }
#
#        # don't loop forever if it's a good track!
#        if ($i == 0)
#        {
#            last;
#        }
#    }

    # store the trimmed track ...
    $traPk = store_track($flight, $pilPk);
    $flight->{'traPk'} = $traPk;

    return $flight;
}

#
# Reduce the flight into sequential Xm (radius) blobs
# Also trim off wild GPS points and determine start/end of track.
#
sub reduce_flight
{
    my ($flight, $pilPk) = @_;
    my $full;
    my @reduced;
    my $dist;
    my $next;


    $full = $flight->{'coords'};
    $coord = shift @$full; 

    # reduce into buckets
    while (defined($coord))
    {
        my %bucket;
        my @blist;

        %bucket = ();
        @blist = ();

        $bucket{'centre'} = $coord;
        push @blist, $coord;

        #print Dumper($coord);
        $next = shift @$full; 
        while (defined($next) && 
               (($dist=distance($coord, $next)) < $bucket_radius))
        {
            push @blist, $next;
            $next = shift @$full; 
        }

        $bucket{'bucket'} = \@blist;
        push @reduced, \%bucket;

        $coord = shift @$full;
        #print Dumper($coord);
    }

    return \@reduced;
}

#
# Find the normal to the plane created by the two points ..
# Normal n = u X v = 
#       ( (uy*vz - uz*vy), (uz*vx - ux*vz), (ux*vy - uy*vx) ) 
#
sub plane_normal
{
    my ($c1, $c2) = @_;
    my %n;

    # Find the normal to the plane created by the two points ..
    # Normal n = u X v = 
    #       ( (uy*vz - uz*vy), (uz*vx - ux*vz), (ux*vy - uy*vx) ) 

    $n{'x'} = $c1->{'y'}*$c2->{'z'} - $c1->{'z'}*$c2->{'y'}; 
    $n{'y'} = $c1->{'z'}*$c2->{'x'} - $c1->{'x'}*$c2->{'z'}; 
    $n{'z'} = $c1->{'x'}*$c2->{'y'} - $c1->{'y'}*$c2->{'x'}; 

#    print "normal=$n{'x'},$n{'y'},$n{'z'}\n";

    return \%n;
}


#
# simple absolute vector length
#
sub vector_length
{
    my ($v) = @_;

    return sqrt($v->{'x'}*$v->{'x'} + $v->{'y'}*$v->{'y'} 
                        + $v->{'z'}*$v->{'z'});

}


#
# 3d (euclidean) vector dot product
#
sub dot_product
{
    my ($v, $w) = @_;
    my $tl;

    $tl = $v->{'x'} * $w->{'x'} + $v->{'y'} * $w->{'y'} + $v->{'z'} * $w->{'z'};
    $bl = vector_length($v) * vector_length($w);

    if ($bl == 0) 
    {
        return 1.0;
    }

    return $tl/$bl;
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
    my ($seg, $end) = @_;

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
        print "straight on - same point\n";
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
    my $v;
    my $w;
    my $lend;
    my $phi;
    my $phideg;

    # $c1 ok still ..
    # $c2 from end of line ...
    $lend = pop @$seg;
    $c2 = $lend->{'centre'}->{'cart'};
    push @$seg, $lend;
    # $c3 is the ne point ..
    $c3 = $end->{'centre'}->{'cart'};

    $v = plane_normal($c1, $c2);
    $w = plane_normal($c2, $c3);

    $phi = acos(dot_product($v,$w));

    $phideg = $phi * 180 / $pi;

    # turned around it seems .. make new seg..
    #print "phideg=$phideg\n";
    if ($phideg > 120)
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
    
    $cart{'x'} = ($nu+$H) * $cosPhi * $cosLambda;
    $cart{'y'} = ($nu+$H) * $cosPhi * $sinLambda;
    $cart{'z'} = ((1-$eSq)*$nu + $H) * $sinPhi;

    #print 'cart=', $cart{'x'}, ' ', $cart{'y'}, ' ', $cart{'z'}, " alt=$H\n";

    return \%cart;
}

#
# Angle between two line segments ...
#
sub angle
{
    my ($s1, $s2) = @_;

}

#
# Reduce into a bunch of straight line segments.
#
sub segment_flight
{
    my ($flight) = @_;
    my $first;
    my $next;
    my $son;
    my @segment = ();

    $first = shift @$flight;
    while (defined($first))
    {
        my @track;
        my %segtr;

        @track = ();
        %segtr = ();

        # Start the line segment with 2 points (so it describes a line ...)
        push @track, $first;
        $next = shift @$flight;
        if (defined($next))
        {
            push @track, $next;
        }
        else
        {
            return \@segment;
        }

        $next = shift @$flight;
        while (defined($next))
        {

            $son = straight_on(\@track, $next);

            if ($son == 1)
            {
                # build up a straight track portion
                push @track, $next;
                $next = shift @$flight;
            }
            elsif ($son == 0)
            {
                # otherwise start a new track segment
                $first = $track[scalar @track - 1];
                unshift @$flight, $next;
                last;
            }
            else
            {
                # -1 .. ignore it ..
                $next = shift @$flight;
                if (!defined($next))
                {
                    $first = $next;
                }
            }
        }

        $segtr{'track'} = \@track;
        $segtr{'entry'} = $track[0];
        $segtr{'exit'} =  $track[scalar @track - 1];
        $segtr{'length'} = distance($segtr{'entry'}->{'centre'}, $segtr{'exit'}->{'centre'});

        push @segment, \%segtr;
    }

    return \@segment;
}

# subroutine acos
#
# input: an angle in radians
#
# output: returns the arc cosine of the angle
# description: this is needed because perl does not provide an 
#   arc cosine function

sub acos 
{
    my ($x) = @_;
    my $ret = atan2(sqrt(1 - $x**2), $x);

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
# dist = acos(res) * 111.23km
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
#   return &acos(cos($a1)*cos($b1)*cos($a2)*cos($b2) + cos($a1)*sin($b1)*cos($a2)*sin($b2) + sin($a1)*sin($a2)) * $r;
#
#   Where:
#
#    $a1 = lat1 in radians
#    $b1 = lon1 in radians
#    $a2 = lat2 in radians
#    $b2 = lon2 in radians
#    $r = radius of the earth in whatever units you want
#
# using Vincenty inverse formula for ellipsoids
#
#


sub distance
{
    my ($p1, $p2) = @_;

    # WGS-84 ellipsiod definitions
    my $a = 6378137.0;
    my $b = 6356752.3142;
    my $f = 1/298.257223563;  

    my $cosSqAlpha;
    my $sinSigma;
    my $cosSigma;
    my $sinLambda;
    my $sigma;
    my $sinAlpha;
    my $cos2SigmaM;
    my $C;

    my $L = $p2->{'long'} - $p1->{'long'};
    my $U1 = atan((1-$f) * tan($p1->{'lat'}));
    my $U2 = atan((1-$f) * tan($p2->{'lat'}));
    my $sinU1 = sin($U1);
    my $cosU1 = cos($U1);
    my $sinU2 = sin($U2);
    my $cosU2 = cos($U2);
  
    my $lambda = L, $lambdaP = 2*$pi;
    my $iterLimit = 20;

    #print "U1=$U1 U2=$U2 L=$L\n";

    while (abs($lambda-$lambdaP) > 1e-12 && --$iterLimit>0) 
    {
        $sinLambda = sin($lambda);
        $cosLambda = cos($lambda);
        $sinSigma = sqrt(($cosU2*$sinLambda) * ($cosU2*$sinLambda) + 
                        ($cosU1*$sinU2-$sinU1*$cosU2*$cosLambda) *
                        ($cosU1*$sinU2-$sinU1*$cosU2*$cosLambda));

        # co-incident points
        if ($sinSigma==0) 
        {
            return 0.0;  
        }

        $cosSigma = $sinU1*$sinU2 + $cosU1*$cosU2*$cosLambda;
        $sigma = atan2($sinSigma, $cosSigma);
        $sinAlpha = $cosU1 * $cosU2 * $sinLambda / $sinSigma;
        $cosSqAlpha = 1.0 - $sinAlpha*$sinAlpha;

        $cos2SigmaM = $cosSigma - 2*$sinU1*$sinU2/$cosSqAlpha;
        # at equatorial line -  cosSqAlpha=0 
        if (!defined($cos2SigmaM)) 
        {
            $cos2SigmaM = 0;  
        }
        $C = $f/16*$cosSqAlpha*(4+$f*(4-3*$cosSqAlpha));
        $lambdaP = $lambda;
        $lambda = $L + (1-$C) * $f * $sinAlpha *
            ($sigma + $C*$sinSigma*($cos2SigmaM+$C*$cosSigma*
                (-1+2*$cos2SigmaM*$cos2SigmaM)));
    }

    # formula failed to converge
    if ($iterLimit==0) 
    {
        return undef;  
    }

    my $uSq = $cosSqAlpha * ($a*$a - $b*$b) / ($b*$b);
    my $A = 1.0 + $uSq/16384*(4096+$uSq*(-768+$uSq*(320-175*$uSq)));
    my $B = $uSq/1024 * (256+$uSq*(-128+$uSq*(74-47*$uSq)));
    my $deltaSigma = $B*$sinSigma*
        ($cos2SigmaM+$B/4*($cosSigma* (-1.0+2*$cos2SigmaM*$cos2SigmaM) - 
            $B/6*$cos2SigmaM*(-3+4*$sinSigma*$sinSigma)*
            (-3+4*$cos2SigmaM*$cos2SigmaM)));
    my $s = $b*$A*($sigma-$deltaSigma);
    
    #s = s.toFixed(3); # round to 1mm precision
#    printf "Finding distance (%.3f): (%s,%s) (%s,%s)\n", $s, $p1->{'dlat'}, $p1->{'dlong'}, $p2->{'dlat'}, $p2->{'dlong'};
#    printf "(same) distance (%.3f): (%s,%s) (%s,%s)\n", $s, $p1->{'lat'} * 180 / $pi, $p1->{'long'} * 180 / $pi, $p2->{'lat'} * 180 / $pi, $p2->{'long'} * 180 / $pi;

    return $s;
}

#
# Work out the distance if a particular segment is proposed to be merged
#
sub reduced_distance
{
    my ($flight, $merged) = @_;
    my $i;
    my %mdist;
    my $tot;
    my $num;
    my $start;
    my $end;
    my $dist;
    my $distalt;
    my $aflag;
    my $eflag;

    $tot = 0;
    $dist = 0;
    $eflag = 0;
    $aflag = 0;
    $num = scalar @$flight;

    for ($i = 0; $i < $num-1; $i++)
    {
        if ($i == $merged)
        {
            $start = $flight->[$i]->{'entry'}->{'centre'};
            $end = $flight->[$i+1]->{'exit'}->{'centre'};
            $mdist{'start'} = $flight->[$i]->{'entry'};
            $mdist{'end'} = $flight->[$i+1]->{'exit'};
            $dist = distance($start, $end);

            # deal with the 'edge' cases'
            if ($i == 0)
            {
                # first segment 
                $distalt = $flight->[$i+1]->{'length'};
                if ($distalt > $dist)
                {
                    $dist = $distalt;
                    $mdist{'start'} = $flight->[$i+1]->{'entry'};
                    $mdist{'offhead'} = $flight->[$i]->{'entry'};
                    $aflag = 1;
                }
            }
            elsif ($i == $num-2)
            {
                # last segment 
                $distalt = $flight->[$i]->{'length'};
                if ($distalt > $dist)
                {
                    $dist = $distalt;
                    $mdist{'end'} = $flight->[$i]->{'exit'};
                    $mdist{'offtail'} = $flight->[$i+1]->{'exit'};
                }
                $eflag = 1;
            }
            $i++;
            $tot = $tot + $dist;
        }
        else
        {
            $tot = $tot + $flight->[$i]->{'length'};
        }
    }
    if ($eflag == 0)
    {
        $tot = $tot + $flight->[$num-1]->{'length'};
    }

    $mdist{'length'} = $tot;
    $mdist{'newseg'} = $dist;
    $mdist{'alt'} = $aflag;

    #print "TRY: reduced $merged length=$tot\n";

    return \%mdist;
}



#
# Find the best scoring flight and return
# the start, t1, t2, t3, finish turnpoints
# type of flight (normal, triangle, faitriangle)
# and the score
# Build line segments around 'points'
#
# This reduced many segments to the number required
# by iteratively removing the "worst" segment ..
#
sub reduce_segments
{
    my ($flight, $segments) = @_;
    my $num;
    my $i;
    my %possible;
    my %tainted;
    my @skeys;
    my $res;
    my $t1;
    my $t2;
    my @cuttail;
    my @cuthead;

    my $dist;
    my $maxd;
    my $maxc;

    $num = scalar @$flight;
    while ($num > $segments)
    {
        %possible = ();
        for ($i = 0; $i < $num-1; $i++)
        {
            $possible{$i} = reduced_distance($flight, $i);
        }

        # sort %possible ..
        # pick the largest (1st) merge and merge them ..
        # and keep doing it until we have a 'conflict'
        @skeys = reverse sort { $possible{$a}->{'length'} <=> $possible{$b}->{'length'} } keys %possible;
        #foreach my $mg ( @skeys )

        # merge two segments ..
        # check if it's a start/finish segment properly ...
        $mg = @skeys[0];
        $res = $possible{$mg};
        if (defined($res->{'offhead'}))
        {
            push @cuthead, $res->{'offhead'};
            # now go through array and find best match ..
            $maxd = $flight->[1]->{'length'};
            $maxc = $flight->[1]->{'entry'};

            foreach my $hd (@cuthead)
            {
                $dist = distance($hd->{'centre'}, $flight->[1]->{'exit'}->{'centre'});
                if ($dist > $maxd)
                {
                    $maxd = $dist;
                    $maxc = $hd;
                }
            }
            $flight->[$mg]->{'entry'} = $maxc;
        }
        else
        {
            $flight->[$mg]->{'entry'} = $res->{'start'};
        }
        if (defined($res->{'offtail'}))
        {
            my $sz;

            push @cuttail, $res->{'offtail'};
            # now go through array and find best match ..
            $sz = scalar @$flight;
            $maxd = $flight->[$sz-2]->{'length'};
            $maxc = $flight->[$sz-2]->{'exit'};
            foreach my $hd (@cuttail)
            {
                $dist = distance($hd->{'centre'}, $flight->[$sz-2]->{'entry'}->{'centre'});
                print "tail dist=$dist (v $maxd)\n";
                if ($dist > $maxd)
                {
                    $maxd = $dist;
                    $maxc = $hd;
                }
            }
            $flight->[$mg]->{'exit'} = $maxc;
        }
        else
        {
            $flight->[$mg]->{'exit'} = $res->{'end'};
        }
        $flight->[$mg]->{'length'} = $res->{'newseg'};
        $t1 = $flight->[$mg]->{'track'};
        $t2 = $flight->[$mg+1]->{'track'};
        $flight->[$mg]->{'track'} = @$t1, @$t2;

        splice @$flight, $mg+1, 1;
        $num--;
        print "reducing ($mg) to $num, new length=", $res->{'length'}, " (", $res->{'alt'}, ")\n";
        #print "length after reduction=", scalar @$flight, "\n";
    }

    #print "length after reduction=", scalar @$flight, "\n";

    return $flight;
}

#
# Given a flight and a line segment description 
# and the first / last points to use in that segment
# find the maximal midpoint 
#
sub maximise_midpoint
{
    my ($flight, $existing, $f, $l) = @_;
    my $i;
    my $first;
    my $last;
    my $maxseg;
    my $maxlen;
    my $newlen;
    my %maxdist;

    $first = $existing->[$f];
    $last = $existing->[$l];

    $maxseg = -1;
    $maxlen = 0;

    #print " mmidpoint: first($f)=$first last($l)=$last\n";
    # sanity check
    if (($last - $first) < 2)
    {
        $maxdist{'length'} = 0;
        $maxdist{'segment'} = -1;

        return \%maxdist;
    }

    for ($i = $first+1; $i < $last; $i++)
    {
        $newlen = distance($flight->[$first]->{'entry'}->{'centre'}, $flight->[$i]->{'entry'}->{'centre'}) 
                + distance($flight->[$i]->{'entry'}->{'centre'}, $flight->[$last]->{'entry'}->{'centre'});
        if ($newlen > $maxlen)
        {
            $maxlen = $newlen;
            $maxseg = $i;
        }
    }

    $maxdist{'segment'} = $maxseg;
    $maxlen = 0;
    splice(@$existing, $f+1, 0, $maxseg);
    for ($i = 0; $i < (scalar @$existing - 1); $i++)
    {
       $maxlen = $maxlen +  
            distance($flight->[$existing->[$i]]->{'entry'}->{'centre'},
                     $flight->[$existing->[$i+1]]->{'entry'}->{'centre'});
    }
    splice(@$existing, $f+1, 1);

    $maxdist{'length'} = $maxlen;
    #print "max_dist $f max=$maxseg length=$maxlen\n";
    return \%maxdist;
}

#
# find a good endpoint 
#
sub maximise_endpoint
{
    my ($flight, $existing) = @_;
    my $i;
    my $first;
    my $last;
    my $maxseg;
    my $maxlen;
    my $newlen;
    my %maxdist;

    $maxseg = -1;
    $maxlen = 0;

    # sanity check

    $first = $existing->[scalar @$existing-1];
    $last = scalar @$flight-1;

    #print " mendpoint: first=$first last=$last\n";

    if (($last - $first) < 2)
    {
        $maxdist{'length'} = 0;
        $maxdist{'segment'} = -1;

        return \%maxdist;
    }

    for ($i = $first+1; $i < $last; $i++)
    {
        $newlen = distance($flight->[$first]->{'entry'}->{'centre'}, $flight->[$i]->{'entry'}->{'centre'}) 
                + distance($flight->[$i]->{'entry'}->{'centre'}, $flight->[$last]->{'entry'}->{'centre'});
        if ($newlen > $maxlen)
        {
            $maxlen = $newlen;
            $maxseg = $i;
        }
    }

    $maxdist{'segment'} = $maxseg;
    for ($i = 0; $i < (scalar @$existing - 1); $i++)
    {
       $maxlen = $maxlen +  
            distance($flight->[$existing->[$i]]->{'entry'}->{'centre'},
                     $flight->[$existing->[$i+1]]->{'entry'}->{'centre'});
    }

    $maxdist{'length'} = $maxlen;
    #print "mendpoint max_dist $f max=$maxseg length=$maxlen\n";
    return \%maxdist;
}

#
# Does the reverse .. pick the endpoints and tries to find 
# best endpoints increasing by 1 each time ...
#
sub select_segments
{
    my ($flight, $segments) = @_;

    my %tempseg;
    my $num;
    my $dist;
    my $i;
    my $j;
    my $k;
    my @skeys;
    my @tmparr;
    my @selected;
    my @selectsegs;

    my $startseg;
    my $maxstartdist;

    my $endseg;
    my $maxenddist;

    # we're actually picking 'points' - build segments at the end
    $segments++;
    $num = scalar @$flight;

    # add a temporary point to flight since we're working with 
    # only 'entry' points to segments ..
    $tempseg{'entry'} = $flight->[$num-1]->{'exit'};
    $tempseg{'exit'} = $flight->[$num-1]->{'exit'};
    $tempseg{'length'} = 0;
    push @$flight, \%tempseg;
    $num++;

    # we picked arbitrary start/end points .. try to pick better ones ..
    @tmparr = ( 0, $num-1 );
    $i = maximise_midpoint($flight, \@tmparr, 0, 1);
    $midseg = $i->{'segment'};

    # now find new better endpoints ...
    $maxstartdist = 0;
    for ($i = 0; $i < $midseg; $i++)
    {
        $dist = distance($flight->[$i]->{'entry'}->{'centre'}, $flight->[$midseg]->{'entry'}->{'centre'});
        if ($dist > $maxstartdist)
        {
            $maxstartdist = $dist;
            $startseg = $i;
        }
    }
    $maxenddist = 0;
    for ($i = $midseg+1; $i < $num; $i++)
    {
        $dist = distance($flight->[$midseg]->{'entry'}->{'centre'}, $flight->[$i]->{'entry'}->{'centre'});
        if ($dist > $maxenddist)
        {
            $maxenddist = $dist;
            $endseg = $i;
        }
    }

    #print "best (from $midseg) start/end $startseg, $endseg\n";

    # and restart with better end points ..
    push @selected, $startseg;
    push @selected, $endseg;

    while (scalar @selected < $segments)
    {
        $num = scalar @selected;
        %possible = ();
        for ($i = 0; $i < $num-1; $i++)
        {
            # fix: need to get total track length with new midpoint ..
            $possible{$i} = maximise_midpoint($flight, \@selected, $i, $i+1);
        }
        # insert/choose a new/better endpoints as alternatives here too
        #if ($selected[0] > 0)
        #{
        #    #@tmparr = ( 0, $selected[0] );
        #    $possible{-1} = maximise_midpoint($flight, \@tmparr, 0, 1);
        #    #print " start=$num len=" . $possible{-1}->{'length'} . "\n";
        #}

        # this should be a maximise endpoint function ...
        if ((scalar @selected < $segments-1)
             && ($selected[$num-1] < scalar @$flight))
        {
            $possible{$num} = maximise_endpoint($flight, \@selected);
            #push @selected, scalar @$flight-1;
            #$possible{$num} = maximise_midpoint($flight, \@selected, $num-1, $num);
            #pop @selected;
            #print " end=$num len=" . $possible{$num}->{'length'} . 
            #    " seg=" . $possible{$num}->{'segment'} . "\n";
        }

        @skeys = reverse sort { $possible{$a}->{'length'} <=> $possible{$b}->{'length'} } keys %possible;

        #foreach my $seg (keys %possible)
        #{
        #    print " len=" . $possible{$seg}->{'length'} . 
        #        " seg=" . $possible{$seg}->{'segment'} . "\n";
        #}

        # find the best and insert ...
        $mg = $skeys[0];
        #print "splicing: $mg with " . $possible{$mg}->{'segment'} . "\n";
        splice(@selected, $mg+1, 0, $possible{$mg}->{'segment'});

        # FIX: special case if we added a new end/start 
        # need to recompute a better midpoint ...
        if ($mg == $num)
        {
            $replseg = maximise_midpoint($flight, \@selected, $num-2, $num);
            #print "replacing " . $selected[$num-1] . 
            #    " with " . $replseg->{'segment'} . "\n";
            $selected[$num-1] = $replseg->{'segment'};
        }
    }

    # return actual segments in a list rather than indices?
    $num = scalar @selected;
    for ($i = 0; $i < $num-1; $i++)
    {
        my $newseg;
        my $len;

        #print "seg $i: " . $selected[$i] . "\n";

        $newseg = ();
        $newseg->{'entry'} = $flight->[$selected[$i]]->{'entry'};
        $newseg->{'exit'} = $flight->[$selected[$i+1]]->{'entry'};
        $len = distance($newseg->{'entry'}->{'centre'},
                                        $newseg->{'exit'}->{'centre'});
        $newseg->{'length'} = $len;

        push @selectsegs, $newseg;
    }
    #print "seg $i: " . $selected[$i] . "\n";

    # restore $flight
    pop @$flight;

    return \@selectsegs;
}

# 
# Search through the "middle" (exit) bucket to find the locally
# "best" point to be the 'centre' for distance and set it
#
# Need to fix for entry/exit is the same point in segments?
#
sub maximise_dist
{
    my ($entry, $exit, $nextend) = @_;
    my $d1;
    my $sz;
    my $bucket;
    my $maxdist;
    my $largest;

    $bucket = $exit->{'bucket'};
    $maxdist = 0;
    foreach my $p2 (@$bucket)
    {
        $d1 = distance($entry->{'centre'}, $p2);
        if ($nextend)
        {
            $d1 = $d1 + distance($p2, $nextend->{'centre'});
        }
        if ($d1 > $maxdist)
        {
            $maxdist = $d1;
            $largest = $p2;
        }
    }
    
    # just set the new centre?
    $exit->{'centre'} = $largest;
    return $largest;
}

#
# Find the best 'centre' to maximise lengths of two segments ..
#
sub optimise_waypoints
{
    my ($flight) = @_;
    my $i;
    my $num;
    my $newcentre;

    $num = scalar @$flight;

    for ($i = 0; $i < $num; $i++)
    {
        if ($i == 0)
        {
           # find best point to start (to seg exit). 
           $newcentre = maximise_dist($flight->[$i]->{'exit'}, $flight->[$i]->{'entry'}, 0);

        }
        elsif ($i == $num-1)
        {
           $newcentre = maximise_dist($flight->[$i]->{'entry'}, $flight->[$i]->{'exit'}, 0);
        }
        else
        {
           $newcentre = maximise_dist($flight->[$i]->{'entry'}, $flight->[$i]->{'exit'}, $flight->[$i+1]->{'exit'});
        }

        $flight->[$i]->{'length'} = distance($flight->[$i]->{'entry'}->{'centre'}, $flight->[$i]->{'exit'}->{'centre'});
    }

    return $flight;
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

    for ($i = 0; $i < $sz; $i++)
    {
        $seg = $track->[$i]->{'centre'}->{'cart'};
        $seg1 = $track->[($i+1)%$sz]->{'centre'}->{'cart'};

        $totarea = $totarea + 
            ($seg->{'x'}*$seg1->{'y'} - $seg1->{'x'}*$seg->{'y'})
    }

    # 'closing' segment (maybe 0)
    $seg = $track->[$sz-1]->{'centre'}->{'cart'};
    $seg1 = $track->[0]->{'centre'}->{'cart'};
    $totarea = $totarea + 
            ($seg->{'x'}*$seg1->{'y'} - $seg1->{'x'}*$seg->{'y'});

    $totarea = 0.5 * $totarea;

    return $totarea;
}

sub score_track
{
    my ($track,$totlen) = @_;
    my $totlen;
    my $polarea;
    my $ascore;
    my $gap;
    my $sz;
    
    $totlen=0;
    foreach my $seg (@$track)
    {
        #print Dumper($seg);
        $totlen = $totlen + $seg->{'length'};
    }

    # check if "closed" (20% leeway) ..
    $sz = scalar @$track;
    $gap = distance($track->[0]->{'entry'}->{'centre'}, $track->[$sz-1]->{'exit'}->{'centre'});
    print "scoring: gap=$gap totlen=$totlen\n";
    if (($gap/$totlen) < 0.2)
    {
        $polarea = polygon_area($track);
        $ascore = (1.5 + (4*$PI*$polarea) / ($totlen*$totlen)) * $totlen - $gap;
        if ($ascore > $totlen)
        {
            return $ascore;
        }
    }

    return $totlen;
}

sub flight_duration
{
    my ($full) = @_;
    my $start;
    my $end;
    my $len;
    

#    $full = $flight->{'coords'};

#    foreach my $coord (@$full)
#    {
#    }

    $len = scalar @$full;
    if ($len < 1)
    {
        print "Something wrong with coord list\n";
        return 0;
    }
    $end = $full->[$len-1]->{'time'};
    $start = $full->[0]->{'time'};

    # or $last_time - $first_time?

    return $end - $start;
}

#
# Main program here ..
#

my $flight;
my $allflights;
my $traPk;
my $totlen = 0;
my $coords;
my $numc;
my $numb;
my $score;
my $duration;
my $pilPk;

db_connect();

# Read the flight
$pilPk = 0 + $ARGV[1];
$flight = read_igc($ARGV[0]);
$coords = $flight->{'coords'};
$numc = scalar @$coords;
print "num coords=$numc\n";

# Is it a duplicate (and other checks)?
$sth = $dbh->prepare("select traPk from tblTrack where pilPk=? and traDate=?");
$sth->execute($pilPk, $flight->{'header'}->{'date'});
$traPk = $sth->fetchrow_array();
if (defined($traPk))
{
    # it's a duplicate ...
    print "duplicate track found\n";
    print "traPk=$traPk\n";
    exit(1);
}

# Trim off silly points ...
$flight = trim_flight($flight, $pilPk);

# Work out flight duration
$duration = flight_duration($coords);
print "flight duration=$duration secs\n";

# Reduce into buckets
$reduced = reduce_flight($flight, $pilPk);
$numb = scalar @$reduced;
print "num buckets=$numb\n";

$traPk = $flight->{'traPk'};
print "reduced: traPk=$traPk\n";
store_buckets($traPk, $reduced);


# Reduce into line segments
$segmented = segment_flight($reduced);
print "Number of unreduced segments=", scalar @$segmented, "\n";
#store_waypoints($traPk, $segmented);

# Ok .. work out total length
foreach my $seg (@$segmented)
{
    #print Dumper($seg);
    $totlen = $totlen + $seg->{'length'};
}
print "Total flight length of un-reduced segments=$totlen\n";
store_segments($traPk, $segmented);

# Reduce segments to numbers of required segments
$segmented = select_segments($segmented,4);
$segmented = optimise_waypoints($segmented);
print "Number of reduced segments=", scalar @$segmented, "\n";
store_waypoints($traPk, $segmented);

# Ok .. output flight segments for a looksy
$totlen=0;
foreach my $seg (@$segmented)
{
    #print Dumper($seg);
    #print "seg=", $seg->{'length'}, "\n";
    $totlen = $totlen + $seg->{'length'};
}

#print Dumper($segmented);
$score = score_track($segmented,$totlen);

print "Total flight length of reduced segments=$totlen\n";
$dbh->do("update tblTrack set traLength=?, traDate=?, traScore=?, traDuration=? where traPk=?",
    undef, $totlen, $flight->{'header'}->{'date'}, $score, $duration, $traPk);

print "traPk=$traPk\n";
# Ok .. score it now ..
#
# Just absolute distance unless 
# final waypoint within 20% of length of start waypoint
# then work out area enclosed ...
#




