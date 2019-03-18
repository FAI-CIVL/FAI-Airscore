#!/usr/bin/perl -w
#
# Reads in a CSV membership list
#
#

require DBD::mysql;
use Data::Dumper;

# Add currect bin directory to @INC
use File::Basename;
use lib '/home/untps52y/perl5/lib/perl5';
use lib dirname (__FILE__) . '/';
use TrackLib qw(:all);

#
# Database handles
#


#
# Extract 'fix' data into a nice record
#
sub read_membership
{
    my ($dbh,$f) = @_;

    my @field;
    my $row;
    my $nat;

    print "reading: $f\n";
    open(FD, "$f") or die "can't open $f: $!";

    while (<FD>)
    {
        $row = $_;

        print "row=$row\n";

        @field = split /,/, $row;
        if ($field[1] eq '')
        {
            next;
        }
        print 'add name: ', $field[1], ' ', $field[2], "\n";
        
        # Get Country ID
        $nat = $field[3];
        $sth = $dbh->prepare("	SELECT 
									C.natID AS Code 
								FROM 
									tblCountryCodes C 
								WHERE 
									C.natIso3 = '$nat'");
        $sth->execute();
        if  ($ref = $sth->fetchrow_hashref())
		{
			$nat = $ref->{'Code'};
		}
		else
		{
			# Set Italy
			$nat = 380;
		}
        


        # should be an insert/update ..
        insertup('tblExtPilot', 'pilPk', "pilLastName='" . $field[2] . 
                "' and pilFAI='" . $field[0] . "'",
            {
                'pilFirstName' => $field[1],
                'pilLastName' => $field[2],
                'pilFAI' => $field[0],
                'pilSex' => $field[4],
                'pilNat' => $nat
            });
        #$dbh->do("INSERT INTO tblPilot (pilFirstName,pilLastName,pilFAI,pilSex) VALUES (?,?,?,?)", undef, $field[1],$field[0],$field[2],'M');
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
my $dbh;

$dbh = db_connect();

print 'Arg: ' . $ARGV[0];

if (scalar @ARGV < 1)
{
    print "bulk_pilot_import.pl <membershiplist>\n";
    exit(1);
}

# Read the csv members
$members = read_membership($dbh, $ARGV[0]);


