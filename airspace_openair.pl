#!/usr/bin/perl 

#
# Reads in an OpenAir airspace file
#
#

require DBD::mysql;
use Data::Dumper;
use Defines qw(:all);

my $port = 3306;

$pi = atan2(1,1) * 4;    # accurate PI.
local * FD;

#
# Database handles
#

my $dsn;
my $dbh;
my $drh;

sub db_connect
{
    $dsn = "DBI:mysql:database=$DATABASE;host=$MYSQLHOST;port=$port";
    $dbh = DBI->connect( $dsn, $MYSQLUSER, $MYSQLPASSWORD, { RaiseError => 1 } )
            or die "Can't connect: $!\n";
    $drh = DBI->install_driver("mysql");
}


# 
# Don't bother with great circle for checking
# Calculate angle described by a line made by two points
# $p1 = origin
sub cart_angle
{
    my ($p1, $p2);
    my ($x,$y);

    $x = $p2->{'cart'}->{'x'} - $p1->{'cart'}->{'x'};
    $y = $p2->{'cart'}->{'y'} - $p1->{'cart'}->{'y'};

    return atan2($x,$y);
}


sub parselatlong
{
    my ($f1, $f2) = @_;
    my @arr;
    my ($lat, $lon);
    my %point;

    $point{'shape'} = 'line';

    @arr = split /=/, $f1;
    if ($arr[0] eq 'CENTRE')
    {
        $f1 = $arr[1];
        $point{'shape'} = 'arc';
    }

    $lat = (0+substr($f1,1,2)) + (0+substr($f1,3,2) / 60) + (0+substr($f1,5,2) / 3600);
    if (substr($f1,0,1) eq "S")
    {
        $lat = -$lat;
    }
    $lon = (0+substr($f2,1,3)) + (0+substr($f2,4,2) / 60) + (0+substr($f2,6,2) / 3600);
    if (substr($f2,0,1) eq "W")
    {
        $lon = -$lon;
    }

    #print "f1=$f1 f2=$f2 lat=$lat lon=$lon\n";
    $point{'lat'} = $lat;
    $point{'lon'} = $lon;

    # calculate radius / angle?

    return \%point;
}

sub oalatlong
{
    my ($f1, $f2) = @_;
    my @arr;
    my ($lat, $lon);
    my %point;

    @arr = split(/:/, $f1);
    $lat = (0+substr($arr[0],1)) + (0+$arr[1]/60) + (0.0+$arr[2])/ 3600;
    if (substr($arr[0],0,1) eq "S")
    {
        $lat = -$lat;
    }

    @arr = split(/:/, $f2);
    $lon = (0+substr($arr[0],1)) + (0+$arr[1]/60) + (0.0+$arr[2])/ 3600;
    if (substr($f2,0,1) eq "W")
    {
        $lon = -$lon;
    }

    #print "f1=$f1 f2=$f2 lat=$lat lon=$lon\n";
    $point{'lat'} = $lat;
    $point{'lon'} = $lon;

    # calculate radius / angle?

    return \%point;
}

sub torad
{
    my ($v) = @_;
    return $v * $pi / 180;
}

sub bearing
{
    my ($p1, $p2) = @_;
    my ($x, $y);
    my ($lat1, $lat2);
    my $dLon;
    my $brng;

    #$dLat = torad($p2->{'lat'}-$p1->{'lat'}).toRad();
    #print Dumper($p2);
    $dLon = torad($p2->{'lon'}-$p1->{'lon'});
    $lat1 = torad($p1->{'lat'});
    $lat2 = torad($p2->{'lat'});

    $y = sin($dLon)*cos($lat2);
    $x = cos($lat1)*sin($lat2) - sin($lat1)*cos($lat2)*cos($dLon);

    $brng = atan2($y, $x);

    # convert back to degree?
    print "bearing=" . ($brng*180/$pi) . "\n";

    return $brng;
}

#****** OPEN AIR (tm) TERRAIN and AIRSPACE DESCRIPTION LANGUAGE *************
#    Version 1.0
#    December 10, 1998
#    Updated October 15, 1999
#
#  AIRSPACE related record types:
#  ==============================
#
# AC class    ;    class = Airspace Class, see below:
#     R restricted
#     Q danger
#     P prohibited
#     A Class A
#     B Class B
#     C Class C
#     D Class D
#     GP glider prohibited
#     CTR CTR
#     W Wave Window
#
#
#  AN string        ;     string = Airspace Name
#  AH string        ;     string = Airspace Ceiling
#  AL string        ;     string = Airspace Floor
#  AT coordinate    ;    coordinate = Coordinate of where to place a name label on the map (optional)
#                     ;     NOTE: there can be multiple AT records for a single airspace segment
#   
#   
#    TERRAIN related record types (WinPilot version 1.130 and newer):
#    ==============================
#
#    TO    {string}                 ; Declares Terrain Open Polygon; string = name (optional)
#    TC    {string}                 ; Declares Terrain Closed Polygon; string = name (optional)
#    SP style, width, red, green, blue    ; Selects Pen to be used in drawing
#    SB red, green, blue                         ; Selects Brush to be used in drawing
#
#
#    Record types common to both TERRAIN and AIRSPACE
#    =================================================
#
#    V x=n             ;     Variable assignment.
#                     ;     Currently the following variables are supported:
#                     ;     D={+|-}    sets direction for: DA and DB records
#                     ;                     '-' means counterclockwise direction; '+' is the default
#                     ;                     automatically reset to '+' at the begining of new airspace segment   
#                     ;     X=coordinate    : sets the center for the following records: DA, DB, and DC   
#                     ;     W=number        : sets the width of an airway in nm (NYI)
#                     ;      Z=number         : sets zoom level at which the element becomes visible (WP version 1.130 and newer)
#
#    DP coordinate                     ; add polygon pointC
#    DA radius, angleStart, angleEnd    ; add an arc, angles in degrees, radius in nm (set center using V X=...)
#    DB coordinate1, coordinate2         ; add an arc, from coordinate1 to coordinate2 (set center using V X=...)
#    DC radius                         ; draw a circle (center taken from the previous V X=...  record, radius in nm
#    DY coordinate                     ; add a segment of an airway (NYI)

sub read_openair
{
    my ($f) = @_;

    my @field;
    my @rest;
    my @regions;
    my $points;
    my $row;
    my $rec;
    my $dirn;
    my $centre;
    my $last;
    my $lastfield;
    my $point2;

    print "reading: $f\n";
    open(FD, "$f") or die "can't open $f: $!";
    $dirn = '+';
    $rec = {};
    $points = [];

    while (<FD>)
    {
        $row = $_;
        chomp $row;
        @field = split /[ ]+/, $row;

        if ($field[0] eq "AN")
        {
            @field = split / /, $row, 2;
            $rec->{'name'} = $field[1];
        }
        elsif ($field[0] eq "AC")
        {
            # new record?
            if (exists $rec->{'class'})
            {
                #if ($lastfield eq "DB")
                #{
                #    push @$points, $last;
                #}
                $rec->{'points'} = $points;
                push @regions, $rec;
                # store it into the database?

                $points = [];
                $rec = {};
                $rec->{'shape'} = 'polygon';
                $rec->{'class'} = $field[1];
            }
            $rec->{'class'} = $field[1];
            $dirn = '+';
        }
        elsif ($field[0] eq "AL")
        {
            if (substr($field[1],0,2) eq "FL")
            {
                $rec->{'base'} = int(0.5 + (0+substr($field[1],2))*100 / 3.28);
            }
            else
            {
                $rec->{'base'} = int(0.5 + (0+$field[1]) / 3.28);
            }
        }
        elsif ($field[0] eq "AH")
        {
            if (substr($field[1],0,2) eq "FL")
            {
                $rec->{'tops'} = int(0.5 + (0+substr($field[1],2))*100 / 3.28);
            }
            else
            {
                $rec->{'tops'} = int(0.5 + (0+$field[1]) / 3.28);
            }
        }
        elsif ($field[0] eq "DP")
        {
            # build a list ...
            my $point;
            $point = oalatlong($field[2] . $field[1], $field[4] . $field[3]);

            if (defined($last))
            {
                # ignore wedge duplicate
                if (($last->{'lat'} == $point->{'lat'}) and ($last->{'lon'} == $point->{'lon'}))
                {
                    print("Ignoring duplicate point\n");
                    next;
                }
            }

            $last = $point;
            push @$points, $point;
            #if ($dirn eq '+')
            #{
            #    push @$points, $point;
            #}
            #else
            #{
            #    unshift @$points, $point;
            #}
        }
        elsif ($field[0] eq "DA")
        {
            # radius, angle from, angle to
        }
        elsif ($field[0] eq "DB")
        {
            # radius, point to point
            my $point;
            my $point3;
            my ($a1,$a2);
            my @carr;

            $rec->{'shape'} = 'wedge';

            $field[4] = substr($field[4], 0, 1);
            $point = oalatlong($field[2] . $field[1], $field[4] . $field[3]);
            #$point->{'radius'} = $rec->{'radius'};

            # handle the associated point
            @carr = split /,[ ]*/, $row, 2;
            @rest = split /[ ]+/, $carr[1];
            $rest[3] = substr($rest[3], 0, 1);

            $point3 = oalatlong($rest[1] . $rest[0], $rest[3] . $rest[2]);

            $point2 = $centre;
            $a1 = bearing($point2, $point);
            $a2 = bearing($point2, $point3);
            $point2->{'astart'} = $a1;
            $point2->{'aend'} = $a2;


            if ($dirn eq '-')
            {
                $point2->{'connect'} = 'arc-';
            }
            else
            {
                $point2->{'connect'} = 'arc+';
            }

            if ( ($last->{'connect'} eq 'arc-' || $last->{'connect'} eq 'arc+')
                || !(($last->{'lat'} == $point->{'lat'}) and ($last->{'lon'} == $point->{'lon'})))
            {
                push @$points, $point;
            }
            push @$points, $point2;

            $last = $point2;
        }
        elsif ($field[0] eq "V")
        {
            #print Dumper(\@field);
            if (substr($field[1],0,1) eq "X")
            {
                # set center of following description 
                $centre = oalatlong($field[2] . substr($field[1],2), $field[4] . $field[3]);
                #$rec->{'centreto'} = oalatlong($field[2] . substr($field[1],2), $field[4] . $field[3]);
            
            }
            elsif (substr($field[1],0,1) eq "D")
            {
                # clockwise description
                $dirn = substr($field[1],2,1);
            }
        }
        elsif ($field[0] eq "DC")
        {
            $rec->{'centreto'} = $centre;
            $rec->{'radius'} = $field[1] * 1852;   # Nautical Miles
            $rec->{'shape'} = 'circle';
        }

        $lastfield = $field[0];
    }

    #if ($lastfield eq "DB")
    #{
    #    push @$points, $last;
    #}

    $rec->{'points'} = $points;

    push @regions, $rec;

    #print Dumper(\@regions);
    return \@regions;
}


#
# Extract 'fix' data into a nice record
#
sub read_airspace
{
    my ($f) = @_;

    my @field;
    my @rest;
    my @regions;
    my @points;
    my $row;
    my %rec;
    my $lastpoint;
    my ($a1, $a2);

    print "reading: $f\n";
    open(FD, "$f") or die "can't open $f: $!";

    while (<FD>)
    {

        $row = $_;
        chomp $row;
        @field = split /=/, $row;

        if ($field[0] eq "INCLUDE")
        {
            # new record?
            if ($rec{'class'} ne '')
            {
                my %newrec;
                my @newpoints;

                @newpoints = @points;
                $rec{'points'} = \@newpoints;
                %newrec = %rec;
                push @regions, \%newrec;
                # store it into the database?

                @points = ();
                %rec = ();
                $rec{'shape'} = 'polygon';
            }
        }
        elsif ($field[0] eq "TITLE")
        {
            $rec{'name'} = $field[1];
        }
        elsif ($field[0] eq "CLASS")
        {
            $rec{'class'} = $field[1];
        }
        elsif ($field[0] eq "BASE")
        {
            $rec{'base'} = int(0.5+(0+$field[1]) / 3.28);
        }
        elsif ($field[0] eq "TOPS")
        {
            if (substr($field[1],0,2) eq "FL")
            {
                $rec{'tops'} = int(0.5+(0+substr($field[1],2))*100 / 3.28);
            }
            else
            {
                $rec{'tops'} = int(0.5+(0+$field[1]) / 3.28);
            }
        }
        elsif ($field[0] eq "POINT")
        {
            # build a list ...
            my $point;
            @rest = split / /, $field[1];

            $point = parselatlong($rest[0], $rest[1]);
            push @points, $point;
            $lastpoint = $point;
        }
        elsif ($field[0] eq "CLOCKWISE RADIUS")
        {
            @rest = split / /, $field[2];
            $rec{'radius'} = (0+$field[1]) * 1000;   # FIX?
            $rec{'centre'} = parselatlong($rest[0], $rest[1]);
            @rest = split / /, $field[3];
            $rec{'centreto'} = parselatlong($rest[0], $rest[1]);
            $rec{'shape'} = 'wedge';
            # handle the associated points
            my $point;
            @rest = split / /, $field[1];
            $point = parselatlong($rest[0], $rest[1]);
            $point->{'radius'} = $rec{'radius'};

            # perhaps calculate angle-in / angle-out?
            $a1 = cart_angle($rec{'centre'}, $lastpoint);
            $a2 = cart_angle($rec{'centre'}, $point);

            $point->{'astart'} = $a1;
            $point->{'aend'} = $a2;

            push @points, $point;
        }
        elsif ($field[0] eq "ANTI-CLOCKWISE RADIUS")
        {
            @rest = split / /, $field[2];
            $rec{'radius'} = $rest[0] * 1000;   # FIX?
            $rec{'centre'} = parselatlong($rest[0], $rest[1]);
            @rest = split / /, $field[3];
            $rec{'centreto'} = parselatlong($rest[0], $rest[1]);
            # handle the associated points
        }
        elsif ($field[0] eq "CIRCLE RADIUS")
        {
            @rest = split / /, $field[2];
            $rec{'radius'} = $rest[0] * 1000;   # FIX?
            $rec{'centre'} = parselatlong($rest[0], $rest[1]);
            @rest = split / /, $field[3];
            $rec{'centreto'} = parselatlong($rest[0], $rest[1]);
            $rec{'shape'} = 'circle';
        }
    }

    $rec{'points'} = \@points;
    push @regions, \%rec;


    return \@regions;
}

#
# Limited straight-line polygon store at the moment ...
# Should actually store the circle arcs for wedges
#
sub store_airspace
{
    my ($regions) = @_;
    my $id;
    my $count;
    my $pts;
    my $cwp;
    my $sth;

    for my $air ( @$regions )
    {
        #print "select * from tblAirspace where airName='" . $air->{'name'} . "' and airClass='" . $air->{'class'} . "' and airBase=" . $air->{'base'} . " and airTops=" . $air->{'tops'} . "\n";
        $sth = $dbh->prepare("select * from tblAirspace where airName='" . $air->{'name'} . "' and airClass='" . $air->{'class'} . "' and airBase=" . $air->{'base'} . " and airTops=" . $air->{'tops'});
        $sth->execute();
        if ($ref = $sth->fetchrow_hashref())
        {
            print "del ", $ref->{'airName'}, "\n";
            $dbh->do("delete from tblAirspaceWaypoint where airPk=?", undef, $ref->{'airPk'});
            $dbh->do("delete from tblAirspace where airPk=?", undef, $ref->{'airPk'});
        }

        # AirspaceWaypoint too?
        print "insert ", $air->{'name'}, "\n";
        $dbh->do("insert into tblAirspace (airName,airClass,airBase,airTops,airShape) values (?,?,?,?,?)", undef, $air->{'name'}, $air->{'class'}, $air->{'base'}, $air->{'tops'}, $air->{'shape'});
        $id = $dbh->last_insert_id(undef, undef, "tblAirspace", undef);
        $count = 0;

        if (defined($air->{'centreto'}))
        {
            $wp = $air->{'centreto'};
            $dbh->do("insert into tblAirspaceWaypoint (airPk, airOrder, awpLatDecimal, awpLongDecimal) values (?,?,?,?)", undef, $id, $count, 0.0 + $wp->{'lat'}, 0.0 + $wp->{'lon'});
            $cwp = $dbh->last_insert_id(undef, undef, "tblAirspaceWaypoint", undef);
            $dbh->do("update tblAirspace set airCentreWP=?, airRadius=? where airPk=?", undef, $cwp, $air->{'radius'}, $id);
            $count++;
        }

        $pts = $air->{'points'};
        for my $wp ( @$pts )
        {
            #print "insert wp ", $air->{'name'}, "\n";
            #print Dumper($wp);
            if ($wp->{'connect'} eq 'arc+' or $wp->{'connect'} eq 'arc-')
            {
                $dbh->do("insert into tblAirspaceWaypoint (airPk, airOrder, awpLatDecimal, awpLongDecimal, awpConnect, awpAngleStart, awpAngleEnd) values (?,?,?,?,?,?,?)", undef, $id, $count, 0.0 + $wp->{'lat'}, 0.0 + $wp->{'lon'}, $wp->{'connect'}, $wp->{'astart'}, $wp->{'aend'});
            }
            else
            {
                $dbh->do("insert into tblAirspaceWaypoint (airPk, airOrder, awpLatDecimal, awpLongDecimal) values (?,?,?,?)", undef, $id, $count, 0.0 + $wp->{'lat'}, 0.0 + $wp->{'lon'});
            }
            $count++;
        }

    }
}


#
# Main program here ..
#

my $airspace;

db_connect();

# Read the airspace file
$airspace = read_openair($ARGV[0]);
#print Dumper($airspace);
store_airspace($airspace);


