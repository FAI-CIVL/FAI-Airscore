#!/usr/bin/perl -w
#
# Verify a track against a task
# Used for Race competitions and Routes.
#
# Geoff Wong 2007
#

require DBD::mysql;

#use Math::Trig;
#use Data::Dumper;
use POSIX qw(ceil floor);
use strict;

# Add currect bin directory to @INC
use File::Basename;
#use lib '/home/ubuntu/perl5/lib/perl5';
use lib dirname (__FILE__) . '/';
use TrackLibTest qw(:all);


my $dbh;
my $debug = 0;
my $wptdistcache;

my (%s1, %s2);
my $wpdist = -1;

$s1{'lat'} = 0.806718150768408;
$s1{'long'} = 0.229448680320048;
$s2{'lat'} = 0.807212132519345;
$s2{'long'} = 0.229381632802791;
$wpdist = distance(\%s1, \%s2);
print "s1 lat = $s1{'lat'} , lon = $s1{'long'} - s2 lat = $s2{'lat'} , lon = $s2{'long'}\n";
print "wpdist waypoint = $wpdist\n";
print "reference was 3159.97713064629\n";