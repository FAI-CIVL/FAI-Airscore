#!/usr/bin/perl -I/home/geoff/bin

#
# IGC (et al) parsing & tracking analysis stuff 
#
require Exporter;

use Time::Local;
use Data::Dumper;

our @ISA    = qw(Exporter);
our @EXPORT = qw{:ALL};

use TrackLib qw(:ALL);

use strict;

my $first_time = 0;
my $last_time = 0;

my $debug = 0;
my $allowjumps = 0;
my $max_errors = 5;
my $DEGREESTOINT = 46603;

my $max_time_break = 300;

# this probably should be dynamic based on total # points
my $goodchunk = 500;        

local * FD;


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
        my $off = 0;
        # date
        if (substr($row, 5, 1) eq 'D')
        {
            $off = 5;
        }
        if (!defined($header->{'date'}))
        {
            $header->{'date'} = substr($row, $off + 9, 2) . substr($row, $off + 7, 2) . substr($row, $off + 5, 2);
            $header->{'start'} = timegm(0, 0, 0, 0+substr($row, $off + 5, 2), 0+substr($row, $off + 7, 2)-1,0+substr($row, $off + 9, 2));
        }
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
    elsif ($rowtype eq "PTZN")
    {
        # work out UTC offset for broken igc file
        #HPTZNUTCOFFSET:10:00
    }
}

#
# Extract 'fix' data into a nice record
# UTC (6), Lat (8), Long (9), Fix (1), Pressure (5), Altitude (5)
#
sub extract_fix
{
    my ($row) = @_;
    my %loc;
    my $ns;
    my $ew;
    my $arec;
    my ($h, $m, $s);
    my $c1;

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
    if ($loc{'time'} < $last_time)
    {
        print "Time went backwards in tracklog ($h:$m:$s) ", $loc{'time'}, " vs $last_time\n";
        return undef;
    }
    elsif ($loc{'time'} == $last_time)
    {
        # some leeway for bad points
        #$loc{'time'} = $last_time + 1;
        $loc{'fix'} = 'bad';
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
    $loc{'dlat'} = 0.0 + $loc{'lat'};
    $loc{'lat'} = $loc{'lat'} * PI() / 180;

    $loc{'long'} = 0 + substr $row, 15, 3;
    $m = (((0 + substr $row, 18, 5) / 1000) / 60);
    $loc{'long'} = $loc{'long'} + $m;
    $ew = substr $row, 23, 1;
    if ($ew eq "W")
    {
        $loc{'long'} = -$loc{'long'};
    }
    $arec = substr $row, 24, 1;
    if ($arec eq "V")
    {
        $loc{'fix'} = 'bad';
        #return undef;
    }
    $loc{'dlong'} = 0.0 + $loc{'long'};
    $loc{'long'} = $loc{'long'} * PI() / 180;

    if (!defined($loc{'fix'}))
    {
        $loc{'fix'} = substr $row, 24, 1;
    }
    $loc{'pressure'} = 0 + substr $row, 25, 5;
    $loc{'altitude'} = 0 + substr $row, 30, 5;
    
    # dodgy XC trainer fix 
    if ($loc{'altitude'} == 0 and $loc{'pressure'} != 0)
    {
        $loc{'altitude'} = $loc{'pressure'};
    }
    if ($loc{'altitude'} < 0)
    {
        $loc{'altitude'} = 0;
    }

    # Unused for simple track reading
    #$c1 = polar2cartesian(\%loc);
    #$loc{'cart'} = $c1;

    return \%loc;
}

sub read_igc
{
    my ($f) = @_;
    my %flight;
    my %header;
    my @coords;
    my $row;
    my $rowtype;
    my $errors = 0;
    my $crd;

    #print "reading: $f\n";
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
            $crd = extract_fix($row);
            if (!defined($crd))
            {
                $errors++;
            }
            elsif ($crd->{'fix'} ne 'bad')
            {
                push @coords, $crd;
            }
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

        if ($errors > $max_errors)
        {
            print "Too many errors in IGC log\n";
            return undef;
        }
    }

    $flight{'coords'} = \@coords;
    $flight{'header'} = \%header;

    return \%flight;
}


# KML reading stuff
#   Each coordinate needs:
#   'time' 'lat' 'dlat' 'long' 'dlong' 'altitude' 'pressure' 'fix'

sub kml_make_coord
{
    my ($ll, $tm, $p) = @_;
    my @arr;
    my $alt;
    my %loc;

    @arr = split(/,/,$ll);
    
    if (scalar(@arr) < 2)
    {
        print "Malformed coordinate: $ll\n";
        return undef;
    }

    $loc{'time'}= 0 + $tm;
    if ($first_time == 0)
    {
        $first_time = $loc{'time'};
    }
    if ($loc{'time'} < $first_time)
    {
        # in case track log goes over 24/00 time boundary
        $loc{'time'} = $loc{'time'} + 24 * 3600;
    }
    if ($loc{'time'} < $last_time)
    {
        print "Time went backwards in tracklog:  ", $loc{'time'}, " vs $last_time\n";
        return undef;
    }
    elsif ($loc{'time'} == $last_time)
    {
        # some leeway for bad points
        $loc{'time'} = $last_time + 1;
    }
    $last_time = $loc{'time'};

    $loc{'dlat'} = 0.0 + $arr[1];
    $loc{'lat'} = $loc{'dlat'} * PI() / 180;

    $loc{'dlong'} = 0.0 + $arr[0];
    $loc{'long'} = $loc{'dlong'} * PI() / 180;

    if (scalar(@arr) > 2)
    {
        $alt = 0 + $arr[2];
    }

    $loc{'altitude'} = $alt;
    $loc{'pressure'} = 0 + $p;

    # KML sucks and doesn't provide whether it's a proper fix or a predicted coord.
    $loc{'fix'} = 'A'; 

    return \%loc;
}

sub read_kml
{
    my ($f) = @_;
    my $tracklog;
    my %flight;
    my %header;
    my @coords;
    my @coordarr;
    my @timearr;
    my @pressurearr;
    my $coordinates;
    my $offset;
    my ($h,$m,$s);
    my ($yy,$mm,$dd);
    my $tmo;

    my $kml = XMLin($ARGV[0]);

    $tracklog = $kml->{'Folder'}->{'Placemark'}->{'Tracklog'};
    #print Dumper($tracklog);

    $tracklog->{'Metadata'}->{'FsInfo'}->{'time_of_first_point'};

    @coordarr = split(/ /,$tracklog->{'LineString'}->{'coordinates'});
    @timearr = split(/ /,$tracklog->{'Metadata'}->{'FsInfo'}->{'SecondsFromTimeOfFirstPoint'});
    @pressurearr = split(/ /,$tracklog->{'Metadata'}->{'FsInfo'}->{'PressureAltitude'});
    $offset = $tracklog->{'Metadata'}->{'FsInfo'}->{'time_of_first_point'};
    $h = 0+substr($offset, 11, 2);
    $m = 0+substr($offset,14,2);
    $s = 0+substr($offset,17,2);
    $tmo = $h * 3600 + $m * 60 + $s;
    $yy = substr($offset, 2, 2);
    $mm = substr($offset, 5, 2);
    $dd = substr($offset, 8, 2);
    $header{'date'} = $yy . $mm . $dd;
    $header{'start'} = timegm(0, 0, 0, $dd, (0+$mm)-1,0+$yy);

    for (my $c = 0; $c < scalar(@coordarr); $c++)
    {
        #print "coord=", $coordarr[$c], "\n";
        push @coords, kml_make_coord($coordarr[$c], $tmo + $timearr[$c], $pressurearr[$c]);
        #print Dumper($coords[$c]);
    }

    $flight{'coords'} = \@coords;
    $flight{'header'} = \%header;

    return \%flight;
}

# Leonardo/LIVE24 Differential track

sub unpack_coord
{
    my ($str) = @_;
    my ($tm,$lon,$lat,$alt);
    my %loc;

    ($tm,$lon,$lat,$alt) = unpack "NNNn", $str;

    $loc{'time'} = $tm;
    $loc{'dlat'} = $lat / $DEGREESTOINT;
    $loc{'lat'} = $loc{'dlat'} * PI() / 180;
    $loc{'dlong'} = $lon / $DEGREESTOINT;
    $loc{'long'} = $loc{'dlong'} * PI() / 180;
    $loc{'altitude'} = $alt;

    return \%loc;
}

# see if we can use differential format:
# 1        Full or diff format        
# 3        time diff        8 secs
# 7        alt diff        6 bits-> 64 m + 1 bit sign
# 11        lat diff        10 bits + 1 sign (1024)
# 10        lon diff         9 bits + 1 sign (512)
# total 1+3+7+11+10 = 32 bits = 4 bytes
sub unpack_diff_coord
{
    my ($last, $str) = @_;
    my ($fmt,$tmd,$lond,$latd,$altd);
    my %loc;

    ($fmt,$tmd,$altd,$latd,$lond) = unpack "bb3b7b11b10", $str;

    if ($fmt == 0)
    {
        return undef;
    }

    $loc{'time'} = $last->{'time'} + $tmd;
    $loc{'dlat'} = $last->{'lat'} + $latd / $DEGREESTOINT;
    $loc{'lat'} = $loc{'dlat'} * PI() / 180;
    $loc{'dlong'} = $last->{'long'} + $lond / $DEGREESTOINT;
    $loc{'long'} = $loc{'dlong'} * PI() / 180;
    $loc{'altitude'} = $last->{'altitude'} + $altd;


    return \%loc;
}

sub read_live
{
    my ($f) = @_;
    my %flight;
    my %header;
    my @coords;
    my $last;
    my $len;
    my $input;
    my $utime;
    my $rest;
    my $start = 0;

    #print "reading: $f\n";

    {
        local $/=undef;
        open(FD, "$f") or die "can't open $f: $!";
        binmode FD;
        $input = <FD>;
        close FD;
    }

    # remove 'Live' 
    $input = substr($input, 5);

    if ($input =~ /time=(\d+)/)
    {
        my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst);
        $utime = $1;
        ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = gmtime($utime);
        $header{'start'} = timegm(0, 0, 0, $mday, $mon, $year);
        $mon = $mon + 1;
        $year = $year + 1900;
        $header{'date'} = "$year-$mon-$mday";
    }

    $rest = index($input, "\n");
    if ($rest == -1)
    {
        return undef;
    }
    $input = substr($input,$rest+1);

    $len = length($input);
    while ($start < $len)
    {
        if (!defined($last))
        {
            $last = unpack_coord(substr($_,$start,14));
            $start += 14;
            push @coords, $last;
        }
        else
        {
            $last = unpack_diff_coord($last,substr($_,$start,4));
            if (defined($last))
            {
                $start += 4;
                push @coords, $last;
            }
            else
            {
                $last = unpack_coord(substr($_,$start,14));
                $start += 14;
            }
        }
    }

    $flight{'coords'} = \@coords;
    $flight{'header'} = \%header;
    return \%flight;
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

    $dist = abs(qckdist2($c1, $c2));
    $altdif = $c2->{'altitude'} - $c1->{'altitude'};
    $timdif = $c2->{'time'} - $c1->{'time'};

    #print "is flying dist=$dist altdif=$altdif timdif=$timdif\n";
    # allow breaks of up to 5 mins ..
    if ($allowjumps) 
    {
        return 0;
    }

    if ($timdif > $max_time_break)
    {
        if ($debug) { print "Not flying: time gap=$timdif secs\n"; }
        return 1;
    }
   
    if ($dist > 20 * $max_time_break)
    {
        if ($debug) { print "Not flying: big dist jump=$dist m\n"; }
        return 10;
    }

    # 
    if ($dist > (50.0*($timdif)))
    {
        # strange distance ....
        # print "dist not flying\n";
        if ($debug) { print "Not flying: teleported=$dist metres\n"; }
        return 1;
    }

    if ($altdif > (20.0*($timdif)))
    {
        if ($debug) { print "Not flying: vertical teleport=$altdif metres\n"; }
        return 1;
    }

    if (($dist < 3.0 and abs($altdif) < 4) || (($dist+abs($altdif)) < 7))
    {
        #print "c1->lat=", $c1->{'lat'}, "c1->long=", $c1->{'long'}, "\n";
        #print "c2->lat=", $c2->{'lat'}, "c2->long=", $c2->{'long'}, "\n";
        #print "c2->alt=", $c2->{'altitude'}, "\n";
        if ($debug)
        {
            print "Not flying ($c2->{'time'}): didn't move: time=$timdif secs horiz=$dist m vert=$altdif m\n";
        }
        return 1;
    }

    return 0;
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
    my $lasti;
    my $timdif;
    my $count = 0;
    my $coord;
    my $i;

    $full = $flight->{'coords'};

    # trim crap off the end of the flight ..
    $coord = pop @$full;
    $next = pop @$full; 
    while (defined($next) && ($count < 2))
    {
        #if ($debug) { print "Trim stuff from end\n"; }
        if (is_flying($next, $coord) > 0)
        {
            $count = 0;
        }
        else
        {
            $count++;        
        }
        $coord = $next;
        $next = pop @$full; 
    }
    # put the last two on again ...
    push @$full, $next;
    push @$full, $coord;

    # trim crap off the front of the flight ..
    $count = 0;
    $coord = shift @$full;
    $next = shift @$full; 
    while (defined($next) && $coord->{'fix'} ne 'A')
    {
        #if ($debug) { print "no fix at start\n"; }
        $coord = $next;
        $next = shift @$full; 
    }
    while (defined($next) && is_flying($coord, $next) > 0)
    {
        #if ($debug) { print "trim at start\n"; }
        $coord = $next;
        $next = shift @$full; 
    }

    # TODO: only take "latest" track if "broken"?
    # work backwards .. look for a !flying
    #print "trim for last flying segment\n";
    $timdif = 0;

    # look for a segment of at least 10 mins ..
    #if ($debug) { print "find best recent segment\n"; }
    $max = scalar @$full;
    while ($timdif < $goodchunk and $max > 2)
    {
        my $isf;

        $max = scalar @$full;
        $count = 0;
        $last = $full->[$max-1];
        $lasti = $max - 1;
        for ($i = $max-1; $i > 0; $i--)
        {
            if ($full->[$i-1]->{'fix'} ne 'A')
            {
                # Only use good fixes ..
                next;
            }
            if ($last->{'time'} - $full->[$i-1]->{'time'} < 15)
            {
                # Only check points every 15 seconds or so ...
                next;
            }
            $isf = is_flying($full->[$i-1], $last);
            if ($isf > 0)
            {
                print "!is_flying ($isf) at $i\n";
                if ($last->{'time'} - $full->[$i-1]->{'time'} > 120)
                {
                    if ($debug) { print "Big time gap in tracklog: ", $last->{'time'}, ", previous: ", $full->[$i-1]->{'time'}, "\n"; }
                    last;
                }
                $count = $count + $isf;
            }
            else
            {
                $count = 0;
            }

            if ($count > 8)
            {
                # only "not" flying after 3?
                if ($debug) { print "Not flying: counted out at $i\n"; }
                last;
            }
            $last = $full->[$i-1];
            $lasti = $i-1;
        }
        $timdif = $full->[$max-1]->{'time'} - $full->[$lasti]->{'time'};
        if (($timdif < $goodchunk) and ($i > 1))
        {
            if ($debug) { print "Using start segment to: $i\n"; }
            @$full = splice(@$full, 0, $i-1);
        }
        elsif (($timdif >= $goodchunk) and ($i > 1))
        {
            if ($debug) { print "Using end segment from: $lasti (to $max)\n"; }
            @$full = splice(@$full, $lasti, $max-$lasti);
        }

        # don't loop forever if it's a good track!
        if ($i == 0)
        {
            last;
        }
    }
    $flight->{'header'}->{'start'} = $flight->{'header'}->{'start'} + $full->[0]->{'time'};

    return $flight;
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

sub determine_filetype
{
    my ($f) = @_;
    my $row;

    #print "reading: $f\n";
    open(FD, "$f") or die "can't open $f: $!";

    $row = <FD>;
    if ($debug) { print "first row=$row"; }
    if ((substr $row, 0, 1) eq 'A')
    {
        return "igc";
    }

    if ((substr $row, 0, 3) eq '<?x')
    {
        return "kml";
    }

    if ($row =~ /B  UTF/)
    {
        return "ozi";
    }

    if ((substr $row, 0, 3) eq 'LIV')
    {
        return "live";
    }

    return undef;
}

1;

