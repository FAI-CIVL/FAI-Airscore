#!/usr/bin/perl -w
#
# Determine the shortest route using cartesian coords
# Geoff Wong 2008
# 

# Add currect bin directory to @INC
use File::Basename;
use lib '/home/untps52y/perl5/lib/perl5';
use lib dirname (__FILE__) . '/';
use Route qw(:all);

use POSIX qw(ceil floor);
use strict;

#
# Main program here ..
#

my $short_route;
my $taskno;

my $dbh = db_connect();

if (scalar @ARGV == 0)
{
    print "short_route.pl <tasPk>\n";
    exit(0);
}
$taskno = $ARGV[0];

# Work out the shortest route through task
my $task = read_task($taskno);
$short_route = find_shortest_route($task);
if (defined($short_route))
{
    store_short_route($dbh, $task, $short_route);
}

# Work out some distances
$task = read_task($taskno);
my ($spt, $ept, $gpt, $ssdist, $startssdist, $endssdist, $totdist) = task_distance($task);
print "spt=$spt ept=$ept gpt=$gpt ssdist=$ssdist startssdist=$startssdist endssdist=$endssdist total=$totdist\n";
print "update tblTask set tasSSDistance=$ssdist, tasEndSSDistance=$endssdist, tasStartSSDistance=$startssdist where tasPk=$taskno\n";
my $sth = $dbh->prepare("update tblTask set tasSSDistance=$ssdist, tasEndSSDistance=$endssdist, tasStartSSDistance=$startssdist where tasPk=$taskno");
$sth->execute();


#print "Task dist=$dist\n";


