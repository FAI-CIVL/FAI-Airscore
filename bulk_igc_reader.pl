#!/usr/bin/perl

#
# Reads in a zip file full of .igc files
# should be named as such: FAINO.igc or LASTNAME_FIRSTNAME.igc
#
# Geoff Wong 2007
#

require DBD::mysql;
use Data::Dumper;
use File::Temp;
use File::Copy;
use File::Basename;

use TrackLib qw(:all);
use Defines qw(:all);

local * DIR;

#
# Extract files and read them all into the database 
#
sub extract_igcs
{
    my ($f) = @_;

    my @fields;
    my @names;
    my %tracks;
    my $row;
    my $tmpdir;
    my $pilPk;
    my $hgfa;
    my $sth;

    # clean up and extract files ..

    $tmpdir = mkdtemp("/tmp/bulkXXXX");
    #system("/usr/bin/rm -rf $tmpdir");
    #mkdir($tmpdir, 0755);
    system("yes | /usr/bin/unzip $f -d $tmpdir");

    opendir(DIR, $tmpdir) or die "can't opendir $f: $!";

    while (defined($file = readdir(DIR))) 
    {
        # find the pilot ..
        #print "got: $file\n";
        if ($file eq "." or $file eq "..")
        {
            next;
        }

        @fields = split /\./, $file;

        # check size = 2
        @names = split /_/, $fields[0];

        if (scalar @names > 0)
        {
            $pilPk = 0 + $fields[0];
            
            #print "found: $pilPk\n";
        }

        if ($pilPk > 0)
        {
            $sth = $dbh->prepare("select pilHGFA from tblPilot where pilPk=$pilPk" );
        }
        else
        {
            if (scalar @names > 1)
            {
                #print "two found: ", $names[0], " ", $names[1], "\n";
                $sth = $dbh->prepare("select pilHGFA from tblPilot where pilLastName='" . $names[0] . "' and pilFirstName='$names[1]'");
            }
            else
            {
                $sth = $dbh->prepare("select pilHGFA from tblPilot where pilLastName='" . $names[0] . "'");
            }
        }
        $sth->execute();

        # add the pilot if they're not found?
        $hgfa = $sth->fetchrow_array() + 0;

        if ($hgfa == 0)
        {
            print "Can't find pilot $file in database\n";
        }
        else
        {
            print "Found: $file with hgfa=$hgfa\n";
            $tracks{$hgfa} = $tmpdir . "/" .$file;
        }
    }

    closedir(DIR);

    return \%tracks;
}

sub read_all_tracks
{
    my ($comPk,$tasPk,$tracks) = @_;
    my $file;
    my $nfile;
    my $traPk;
    my @fields;
    my $out;
    my $outo;
    my $gliPk;
    my $sth;
    my $res;
    my $name;
    my $copyname;
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst);
    my $dte;

    ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime();
    $year = $year + 1900;
    $dte = sprintf("%04d-%02d-%02d_%02d%02d%02d", $year, $mon+1, $mday, $hour, $min, $sec);

    #print Dumper($tracks);
    for my $pilPk ( keys %$tracks )
    {
        $file = $tracks->{$pilPk};
        #print "Track read ($file) for pilot=$pilPk\n";
        
        $nfile = dirname($file) . "\/$pilPk";
        rename($file, $nfile);

        print ("${BINDIR}add_track.pl $pilPk \"$nfile\" $comPk $tasPk\n");
        $res = `${BINDIR}add_track.pl $pilPk \"$nfile\" $comPk $tasPk`;
        print $res;
        #print "Track read ($pilPk:$file) may have failed: $out\n";

        $sth = $dbh->prepare("select pilLastName from tblPilot where pilHGFA='$pilPk'");
        $sth->execute();
        $name = lc($sth->fetchrow_array());

        $copyname = $FILEDIR . $year . "/" . $name . "_" . $pilPk . "_" . $dte;
        print "cp $nfile $copyname\n";
        copy($file, $copyname);
        chmod 0644, $copyname;
    }
}

#
# Main program here ..
#

my $tracks;
my $tasPk;
my $comPk;
my $sth;

if (scalar @ARGV < 2)
{
    print "bulk_igc_reader.pl tasPk zipfile\n";
    exit 0;
}

$dbh = db_connect();

# Check the task stuff
$tasPk = $ARGV[0] + 0;

$sth = $dbh->prepare("select comPk from tblTask where tasPk=$tasPk");
$sth->execute();
$comPk  = $sth->fetchrow_array() + 0;

if ($comPk == 0)
{
    print "Can't find task $tasPk\n";
    exit 1;
}

# Find all the tracks
$tracks = extract_igcs($ARGV[1]);

# Read each of the tracks 
read_all_tracks($comPk,$tasPk,$tracks);

# Score the round ..
#system("task_score.pl $tasPk");

