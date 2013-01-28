#!/usr/bin/perl
#
# Check to see if a track violates airspace
#
# Needs to be quick/pruned somehow?
# Only check if 'nearby' / every 30 seconds?
# 
# Geoff Wong 2008
#

require DBD::mysql;

use Math::Trig;
use Data::Dumper;
use POSIX qw(ceil floor);
use TrackLib qw(:all);

my $dbh;

my $max_height = 3048;  # 10000' limit in oz 
#my $max_height = 2591;  # 10000' limit in oz 

#
# Read an abbreviated tracklog from the database 
#
sub read_short_track
{
    my ($traPk) = @_;
    my %track;
    my @coords;
    my %awards;
    my $ref;
    my $c1;

    $sth = $dbh->prepare("select *, floor(trlTime/60) as trlMinTime, max(trlAltitude) as maxAlt from tblTrackLog where traPk=$traPk group by floor(trlTime/60) order by trlTime");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        #print "Found a row: time = $ref->{'trlTime'}\n";
        my %coord;

        $coord{'dlat'} = $ref->{'trlLatDecimal'};
        $coord{'dlong'} = $ref->{'trlLongDecimal'};

        # radians
        $coord{'lat'} = $ref->{'trlLatDecimal'} * $pi / 180;
        $coord{'long'} = $ref->{'trlLongDecimal'} * $pi / 180;

        # alt / time  / pressure?
        $coord{'alt'} = $ref->{'maxAlt'};
        $coord{'time'} = $ref->{'trlTime'};

        # and cartesian ..
        $c1 = polar2cartesian(\%coord);
        $coord{'cart'} = $c1;

        push @coords, \%coord;
    }

    $track{'coords'} = \@coords;

    return \%track;
}

sub airspace_check
{
    my ($traPk, $airspaces) = @_;
    my $flight;
    my $violation;
    my $dst;

    $violation = 0;
    $flight = read_short_track($traPk);
    $full = $flight->{'coords'};

    foreach $space (@$airspaces)
    {
        print "Checking airspace ", $space->{'name'}, " with base=", $space->{'base'}, "\n";
        #print Dumper($space);

        for my $coord ( @$full )
        {
            # add dist check on centre of space too ...distance($coord, $space->{'centre'}) < $space->{'radius'}
            # fix: create an angle to current point .. compare with radius
            #  and if between the angles of the "edge" points of (outer) radius
            #print "check ", $space->{'name'}, "\n";
            if ($coord->{'alt'} > 10000) 
            {
                # ignore stupid values from tracklog
                next;
            }

            # stupid max height (10000ft) check for oz pilots
            if ($coord->{'alt'} > $max_height)
            {
                if ($coord->{'alt'} - $space->{'base'} > $violation)
                {
                    $violation = $coord->{'alt'} - $max_height;
                    print "PV: max_height (8500') violation\n";
                }
            }

            if ($coord->{'alt'} > $space->{'base'})
            { 
                # potential violation ..
                if ($space->{'shape'} eq 'circle')
                {
                    $dst = distance($coord, $space->{'centre'});
                    if ($dst < $space->{'radius'})
                    {
                        print "PV(circle):  alt=", $coord->{'alt'}, " dlat=", $coord->{'dlat'}, " dlong=", $coord->{'dlong'}, "\n";
                        $violation = $coord->{'alt'} - $space->{'base'};
                    }

                }
#                if ($space->{'shape'} eq 'wedge')
#                {
#                    if (in_wedge($coord, $space->{'points'}))
#                    {
#                    }
#                    $dst = distance($coord, $space->{'centre'});
#                    if ($dst < $space->{'radius'})
#                    {
#                        # Find bearing and check if between anglestart/end
#                        print "PV:  alt=", $coord->{'alt'}, " dlat=", $coord->{'dlat'}, " dlong=", $coord->{'dlong'}, "\n";
#                        $violation = $coord->{'alt'} - $space->{'base'};
#                    }
#                }
                elsif (in_polygon($coord, $space->{'points'}))
                {
                    if ($coord->{'alt'} - $space->{'base'} > $violation)
                    {
                        print "PV(poly):  alt=", $coord->{'alt'}, " dlat=", $coord->{'dlat'}, " dlong=", $coord->{'dlong'}, "\n";
                        $violation = $coord->{'alt'} - $space->{'base'};
                    }
                }
            }
        }
    }
    return $violation;
}

#int nvert, float *vertx, float *verty, float testx, float testy)
#  for (i = 0, j = nvert-1; i < nvert; j = i++) 
#  {
#    if ( ((verty[i]>$wpt->{'y'}) != (verty[j]>$wpt->{'y'})) &&
#     (testx < (vertx[j]-vertx[i]) * (testy-verty[i]) / (verty[j]-verty[i]) + vertx[i]) )
#       c = !c;
#
#      for (i = 0, j = npol-1; i < npol; j = i++) {
#        if ((((yp[i] <= y) && (y < yp[j])) ||
#             ((yp[j] <= y) && (y < yp[i]))) &&
#            (x < (xp[j] - xp[i]) * (y - yp[i]) / (yp[j] - yp[i]) + xp[i]))
#          c = !c;
#      }

sub in_polygon
{
    my ($wpt, $poly) = @_;
    my ($i, $j);
    my $c = 0;
    my $nvert;

    $nvert = scalar @$poly;

#    print "wpt=", Dumper($wpt);
#    print "poly=", Dumper($poly);

    for ($i = 0, $j = $nvert-1; $i < $nvert; $j = $i++) 
    {
#        if ( (($poly->[$i]->{'cart'}->{'y'} > $wpt->{'cart'}->{'y'}) 
#                != ($poly->[$j]->{'cart'}->{'y'} > $wpt->{'cart'}->{'y'})) &&
#            ($wpt->{'cart'}->{'x'} < ($poly->[$j]->{'cart'}->{'x'}-$poly->[$i]->{'cart'}->{'x'}) * ($wpt->{'cart'}->{'y'} - $poly->[$i]->{'cart'}->{'y'}) / 
#            ($poly->[$j]->{'cart'}->{'y'} - $poly->[$i]->{'cart'}->{'y'}) + $poly->[$i]->{'cart'}->{'x'}) )
        if (( (($poly->[$i]->{'cart'}->{'y'} <= $wpt->{'cart'}->{'y'}) &&
               ($wpt->{'cart'}->{'y'} < $poly->[$j]->{'cart'}->{'y'})) ||
              (($poly->[$j]->{'cart'}->{'y'} <= $wpt->{'cart'}->{'y'}) &&
               ($wpt->{'cart'}->{'y'} < $poly->[$i]->{'cart'}->{'y'}))) &&
               ($wpt->{'cart'}->{'x'} < ($poly->[$j]->{'cart'}->{'x'} -
                    $poly->[$i]->{'cart'}->{'x'}) * ($wpt->{'cart'}->{'y'} -
                $poly->[$i]->{'cart'}->{'y'}) / 
                ($poly->[$j]->{'cart'}->{'y'} - $poly->[$i]->{'cart'}->{'y'}) + $poly->[$i]->{'cart'}->{'x'}) )
        {
            #print "cross\n";
            $c++;
        }
    }

    return ($c % 2);
}

# radius should be maximum wedge radius
#
sub in_wedge
{
    my ($wpt, $poly) = @_;
    my ($i, $j);
    my $dst;
    my $nvert;

    $dst = distance($coord, $space->{'centre'});
    if ($dst < $space->{'radius'})
    {
        $nvert = scalar @$poly;
        for ($i = 0, $j = $nvert-1; $i < $nvert; $j = $i++) 
        {
            # Find bearing and check if between anglestart/end
            #print "PV:  alt=", $coord->{'alt'}, " dlat=", $coord->{'dlat'}, " dlong=", $coord->{'dlong'}, "\n";
            #$violation = $coord->{'alt'} - $space->{'base'};
        }
    }
}

sub make_wedge
{
    my ($center, $alpha, $beta, $radius, $dirn) = @_;

    my $points = 16;
    my $earth = 6378137.0;
    my $delta;
    my @Cpoints;
    my ($nlat,$nlon);
    my $nbrg;

    #print "make_wedge $alpha $beta $radius $dirn\n";
    #print "center = ", Dumper($center);

    # to radians
    if ($dirn eq "arc-")
    {
        # anti
        $delta = $alpha - $beta;
    }
    else
    {
        # clock
        $delta = $beta - $alpha;
    }

    if ($delta < 0)
    {
        $delta = $delta + $pi * 2;
    }

    $delta = $delta / $points;

    if ($dirn eq "arc-")
    {
        $delta = - $delta;
    }

    $nbrg = $alpha;
    for (my $i=0; $i < $points; $i++) 
    {
        my %coord;

        $nlat = asin(sin($center->{'lat'})*cos($radius/$earth) + 
                cos($center->{'lat'})*sin($radius/$earth)*cos($nbrg) );

        $nlon = $center->{'long'} + atan2(sin($nbrg)*sin($radius/$earth)*cos($center->{'lat'}), cos($radius/$earth)-sin($center->{'lat'})*sin($nlat));

        # back to degrees ..
        $nlat = $nlat * 180 / $pi;
        $nlon = $nlon * 180 / $pi;

        #print "added lat=$nlat lon=$nlon\n";

        $coord{'dlat'} = $nlat;
        $coord{'dlong'} = $nlon;
        $coord{'lat'} = $nlat * $pi / 180;
        $coord{'long'} = $nlon * $pi / 180;
        $coord{'cart'} = polar2cartesian(\%coord);

        push @Cpoints, \%coord;

        $nbrg = $nbrg + $delta;
    }

    return \@Cpoints;
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

#
# Returns a list of airspace that is centred 'near' the track  
# within traDistance+XXX)
#
sub find_nearby_airspace
{
    my ($regPk, $dist) = @_;
    my @allair;
    my ($sth,$ref);
    my %nearair;
    my $airPk;
    my @points;
    my $centre;

    # Get regPk centre ...
    #$sth = $dbh->prepare("select * from tblAirspace A, tblAirspaceWaypoint AW where A.airCentreWP = AW.awpPk and AW.awpLatDecimal between (X,Y) and AW.awpLonDecimal between (X,Y)");

    # Get it all for now ...
    $sth = $dbh->prepare("select * from tblAirspace A, tblAirspaceWaypoint AW where A.airPk=AW.airPk order by A.airPk,AW.airOrder");

    $sth->execute();
    $airPk = 0;
    while ($ref = $sth->fetchrow_hashref())
    {
        my %coord;

        if ($ref->{'airPk'} != $airPk)
        {
            if ($airPk == 0)
            {
                $airPk = $ref->{'airPk'};
            }
            else
            {
                my @pts;
                my %na;
                @pts = @points;
                $nearair{'points'} = \@pts;
                %na = %nearair;
                push @allair, \%na;
                @points = ();
                %nearair = ();
                $airPk = $ref->{'airPk'};

            }
        }

        $nearair{'name'} = $ref->{'airName'};
        $nearair{'class'} = $ref->{'airClass'};
        $nearair{'base'} = $ref->{'airBase'};
        $nearair{'tops'} = $ref->{'airTops'};
        $nearair{'shape'} = $ref->{'airShape'};
        $nearair{'radius'} = $ref->{'airRadius'};

        $coord{'dlat'} = $ref->{'awpLatDecimal'};
        $coord{'dlong'} = $ref->{'awpLongDecimal'};
        $coord{'lat'} = $ref->{'awpLatDecimal'} * $pi / 180;
        $coord{'long'} = $ref->{'awpLongDecimal'} * $pi / 180;
        $coord{'cart'} = polar2cartesian(\%coord);
        $coord{'astart'} = $ref->{'awpAngleStart'};
        $coord{'aend'} = $ref->{'awpAngleEnd'};
        $coord{'connect'} = $ref->{'awpConnect'};
        #print "coord=",Dumper($coord), "\n";

        push @points, \%coord;
    }

    $nearair{'points'} = \@points;
    # Assuming only one point for circular regions
    $nearair{'centre'} = $points[0];

    push @allair, \%nearair;
    return \@allair;
}

sub find_task_airspace
{
    my ($tasPk) = @_;
    my @allair;
    my ($sth,$ref);
    my %nearair;
    my $airPk;
    my @points;
    my $centre;

    # Get regPk centre ...
    #$sth = $dbh->prepare("select * from tblAirspace A, tblAirspaceWaypoint AW where A.airCentreWP = AW.awpPk and AW.awpLatDecimal between (X,Y) and AW.awpLonDecimal between (X,Y)");

    # Get it all for now ...
    $sth = $dbh->prepare("select * from tblTaskAirspace TA, tblAirspace A, tblAirspaceWaypoint AW where TA.tasPk=$tasPk and A.airPk=TA.airPk and A.airPk=AW.airPk order by A.airPk,AW.airOrder");

    $sth->execute();
    $airPk = 0;
    while ($ref = $sth->fetchrow_hashref())
    {
        my %coord;

        if ($ref->{'airPk'} != $airPk)
        {
            if ($airPk == 0)
            {
                $airPk = $ref->{'airPk'};
            }
            else
            {
                my @pts;
                my %na;
                @pts = @points;
                $nearair{'points'} = \@pts;
                %na = %nearair;
                push @allair, \%na;
                @points = ();
                %nearair = ();
                $airPk = $ref->{'airPk'};

            }
        }

        $nearair{'name'} = $ref->{'airName'};
        $nearair{'class'} = $ref->{'airClass'};
        $nearair{'base'} = $ref->{'airBase'};
        $nearair{'tops'} = $ref->{'airTops'};
        $nearair{'shape'} = $ref->{'airShape'};
        $nearair{'radius'} = $ref->{'airRadius'};

        # else ...
        $coord{'dlat'} = $ref->{'awpLatDecimal'};
        $coord{'dlong'} = $ref->{'awpLongDecimal'};
        $coord{'lat'} = $ref->{'awpLatDecimal'} * $pi / 180;
        $coord{'long'} = $ref->{'awpLongDecimal'} * $pi / 180;
        $coord{'cart'} = polar2cartesian(\%coord);

        if (($ref->{'awpConnect'} eq 'arc+') or ($ref->{'awpConnect'} eq 'arc-'))
        {
            # add in 
            my $radius;
            my $ext;
            
            $radius = distance(\%coord, $points[scalar(@points)-1]);
            $extra = make_wedge(\%coord, 0.0+$ref->{'awpAngleStart'}, 0.0+$ref->{'awpAngleEnd'}, $radius, $ref->{'awpConnect'});
            shift @$extra;
            foreach $ext (@$extra)
            {
                push @points, $ext;
            }
        }

        push @points, \%coord;
    }

    $nearair{'points'} = \@points;
    # Assuming only one point for circular regions
    $nearair{'centre'} = $points[0];

    push @allair, \%nearair;
    return \@allair;
}

sub get_all_tracks
{
    my ($tasPk) = @_;
    my ($sth,$ref);
    my %ret;

    $sth = $dbh->prepare("select CTT.traPk, P.* from tblComTaskTrack CTT, tblTrack T, tblPilot P where CTT.traPk=T.traPk and P.pilPk=T.pilPk and CTT.tasPk=$tasPk");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref())
    {
        $ret{$ref->{'traPk'}} = $ref;
    }

    return \%ret;
}

#
# Verify an entire task ...
#

my $tasPk = 0 + $ARGV[0];
my $tracks;
my $airspace;
my $dist;
my $name;

$dbh = db_connect();
$tracks = get_all_tracks($tasPk);
#$tracks = [ 821, 823, 865 ];
#$airspace = find_nearby_airspace($regPk, 100000.0);
$airspace = find_task_airspace($tasPk);
#print Dumper($airspace);

# Go through all the tracks ..
# might be more useful to print the names :-)

for my $track (keys %$tracks)
{
    print "Airspace check for track: $track\n";
    $dist = 0;
    $name = $tracks->{$track}->{'pilFirstName'} . " " . $tracks->{$track}->{'pilLastName'};
    if (($dist = airspace_check($track,$airspace)) > 0)
    {
        print "   Maximum violation of $dist metres ($name).\n";
    }
    else
    {
        print "   No violation ($name).\n";
    }
}


