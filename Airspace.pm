#!/usr/bin/perl -w
#
# Check to see if a track violates airspace
#
# Needs to be quick/pruned somehow?
# Only check if 'nearby' / every 30 seconds?
# 
# Geoff Wong 2008
#

require      Exporter;
require DBD::mysql;
use Math::Trig;
use Time::Local;
use Data::Dumper;

our @ISA       = qw(Exporter);
our @EXPORT = qw{:ALL};

use POSIX qw(ceil floor);
use TrackLib qw(:all);

use strict;

my $dbh;

my $max_height = 3048;  # 10000' limit in oz 
my $start_below = 20;
#my $max_height = 2591;  # 8500' limit in oz 
#my $max_height = 1666;  # 5000' limit in oz 

#
# Read an abbreviated tracklog from the database 
#
sub read_short_track
{
    my ($dbh, $traPk,$bucket) = @_;
    my %track;
    my @coords;
    my %awards;
    my $ref;
    my $c1;

    my $sth = $dbh->prepare("select *, floor(trlTime/$bucket) as trlMinTime, max(trlAltitude) as maxAlt, min(trlLatDecimal) as minLatDecimal, min(trlLongDecimal) as minLongDecimal, max(trlLatDecimal) as maxLatDecimal, max(trlLongDecimal) as maxLongDecimal from tblTrackLog where traPk=$traPk group by floor(trlTime/$bucket) order by trlTime");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref()) 
    {
        #print "Found a row: time = $ref->{'trlTime'}\n";
        my %coordll;
        my %coordlm;
        my %coordml;
        my %coordmm;

        # coords - decimal / radians / alt/time / cartesian for the region
        $coordll{'dlat'} = $ref->{'minLatDecimal'};
        $coordll{'dlong'} = $ref->{'minLongDecimal'};
        $coordll{'lat'} = $ref->{'minLatDecimal'} * PI() / 180;
        $coordll{'long'} = $ref->{'minLongDecimal'} * PI() / 180;
        $coordll{'alt'} = $ref->{'maxAlt'};
        $coordll{'time'} = $ref->{'trlTime'};
        $c1 = polar2cartesian(\%coordll);
        $coordll{'cart'} = $c1;
        push @coords, \%coordll;

        if ($bucket > 1)
        {
            # coord - decimal / radians / alt/time
            $coordlm{'dlat'} = $ref->{'minLatDecimal'};
            $coordlm{'dlong'} = $ref->{'maxLongDecimal'};
            $coordlm{'lat'} = $ref->{'minLatDecimal'} * PI() / 180;
            $coordlm{'long'} = $ref->{'maxLongDecimal'} * PI() / 180;
            $coordlm{'alt'} = $ref->{'maxAlt'};
            $coordlm{'time'} = $ref->{'trlTime'};
            $c1 = polar2cartesian(\%coordlm);
            $coordlm{'cart'} = $c1;
            push @coords, \%coordlm;
    
            # coord - decimal / radians / alt/time
            $coordml{'dlat'} = $ref->{'maxLatDecimal'};
            $coordml{'dlong'} = $ref->{'minLongDecimal'};
            $coordml{'lat'} = $ref->{'maxLatDecimal'} * PI() / 180;
            $coordml{'long'} = $ref->{'minLongDecimal'} * PI() / 180;
            $coordml{'alt'} = $ref->{'maxAlt'};
            $coordml{'time'} = $ref->{'trlTime'};
            $c1 = polar2cartesian(\%coordml);
            $coordml{'cart'} = $c1;
            push @coords, \%coordml;
    
            # coord - decimal / radians / alt/time
            $coordmm{'dlat'} = $ref->{'maxLatDecimal'};
            $coordmm{'dlong'} = $ref->{'maxLongDecimal'};
            $coordmm{'lat'} = $ref->{'maxLatDecimal'} * PI() / 180;
            $coordmm{'long'} = $ref->{'maxLongDecimal'} * PI() / 180;
            $coordmm{'alt'} = $ref->{'maxAlt'};
            $coordmm{'time'} = $ref->{'trlTime'};
            $c1 = polar2cartesian(\%coordmm);
            $coordmm{'cart'} = $c1;
            push @coords, \%coordmm;
        }

    }

    $track{'coords'} = \@coords;

    return \%track;
}

sub cln
{
    my ($fix) = @_;
    #$fix =~ s/[\d001-\d037]//g;
    $fix =~ s/[^[:print:]]//g;
    return $fix;
}

sub flight_check
{
    my ($quick, $flight, $airspaces) = @_;
    my $full;
    my $violation = 0;
    my $space;

    $full = $flight->{'coords'};
    foreach $space (@$airspaces)
    {
        #print Dumper($space);
        if (!defined($space->{'centre'}))
        {
            $space->{'centre'} = $space->{'points'}->[0];
        }

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
            if ($coord->{'alt'} > $max_height - $start_below)
            {
                if (($coord->{'alt'} - ($max_height - $start_below)) > $violation)
                {
                    $violation = $coord->{'alt'} - ( $max_height - $start_below );
                    if ($quick)
                    {
                        return $violation;
                    }
                    else
                    {
                        print "\n    MaxAltitude (", cln($space->{'name'}), ") max=", $max_height, "m alt=", $coord->{'alt'}, " dlat=", $coord->{'dlat'}, " dlong=", $coord->{'dlong'};
                    }
                }
            }

            if (($coord->{'alt'} > $space->{'base'} - $start_below) && $coord->{'alt'} < $space->{'tops'})
            {
                # potential violation ..
                if ($space->{'shape'} eq 'circle')
                {
                    my $dst = distance($coord, $space->{'centre'});
                    if ($dst < $space->{'radius'} + $start_below)
                    { 
                        $violation = $coord->{'alt'} - ( $space->{'base'} - $start_below );
                        if ($quick)
                        {
                            return $violation;
                        }
                        else
                        {
                            print "\n    Circle (", cln($space->{'name'}), ") base=", $space->{'base'}, "m @ alt=", $coord->{'alt'}, "m horiz=", floor($space->{'radius'}-$dst+$start_below) , "m dlat=", $coord->{'dlat'}, " dlong=", $coord->{'dlong'};
                        }
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
                    if ($coord->{'alt'} - ( $space->{'base'} - $start_below ) > $violation)
                    {
                        $violation = $coord->{'alt'} - ( $space->{'base'} - $start_below );
                        if ($quick)
                        {
                            return $violation;
                        }
                        else
                        {
                            print "\n    Polygon (", cln($space->{'name'}), ") base=", $space->{'base'}, "m) @ alt=", $coord->{'alt'}, " dlat=", $coord->{'dlat'}, " dlong=", $coord->{'dlong'};
                        }
                    }
                }
            }
        }
    }

    return $violation;
}

sub airspace_check
{
    my ($dbh, $traPk, $airspaces) = @_;
    my $flight;
    my $violation;
    my $dst;

    $violation = 0;
    $flight = read_short_track($dbh,$traPk,200);
    $violation = flight_check(1, $flight, $airspaces);
    if ($violation > 0)
    {
        $flight = read_short_track($dbh, $traPk,1);
        $violation = flight_check(0, $flight, $airspaces);
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
    my ($wpt, $space) = @_;
    my ($i, $j);
    my $dst;
    my $nvert;
    my $poly = $space->{'points'};

    $dst = distance($wpt, $space->{'centre'});
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
        $delta = $delta + PI() * 2;
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
        $nlat = $nlat * 180 / PI();
        $nlon = $nlon * 180 / PI();

        #print "added lat=$nlat lon=$nlon\n";

        $coord{'dlat'} = $nlat;
        $coord{'dlong'} = $nlon;
        $coord{'lat'} = $nlat * PI() / 180;
        $coord{'long'} = $nlon * PI() / 180;
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
    my $ref;
    my %nearair;
    my $airPk;
    my @points;
    my $centre;

    # Get regPk centre ...
    #$sth = $dbh->prepare("select * from tblAirspace A, tblAirspaceWaypoint AW where A.airCentreWP = AW.awpPk and AW.awpLatDecimal between (X,Y) and AW.awpLonDecimal between (X,Y)");

    # Get it all for now ...
    my $sth = $dbh->prepare("select * from tblAirspace A, tblAirspaceWaypoint AW where A.airPk=AW.airPk order by A.airPk,AW.airOrder");

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
        $coord{'lat'} = $ref->{'awpLatDecimal'} * PI() / 180;
        $coord{'long'} = $ref->{'awpLongDecimal'} * PI() / 180;
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
    my ($dbh, $tasPk) = @_;
    my @allair;
    my $ref;
    my %nearair;
    my $airPk;
    my @points;
    my $centre;

    # Get regPk centre ...
    #$sth = $dbh->prepare("select * from tblAirspace A, tblAirspaceWaypoint AW where A.airCentreWP = AW.awpPk and AW.awpLatDecimal between (X,Y) and AW.awpLonDecimal between (X,Y)");

    # Get it all for now ...
    my $sth = $dbh->prepare("select * from tblTaskAirspace TA, tblAirspace A, tblAirspaceWaypoint AW where TA.tasPk=$tasPk and A.airPk=TA.airPk and A.airPk=AW.airPk order by A.airPk,AW.airOrder");

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
        $coord{'lat'} = $ref->{'awpLatDecimal'} * PI() / 180;
        $coord{'long'} = $ref->{'awpLongDecimal'} * PI() / 180;
        $coord{'cart'} = polar2cartesian(\%coord);

        if (($ref->{'awpConnect'} eq 'arc+') or ($ref->{'awpConnect'} eq 'arc-'))
        {
            # add in 
            my $radius;
            my $ext;
            
            $radius = distance(\%coord, $points[scalar(@points)-1]);
            my $extra = make_wedge(\%coord, 0.0+$ref->{'awpAngleStart'}, 0.0+$ref->{'awpAngleEnd'}, $radius, $ref->{'awpConnect'});
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
    my ($dbh, $tasPk) = @_;
    my $ref;
    my %ret;

    my $sth = $dbh->prepare("select CTT.traPk, P.* from tblComTaskTrack CTT, tblTrack T, tblPilot P where CTT.traPk=T.traPk and P.pilPk=T.pilPk and CTT.tasPk=$tasPk order by P.pilLastName");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref())
    {
        $ret{$ref->{'traPk'}} = $ref;
    }

    return \%ret;
}

sub get_one_track
{
    my ($dbh, $traPk) = @_;
    my $ref;
    my %ret;

    my $sth = $dbh->prepare("select CTT.traPk, P.* from tblComTaskTrack CTT, tblTrack T, tblPilot P where T.traPk=$traPk and CTT.traPk=T.traPk and P.pilPk=T.pilPk");
    $sth->execute();
    while ($ref = $sth->fetchrow_hashref())
    {
        $ret{$ref->{'traPk'}} = $ref;
    }

    return \%ret;
}

1;

