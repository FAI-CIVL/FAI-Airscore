#!/usr/bin/perl
#
# Reads in a .sua airspace file
#
#

require DBD::mysql;
use Data::Dumper;

my $database = '%DATABASE%';
my $hostname = '%MYSQLHOST%';
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
    $dbh = DBI->connect( $dsn, '%MYSQLUSER%', '%MYSQLPASSWORD%', { RaiseError => 1 } )
            or die "Can't connect: $!\n";
    $drh = DBI->install_driver("mysql");
}

sub parselatlong
{
    my ($f1, $f2) = @_;
    my @arr;
    my ($lat, $lon);
    my %point;

    @arr = split /=/, $f1;
    if ($arr[0] eq 'CENTRE')
    {
        $f1 = $arr[1];
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
    $point{'style'} = 'line';
    return \%point;
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
    my $points;
    my $row;
    my $rec;

    print "reading: $f\n";
    open(FD, "$f") or die "can't open $f: $!";

    $points = [];
    $rec = {};
    $rec->{'shape'} = 'polygon';

    while (<FD>)
    {

        $row = $_;
        chomp $row;
        @field = split /=/, $row;

        if ($field[0] eq "INCLUDE")
        {
            # new record?
            if (defined($rec->{'class'}))
            {
                $rec->{'points'} = $points;
                push @regions, $rec;
                # store it into the database?

                $points = [];
                $rec = {};
                $rec->{'shape'} = 'polygon';
            }
        }
        elsif ($field[0] eq "TITLE")
        {
            chop $field[1];
            $rec->{'name'} = $field[1];
        }
        elsif ($field[0] eq "CLASS")
        {
            chop $field[1];
            $rec->{'class'} = $field[1];
        }
        elsif ($field[0] eq "BASE")
        {
            $rec->{'base'} = (0+$field[1]) / 3.28;
        }
        elsif ($field[0] eq "TOPS")
        {
            if (substr($field[1],0,2) eq "FL")
            {
                $rec->{'tops'} = (0+substr($field[1],2))*100 / 3.28;
            }
            else
            {
                $rec->{'tops'} = (0+$field[1]) / 3.28;
            }
        }
        elsif ($field[0] eq "POINT")
        {
            # build a list ...
            my $point;
            @rest = split / /, $field[1];

            $point = parselatlong($rest[0], $rest[1]);
            #print Dumper($point);
            push @$points, $point;
        }
        elsif ($field[0] eq "CLOCKWISE RADIUS")
        {
            @rest = split / /, $field[2];
            $rec->{'radius'} = (0+$field[1]) * 1852;   # nmiles -> m
            $point = parselatlong($rest[0], $rest[1]);
            $point->{'style'} = 'arc';
            push @$points, $point;
            $rec->{'shape'} = 'wedge';
        }
        elsif ($field[0] eq "ANTI-CLOCKWISE RADIUS")
        {
            # FIX: need to reverse point list if we're anti (sigh)
            @rest = split / /, $field[2];
            $rec->{'radius'} = (0+$field[1]) * 1852;   # nmiles -> m
            $point = parselatlong($rest[0], $rest[1]);
            $point->{'style'} = 'arc';
            push @$points, $point;
        }
        elsif ($field[0] eq "CIRCLE RADIUS")
        {
            @rest = split / /, $field[2];
            $rec->{'radius'} = (0+$field[1]) * 1852;   # nmiles -> m
            $point = parselatlong($rest[0], $rest[1]);
            push @$points, $point;
            $rec->{'shape'} = 'circle';
        }
    }

    $rec->{'points'} = $points;
    push @regions, $rec;


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

    for my $air ( @$regions )
    {
        #print "del ", $air->{'name'}, "\n";
        $dbh->do("delete from tblAirspace where airName=? and airClass=? and airBase=? and airTops=?", undef,
            $air->{'name'}, $air->{'class'}, $air->{'base'}, $air->{'tops'});
        print "insert ", $air->{'name'}, "\n";
        $dbh->do("insert into tblAirspace (airName,airClass,airBase,airTops,airShape,airRadius) values (?,?,?,?,?,?)", undef,
            $air->{'name'}, $air->{'class'}, $air->{'base'}, $air->{'tops'}, $air->{'shape'}, $air->{'radius'});
        $id = $dbh->last_insert_id(undef, undef, "tblAirspace", undef);
        $count = 0;
        $pts = $air->{'points'};
        for my $wp ( @$pts )
        {
            print "insert wp ", $air->{'name'}, "\n";
            #print Dumper($wp);
            $dbh->do("insert into tblAirspaceWaypoint (airPk, airOrder, awpLatDecimal, awpLongDecimal, awpConnect) values (?,?,?,?,?)", undef, $id, $count, 0.0 + $wp->{'lat'}, 0.0 + $wp->{'lon'}, $wp->{'style'});
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
$airspace = read_airspace($ARGV[0]);
print Dumper($airspace);
store_airspace($airspace);


