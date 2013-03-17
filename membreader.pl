#!/usr/bin/perl

#
# Reads in a CSV membership list
#
#

require DBD::mysql;
use Data::Dumper;
use Defines qw(:all);

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
    $dsn = "DBI:mysql:database=$DATABASE;host=$MYSQLHOST;port=$port";
    $dbh = DBI->connect( $dsn, $MYSQLUSER, $MYSQLPASSWORD, { RaiseError => 1 } )
            or die "Can't connect: $!\n";
    $drh = DBI->install_driver("mysql");
}

#
# Extract 'fix' data into a nice record
#
sub read_membership
{
    my ($f) = @_;

    my @field;
    my $row;

    print "reading: $f\n";
    open(FD, "$f") or die "can't open $f: $!";

    while (<FD>)
    {
        $row = $_;

        print "row=$row\n";

        @field = split /,/, $row;
        print 'name: ', $field[1], ' ', $field[0], "\n";

        $dbh->do("INSERT INTO tblPilot (pilFirstName,pilLastName,pilHGFA,pilSex) VALUES (?,?,?,?)", undef, $field[2],$field[1],$field[0],'');
    }

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


if (scalar @ARGV < 1)
{
    print("membreader.pl <csv file>\n");
    exit(1);
}

db_connect();

# Read the csv members
$members = read_membership($ARGV[0]);


