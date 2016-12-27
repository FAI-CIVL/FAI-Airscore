#!/usr/bin/perl 
##!/usr/bin/perl -I/home/geoff/bin
#
# Determine the shortest route using cartesian coords
# Geoff Wong 2008
# 

use POSIX qw(ceil floor);
use Route qw(:all);
use strict;

#
# Main program here ..
#

my $dist;
my $taskno;
my $task;

my $dbh = db_connect();

if (scalar @ARGV == 0)
{
    print "short_route.pl <tasPk>\n";
    exit(0);
}
$taskno = $ARGV[0];

# Work out the shortest route through task
$dist = task_update($taskno);

# Work out some distances
$task = read_task($taskno);
my ($spt, $ept, $gpt, $ssdist, $startssdist, $endssdist) = task_distance($task);
print "spt=$spt ept=$ept gpt=$gpt ssdist=$ssdist startssdist=$startssdist endssdist=$endssdist\n";
print "update tblTask set tasSSDistance=$ssdist, tasEndSSDistance=$endssdist, tasStartSSDistance=$startssdist where tasPk=$taskno\n";
my $sth = $dbh->prepare("update tblTask set tasSSDistance=$ssdist, tasEndSSDistance=$endssdist, tasStartSSDistance=$startssdist where tasPk=$taskno");
$sth->execute();


#print "Task dist=$dist\n";


