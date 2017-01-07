#!/usr/bin/perl -I..

use Test::More;
use Data::Dumper;
use Route qw(:all);
use strict;

# Helper function tests

#is(round(1.3), 1.0, "Rounding 1");
#is(round(1.5), 2.0, "Rounding 2");
#is(round(1.8), 2.0, "Rounding 3");

my $task1 = 
    { 
        'tasPk' => 1,
        'waypoints' =>
        [
            { 'key'=> 1, 'number' => 1, 'type' => 'start',    'how' => 'exit',  'shape' => 'circle', radius => 1000, name => 'test1', 'lat' => -36.5 * PI() / 180, 'long' => 110.0 * PI() / 180 },
            { 'key'=> 3, 'number' => 3, 'type' => 'waypoint', 'how' => 'entry', 'shape' => 'circle', radius => 1000, name => 'test3', 'lat' => -37.0 * PI() / 180, 'long' => 110.0 * PI() / 180 },
            { 'key'=> 5, 'number' => 5, 'type' => 'goal',     'how' => 'entry', 'shape' => 'circle', radius => 1000, name => 'test5', 'lat' => -36.5 * PI() / 180, 'long' => 110.5 * PI() / 180 },
        ]
    };


my $task2 = 
    { 
        'tasPk' => 2,
        'waypoints' => 
        [
            { 'key'=> 1, 'number' => 1, 'type' => 'start',    'how' => 'exit',  'shape' => 'circle', radius => 400, name => 'test1', 'lat' => -36.5 * PI() / 180, 'long' => 110.0 * PI() / 180 },
            { 'key'=> 2, 'number' => 2, 'type' => 'speed',    'how' => 'exit',  'shape' => 'circle', radius => 5000, name => 'test2', 'lat' => -36.5 * PI() / 180, 'long' => 110.0 * PI() / 180 },
            { 'key'=> 3, 'number' => 3, 'type' => 'waypoint', 'how' => 'entry', 'shape' => 'circle', radius => 1000, name => 'test3', 'lat' => -37.0 * PI() / 180, 'long' => 110.0 * PI() / 180 },
            { 'key'=> 4, 'number' => 4, 'type' => 'endspeed', 'how' => 'entry', 'shape' => 'circle', radius => 2000, name => 'test4', 'lat' => -36.5 * PI() / 180, 'long' => 110.5 * PI() / 180 },
            { 'key'=> 5, 'number' => 5, 'type' => 'goal',     'how' => 'entry', 'shape' => 'circle', radius => 1000, name => 'test5', 'lat' => -36.5 * PI() / 180, 'long' => 110.5 * PI() / 180 },
        ]
    };

my $task3 = 
    { 
        'tasPk' => 3,
        'waypoints' => 
[
{ 'key' => 3383, 'number' => 1, 'type' => 'start', 'how' => 'exit', 'shape' => 'circle', 'radius' => 400, name => 'wk2', 'lat' => -44.63759987 * PI() / 180, 'long' => 168.90910026 * PI() / 180 },
{ 'key' => 3378, 'number' => 2, 'type' => 'speed', 'how' => 'exit', 'shape' => 'circle', 'radius' => 1000, name => 'wk2', 'lat' => -44.63759987 * PI() / 180, 'long' => 168.90910026 * PI() / 180 },
{ 'key' => 3379, 'number' => 3, 'type' => 'waypoint', 'how' => 'exit', 'shape' => 'circle', 'radius' => 8000, name => 'wk2', 'lat' => -44.63759987 * PI() / 180, 'long' => 168.90910026 * PI() / 180 },
{ 'key' => 3380, 'number' => 4, 'type' => 'waypoint', 'how' => 'entry', 'shape' => 'circle', 'radius' => 400, name => 'wk2', 'lat' => -44.63759987 * PI() / 180, 'long' => 168.90910026 * PI() / 180 },
{ 'key' => 3381, 'number' => 5, 'type' => 'waypoint', 'how' => 'entry', 'shape' => 'circle', 'radius' => 1000, name => 'wk3', 'lat' => -44.59199997 * PI() / 180, 'long' => 169.33140015 * PI() / 180 },
{ 'key' => 3382, 'number' => 6, 'type' => 'goal', 'how' => 'entry', 'shape' => 'circle', 'radius' => 1000, name => 'wk4', 'lat' => -44.68069995 * PI() / 180, 'long' => 169.19040011 * PI() / 180 }
]
    };


my ($spt, $ept, $gpt, $ssdist, $startssdist, $endssdist, $totdist);
my $sr1 = find_shortest_route($task1);
for (my $i = 0; $i < scalar @$sr1; $i++)
{
    $task1->{'waypoints'}->[$i]->{'short_lat'} = $sr1->[$i]->{'lat'};
    $task1->{'waypoints'}->[$i]->{'short_long'} = $sr1->[$i]->{'long'};
}

($spt, $ept, $gpt, $ssdist, $startssdist, $endssdist, $totdist) = task_distance($task1);

is($spt, 0, "start speed point");
is($ept, 2, "end speed point");
is($gpt, 2, "goal point");
is(sprintf("%.1f", $ssdist), "122930.3", "speed section distance");
is($startssdist, 1000, "start speed distance");
is(sprintf("%.1f", $endssdist), "123930.3", "end speed section distance");
is(sprintf("%.1f", $totdist), "123930.3", "total distance");

my $sr2 = find_shortest_route($task2);
for (my $i = 0; $i < scalar @$sr2; $i++)
{
    $task2->{'waypoints'}->[$i]->{'short_lat'} = $sr2->[$i]->{'lat'};
    $task2->{'waypoints'}->[$i]->{'short_long'} = $sr2->[$i]->{'long'};
}

($spt, $ept, $gpt, $ssdist, $startssdist, $endssdist, $totdist) = task_distance($task2);

is($spt, 1, "start speed point");
is($ept, 3, "end speed point");
is($gpt, 4, "goal point");
is(sprintf("%.1f", $ssdist), "117947.8", "speed section distance");
is($startssdist, 5000, "start speed distance");
is(sprintf("%.1f", $endssdist), "122947.8", "end speed section distance");
is(sprintf("%.1f", $totdist), "123941.7", "total distance");

$task2->{'waypoints'}->[4]->{'shape'} = 'line';
my $sr3 = find_shortest_route($task2);
for (my $i = 0; $i < scalar @$sr3; $i++)
{
    $task2->{'waypoints'}->[$i]->{'short_lat'} = $sr3->[$i]->{'lat'};
    $task2->{'waypoints'}->[$i]->{'short_long'} = $sr3->[$i]->{'long'};
}

($spt, $ept, $gpt, $ssdist, $startssdist, $endssdist, $totdist) = task_distance($task2);

is($spt, 1, "start speed point");
is($ept, 3, "end speed point");
is($gpt, 4, "goal point");
is(sprintf("%.1f", $ssdist), "117947.8", "speed section distance");
is($startssdist, 5000, "start speed distance");
is(sprintf("%.1f", $endssdist), "122947.8", "end speed section distance");
is(sprintf("%.1f", $totdist), "124941.6", "total distance");


my $sr4 = find_shortest_route($task3);
for (my $i = 0; $i < scalar @$sr4; $i++)
{
    $task3->{'waypoints'}->[$i]->{'short_lat'} = $sr4->[$i]->{'lat'};
    $task3->{'waypoints'}->[$i]->{'short_long'} = $sr4->[$i]->{'long'};
}

($spt, $ept, $gpt, $ssdist, $startssdist, $endssdist, $totdist) = task_distance($task3);

is($spt, 1, "start speed point");
is($ept, 5, "end speed point");
is($gpt, 5, "goal point");
is(sprintf("%.1f", $ssdist), "60179.6", "speed section distance");
is($startssdist, 1000, "start speed distance");
is(sprintf("%.1f", $endssdist), "61179.6", "end speed section distance");
is(sprintf("%.1f", $totdist), "61179.6", "total distance");

# add a test for in_semicircle

done_testing
