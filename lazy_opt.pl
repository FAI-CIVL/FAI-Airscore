#!/usr/bin/perl

#
# Verify a track against a task
# 
# Geoff Wong 2007
#

require DBD::mysql;

use Math::Trig;
use Data::Dumper;
use Time::Local;
use POSIX qw(ceil floor);
use TrackLib qw(:all);

my $debug = 0;

my $track_width = 400;      # metres either side of middle lines
my $bucket_radius = 400;    # aggregation of points radius

#
# Task trimming/checking  ..
#
sub task_trim
{
    my ($task, $flight) = @_;
    my $waypoints;
    my @allpoints;
    my $coords;
    my @newcoords;
    my $count;
    my ($gmstart, $gmfinish);

    $waypoints = $task->{'waypoints'};
    $coords = $flight->{'coords'};

    $allpoints = scalar @$waypoints;

    $count = 0;
    for $coord (@$coords)
    {
        # Check the task isn't finished ..
        if ($flight->{'udate'} + $coord->{'time'} < $task->{'gmstart'})
        {
            print "Flight started before task start time (", $flight->{'udate'}+$coord->{'time'}, " < ", $task->{'gmstart'}, ")\n";
            $flight->{'coords'} = \@newcoords;
            return $flight;
        }

        if ($task->{'udate'} + $coord->{'time'} > $task->{'gmfinish'})
        {
            print "Flight continued after task end time: ", $flight->{'udate'}+$coord->{'time'}, ">", $task->{'gmfinish'}, "\n";
            splice(@$coords, $count);
            last;
        }
        $count++;
    }

    return $flight;
}

#
# Reduce the flight into sequential Xm (radius) blobs
# Also trim off wild GPS points and determine start/end of track.
#
sub reduce_flight
{
    my ($flight, $pilPk, $radius) = @_;
    my $full;
    my @reduced;
    my $dist;
    my $next;
    my $count;


    $full = $flight->{'coords'};
    $coord = shift @$full; 

    # reduce into buckets
    while (defined($coord))
    {
        my %bucket;
        my @blist;

        %bucket = ();
        @blist = ();

        #$bucket{'centre'} = $coord;
        push @blist, $coord;

        #print Dumper($coord);
        $next = shift @$full; 
        $count = 0;
        while (defined($next) && 
               (($dist=distance($coord, $next)) < $radius))
        {
            $count++;
            push @blist, $next;
            $next = shift @$full; 
        }
        #print Dumper($blist[int($count/2)]);
        $bucket{'centre'} = $blist[int($count/2)];

        $bucket{'bucket'} = \@blist;
        push @reduced, \%bucket;

        $coord = shift @$full;
        #print Dumper($coord);
    }

    return \@reduced;
}

#
# Reduce into a bunch of straight line segments.
#
sub segment_flight
{
    my ($flight) = @_;
    my $first;
    my $next;
    my $son;
    my @segment = ();

    $first = shift @$flight;
    while (defined($first))
    {
        my @track;
        my %segtr;

        @track = ();
        %segtr = ();

        # Start the line segment with 2 points (so it describes a line ...)
        push @track, $first;
        $next = shift @$flight;
        if (defined($next))
        {
            push @track, $next;
        }
        else
        {
            return \@segment;
        }

        $next = shift @$flight;
        while (defined($next))
        {

            #print Dumper($next);
            $son = straight_on(\@track, $next, $track_width);

            if ($son == 1)
            {
                # build up a straight track portion
                push @track, $next;
                $next = shift @$flight;
            }
            elsif ($son == 0)
            {
                # otherwise start a new track segment
                $first = $track[scalar @track - 1];
                unshift @$flight, $next;
                last;
            }
            else
            {
                # -1 .. ignore it ..
                $next = shift @$flight;
                if (!defined($next))
                {
                    $first = $next;
                }
            }
        }

        $segtr{'track'} = \@track;
        $segtr{'entry'} = $track[0];
        $segtr{'exit'} =  $track[scalar @track - 1];
        $segtr{'length'} = distance($segtr{'entry'}->{'centre'}, $segtr{'exit'}->{'centre'});

        push @segment, \%segtr;
    }

    return \@segment;
}

#
# Work out the distance if a particular segment is proposed to be merged
#
sub reduced_distance
{
    my ($flight, $merged) = @_;
    my $i;
    my %mdist;
    my $tot;
    my $num;
    my $start;
    my $end;
    my $dist;
    my $distalt;
    my $aflag;
    my $eflag;

    $tot = 0;
    $dist = 0;
    $eflag = 0;
    $aflag = 0;
    $num = scalar @$flight;

    for ($i = 0; $i < $num-1; $i++)
    {
        if ($i == $merged)
        {
            $start = $flight->[$i]->{'entry'}->{'centre'};
            $end = $flight->[$i+1]->{'exit'}->{'centre'};
            $mdist{'start'} = $flight->[$i]->{'entry'};
            $mdist{'end'} = $flight->[$i+1]->{'exit'};
            $dist = distance($start, $end);

            # deal with the 'edge' cases'
            if ($i == 0)
            {
                # first segment 
                $distalt = $flight->[$i+1]->{'length'};
                if ($distalt > $dist)
                {
                    $dist = $distalt;
                    $mdist{'start'} = $flight->[$i+1]->{'entry'};
                    $mdist{'offhead'} = $flight->[$i]->{'entry'};
                    $aflag = 1;
                }
            }
            elsif ($i == $num-2)
            {
                # last segment 
                $distalt = $flight->[$i]->{'length'};
                if ($distalt > $dist)
                {
                    $dist = $distalt;
                    $mdist{'end'} = $flight->[$i]->{'exit'};
                    $mdist{'offtail'} = $flight->[$i+1]->{'exit'};
                }
                $eflag = 1;
            }
            $i++;
            $tot = $tot + $dist;
        }
        else
        {
            $tot = $tot + $flight->[$i]->{'length'};
        }
    }
    if ($eflag == 0)
    {
        $tot = $tot + $flight->[$num-1]->{'length'};
    }

    $mdist{'length'} = $tot;
    $mdist{'newseg'} = $dist;
    $mdist{'alt'} = $aflag;

    #print "TRY: reduced $merged length=$tot\n";

    return \%mdist;
}



#
# Find the best scoring flight and return
# the start, t1, t2, t3, finish turnpoints
# type of flight (normal, triangle, faitriangle)
# and the score
# Build line segments around 'points'
#
# This reduced many segments to the number required
# by iteratively removing the "worst" segment ..
#
sub reduce_segments
{
    my ($flight, $segments) = @_;
    my $num;
    my $i;
    my %possible;
    my %tainted;
    my @skeys;
    my $res;
    my $t1;
    my $t2;
    my @cuttail;
    my @cuthead;

    my $dist;
    my $maxd;
    my $maxc;

    $num = scalar @$flight;
    while ($num > $segments)
    {
        %possible = ();
        for ($i = 0; $i < $num-1; $i++)
        {
            $possible{$i} = reduced_distance($flight, $i);
        }

        # sort %possible ..
        # pick the largest (1st) merge and merge them ..
        # and keep doing it until we have a 'conflict'
        @skeys = reverse sort { $possible{$a}->{'length'} <=> $possible{$b}->{'length'} } keys %possible;
        #foreach my $mg ( @skeys )

        # merge two segments ..
        # check if it's a start/finish segment properly ...
        $mg = @skeys[0];
        $res = $possible{$mg};
        if (defined($res->{'offhead'}))
        {
            push @cuthead, $res->{'offhead'};
            # now go through array and find best match ..
            $maxd = $flight->[1]->{'length'};
            $maxc = $flight->[1]->{'entry'};

            foreach my $hd (@cuthead)
            {
                $dist = distance($hd->{'centre'}, $flight->[1]->{'exit'}->{'centre'});
                if ($dist > $maxd)
                {
                    $maxd = $dist;
                    $maxc = $hd;
                }
            }
            $flight->[$mg]->{'entry'} = $maxc;
        }
        else
        {
            $flight->[$mg]->{'entry'} = $res->{'start'};
        }
        if (defined($res->{'offtail'}))
        {
            my $sz;

            push @cuttail, $res->{'offtail'};
            # now go through array and find best match ..
            $sz = scalar @$flight;
            $maxd = $flight->[$sz-2]->{'length'};
            $maxc = $flight->[$sz-2]->{'exit'};
            foreach my $hd (@cuttail)
            {
                $dist = distance($hd->{'centre'}, $flight->[$sz-2]->{'entry'}->{'centre'});
                print "tail dist=$dist (v $maxd)\n";
                if ($dist > $maxd)
                {
                    $maxd = $dist;
                    $maxc = $hd;
                }
            }
            $flight->[$mg]->{'exit'} = $maxc;
        }
        else
        {
            $flight->[$mg]->{'exit'} = $res->{'end'};
        }
        $flight->[$mg]->{'length'} = $res->{'newseg'};
        $t1 = $flight->[$mg]->{'track'};
        $t2 = $flight->[$mg+1]->{'track'};
        $flight->[$mg]->{'track'} = @$t1, @$t2;

        splice @$flight, $mg+1, 1;
        $num--;
        print "reducing ($mg) to $num, new length=", $res->{'length'}, " (", $res->{'alt'}, ")\n";
        #print "length after reduction=", scalar @$flight, "\n";
    }

    #print "length after reduction=", scalar @$flight, "\n";

    return $flight;
}

#
# Given a flight and a line segment description 
# and the first / last points to use in that segment
# find the maximal midpoint 
#
sub maximise_midpoint
{
    my ($flight, $existing, $f, $l) = @_;
    my $i;
    my $first;
    my $last;
    my $maxseg;
    my $maxlen;
    my $newlen;
    my %maxdist;

    $first = $existing->[$f];
    $last = $existing->[$l];

    $maxseg = -1;
    $maxlen = 0;

    #print " mmidpoint: first($f)=$first last($l)=$last\n";
    # sanity check
    if (($last - $first) < 2)
    {
        $maxdist{'length'} = 0;
        $maxdist{'segment'} = -1;

        return \%maxdist;
    }

    for ($i = $first+1; $i < $last; $i++)
    {
        $newlen = distance($flight->[$first]->{'entry'}->{'centre'}, $flight->[$i]->{'entry'}->{'centre'}) 
                + distance($flight->[$i]->{'entry'}->{'centre'}, $flight->[$last]->{'entry'}->{'centre'});
        if ($newlen > $maxlen)
        {
            $maxlen = $newlen;
            $maxseg = $i;
        }
    }

    $maxdist{'segment'} = $maxseg;
    $maxlen = 0;
    splice(@$existing, $f+1, 0, $maxseg);
    for ($i = 0; $i < (scalar @$existing - 1); $i++)
    {
       $maxlen = $maxlen +  
            distance($flight->[$existing->[$i]]->{'entry'}->{'centre'},
                     $flight->[$existing->[$i+1]]->{'entry'}->{'centre'});
    }
    splice(@$existing, $f+1, 1);

    $maxdist{'length'} = $maxlen;
    #print "max_dist $f max=$maxseg length=$maxlen\n";
    return \%maxdist;
}

#
# find a good endpoint 
#
sub maximise_endpoint
{
    my ($flight, $existing) = @_;
    my $i;
    my $first;
    my $last;
    my $maxseg;
    my $maxlen;
    my $newlen;
    my %maxdist;

    $maxseg = -1;
    $maxlen = 0;

    # sanity check

    $first = $existing->[scalar @$existing-1];
    $last = scalar @$flight-1;

    #print " mendpoint: first=$first last=$last\n";

    if (($last - $first) < 2)
    {
        $maxdist{'length'} = 0;
        $maxdist{'segment'} = -1;

        return \%maxdist;
    }

    for ($i = $first+1; $i < $last; $i++)
    {
        $newlen = distance($flight->[$first]->{'entry'}->{'centre'}, $flight->[$i]->{'entry'}->{'centre'}) 
                + distance($flight->[$i]->{'entry'}->{'centre'}, $flight->[$last]->{'entry'}->{'centre'});
        if ($newlen > $maxlen)
        {
            $maxlen = $newlen;
            $maxseg = $i;
        }
    }

    $maxdist{'segment'} = $maxseg;
    for ($i = 0; $i < (scalar @$existing - 1); $i++)
    {
       $maxlen = $maxlen +  
            distance($flight->[$existing->[$i]]->{'entry'}->{'centre'},
                     $flight->[$existing->[$i+1]]->{'entry'}->{'centre'});
    }

    $maxdist{'length'} = $maxlen;
    #print "mendpoint max_dist $f max=$maxseg length=$maxlen\n";
    return \%maxdist;
}

my $maxdist;
my @best;

sub combo_generator
{
    my ($flight, $dist, $base, $basearr, $min, $max, $num) = @_;
    my $copy;
    my $tdist;
    my $i;

    if ($debug)
    {
        print "cg ($num): $min $max $num ( ";
        for ($i = 0; $i < scalar @$basearr; $i++)
        {
            print $basearr->[$i], " ";
        }
        print ")\n";
    }
    for ($i = $min; $i < $max; $i++)
    {
        my @copy;
        
        if ($num > 1)
        {
            if ( ($max-($i)) >= $num)
            {
                @copy = @$basearr;
                push @copy, $i;

                if ($base > -1)
                {
                    $tdist = $dist + distance($flight->[$base]->{'entry'}->{'centre'}, $flight->[$i]->{'entry'}->{'centre'});
                }

                # FIX: only recurse if tdist sensible value (>400m?)
                combo_generator($flight, $tdist, $i, \@copy, $i+1, $max, $num-1);
            }
        }
        else
        {
            $tdist = $dist + distance($flight->[$base]->{'entry'}->{'centre'}, $flight->[$i]->{'entry'}->{'centre'});

            if ($tdist > $maxdist)
            {
                $maxdist = $tdist;
                @best = @$basearr;
                push @best, $i;
                print "  new best (seg=$i) dist=$maxdist: ";
                for (my $j = 0; $j < scalar @best; $j++)
                {
                    print $best[$j], " ";
                }
                print("\n");
            }
            elsif ($debug)
            {
                print "    +$i dist=$tdist\n";
            }
        }
    }
}

sub create_segments
{
    my ($flight, $best) = @_;
    my @selectsegs;
    my $num;

    $num = scalar @$best;

    if ($num < 2)
    {
        return $flight;
    }

    for ($i = 0; $i < $num-1; $i++)
    {
        my $newseg;
        my $len;

        #print "seg $i: " , $best->[$i] , "\n";

        $newseg = ();
        $newseg->{'entry'} = $flight->[$best->[$i]]->{'entry'};
        $newseg->{'exit'} = $flight->[$best->[$i+1]]->{'entry'};
        $len = distance($newseg->{'entry'}->{'centre'},
                                        $newseg->{'exit'}->{'centre'});
        $newseg->{'length'} = $len;

        push @selectsegs, $newseg;
    }

    return \@selectsegs;
}


sub bf_select_segments
{
    my ($flight, $segments) = @_;
    my $i;
    my @all;
    my @none;
    my $num;
    my $dist;
    my $seglen;
    my $result;
    my %tempseg;

    if (scalar @$flight <= $segments)
    {
        return $flight;
    }

    $num = scalar @$flight;
    #$maxdist = 0;

    $tempseg{'entry'} = $flight->[$num-1]->{'exit'};
    $tempseg{'exit'} = $flight->[$num-1]->{'exit'};
    $tempseg{'length'} = distance($tempseg{'entry'}->{'centre'}, $tempseg{'exit'}->{'centre'});
    push @$flight, \%tempseg;

    combo_generator($flight, 0, -1, \@none, 0, $num+1, $segments+1);
    #print "longest=", $maxdist, "\n";

    # return actual segments in a list rather than indices?
    #print Dumper(@best);
    $result = create_segments($flight, \@best);

    # restore $flight
    pop @$flight;

    return $result;
}

#
# Does the reverse .. pick the endpoints and tries to find 
# best endpoints increasing by 1 each time ...
#
sub select_segments
{
    my ($flight, $segments) = @_;

    my %tempseg;
    my $num;
    my $dist;
    my $i;
    my $j;
    my $k;
    my @skeys;
    my @tmparr;
    my $result;

    my $startseg;
    my $maxstartdist;

    my $endseg;
    my $maxenddist;

    # we're actually picking 'points' - build segments at the end
    $segments++;
    $num = scalar @$flight;

    # add a temporary point to flight since we're working with 
    # only 'entry' points to segments ..
    # FIX: seems to screw up maximise_dist of the last point?
    $tempseg{'entry'} = $flight->[$num-1]->{'exit'};
    $tempseg{'exit'} = $flight->[$num-1]->{'exit'};
    $tempseg{'length'} = 0;
    push @$flight, \%tempseg;
    $num++;

    # we picked arbitrary start/end points .. try to pick better ones ..
    @tmparr = ( 0, $num-1 );
    $i = maximise_midpoint($flight, \@tmparr, 0, 1);
    $midseg = $i->{'segment'};

    # now find new better endpoints ...
    $maxstartdist = 0;
    for ($i = 0; $i < $midseg; $i++)
    {
        $dist = distance($flight->[$i]->{'entry'}->{'centre'}, $flight->[$midseg]->{'entry'}->{'centre'});
        if ($dist > $maxstartdist)
        {
            $maxstartdist = $dist;
            $startseg = $i;
        }
    }
    $maxenddist = 0;
    for ($i = $midseg+1; $i < $num; $i++)
    {
        $dist = distance($flight->[$midseg]->{'entry'}->{'centre'}, $flight->[$i]->{'entry'}->{'centre'});
        if ($dist > $maxenddist)
        {
            $maxenddist = $dist;
            $endseg = $i;
        }
    }

    #print "best (from $midseg) start/end $startseg, $endseg\n";

    # and restart with better end points ..
    push @selected, $startseg;
    push @selected, $endseg;

    while (scalar @selected < $segments)
    {
        $num = scalar @selected;
        %possible = ();
        for ($i = 0; $i < $num-1; $i++)
        {
            # fix: need to get total track length with new midpoint ..
            $possible{$i} = maximise_midpoint($flight, \@selected, $i, $i+1);
        }
        # insert/choose a new/better endpoints as alternatives here too
        #if ($selected[0] > 0)
        #{
        #    #@tmparr = ( 0, $selected[0] );
        #    $possible{-1} = maximise_midpoint($flight, \@tmparr, 0, 1);
        #    #print " start=$num len=" . $possible{-1}->{'length'} . "\n";
        #}

        # this should be a maximise endpoint function ...
        if ((scalar @selected < $segments-1)
             && ($selected[$num-1] < scalar @$flight))
        {
            $possible{$num} = maximise_endpoint($flight, \@selected);
            #push @selected, scalar @$flight-1;
            #$possible{$num} = maximise_midpoint($flight, \@selected, $num-1, $num);
            #pop @selected;
            #print " end=$num len=" . $possible{$num}->{'length'} . 
            #    " seg=" . $possible{$num}->{'segment'} . "\n";
        }

        @skeys = reverse sort { $possible{$a}->{'length'} <=> $possible{$b}->{'length'} } keys %possible;

        #foreach my $seg (keys %possible)
        #{
        #    print " len=" . $possible{$seg}->{'length'} . 
        #        " seg=" . $possible{$seg}->{'segment'} . "\n";
        #}

        # find the best and insert ...
        $mg = $skeys[0];
        #print "splicing: $mg with " . $possible{$mg}->{'segment'} . "\n";
        splice(@selected, $mg+1, 0, $possible{$mg}->{'segment'});

        # FIX: special case if we added a new end/start 
        # need to recompute a better midpoint ...
        if ($mg == $num)
        {
            $replseg = maximise_midpoint($flight, \@selected, $num-2, $num);
            #print "replacing " . $selected[$num-1] . 
            #    " with " . $replseg->{'segment'} . "\n";
            $selected[$num-1] = $replseg->{'segment'};
        }
    }

    # return actual segments in a list rather than indices?
    $result = create_segments($flight, \@selected);
    
    # restore $flight
    pop @$flight;

    return $result;
}

# 
# Search through the "middle" (exit) bucket to find the locally
# "best" point to be the 'centre' for distance and set it
#
# Need to fix for entry/exit is the same point in segments?
#
sub maximise_dist
{
    my ($entry, $exit, $nextend) = @_;
    my $d1;
    my $sz;
    my $bucket;
    my $maxdist;
    my $largest;

    $bucket = $exit->{'bucket'};
    $maxdist = 0;
    foreach my $p2 (@$bucket)
    {
        $d1 = distance($entry->{'centre'}, $p2);
        if ($nextend)
        {
            $d1 = $d1 + distance($p2, $nextend->{'centre'});
        }
        if ($d1 > $maxdist)
        {
            $maxdist = $d1;
            $largest = $p2;
        }
    }
    
    # just set the new centre?
    $exit->{'centre'} = $largest;
    return $largest;
}

#
# Find the best 'centre' to maximise lengths of two segments ..
#
sub optimise_waypoints
{
    my ($flight) = @_;
    my $i;
    my $num;
    my $newcentre;
    my $entry;
    my $exit;

    $num = scalar @$flight;

    for ($i = 0; $i < $num; $i++)
    {
        if ($i == $num-1)
        {
            #$entry = $flight->[$i-1]->{'exit'};
            $entry = $flight->[$i]->{'entry'};
            $exit = $flight->[$i]->{'exit'};
            $newcentre = maximise_dist($entry, $exit, 0);
        }
        elsif ($i == 0)
        {
            # find best point to start (to seg exit). 
            $entry = $flight->[$i]->{'entry'};
            $exit = $flight->[$i+1]->{'entry'};
            $newcentre = maximise_dist($flight->[$i]->{'exit'}, $entry, 0);
            $newcentre = maximise_dist($entry, $exit, $flight->[$i+1]->{'exit'});
        }
        else
        {
            $entry = $flight->[$i]->{'entry'};
            $exit = $flight->[$i+1]->{'entry'};
            $newcentre = maximise_dist($entry, $exit, $flight->[$i+1]->{'exit'});
        }
        $flight->[$i]->{'length'} = distance($entry->{'centre'}, $exit->{'centre'});

    }

    return $flight;
}


#
# Store waypoints associated with track
#
sub store_waypoints
{
    my ($traPk,$flight) = @_;
    my $coords;
    my $sth;
    my $seg;
    my $i;
    my $sz;

    #$sth = $dbh->prepare("select max(traPk) from tblTrack");
    #$sth->execute();
    #$traPk  = $sth->fetchrow_array();

    $dbh->do("delete from tblWaypoint where traPk=?", undef, $traPk);

    $sz = scalar @$flight;
    #print "Flight length=$sz\n";
    for ($i = 0; $i < $sz; $i++)
    {
        $seg = $flight->[$i];
        if (!defined($seg->{'entry'}))
        {
            next;
        }
        $dbh->do("INSERT INTO tblWaypoint (traPk, wptLatDecimal, wptLongDecimal, wptTime, wptPosition) VALUES (?,?,?,?,?)", undef, $traPk, $seg->{'entry'}->{'centre'}->{'dlat'}, $seg->{'entry'}->{'centre'}->{'dlong'}, $seg->{'entry'}->{'centre'}->{'time'}, $i);
        #$dbh->do("INSERT INTO tblWaypoint (traPk, wptLatDecimal, wptLongDecimal, wptTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'exit'}->{'centre'}->{'dlat'}, $seg->{'exit'}->{'centre'}->{'dlong'}, $seg->{'exit'}->{'centre'}->{'time'});
    }

    $i = $sz - 1;
    $seg = $flight->[$i];
    # Add the exit of the last segment too ...
    $dbh->do("INSERT INTO tblWaypoint (traPk, wptLatDecimal, wptLongDecimal, wptTime, wptPosition) VALUES (?,?,?,?,?)", undef, $traPk, $seg->{'exit'}->{'centre'}->{'dlat'}, $seg->{'exit'}->{'centre'}->{'dlong'}, $seg->{'exit'}->{'centre'}->{'time'}, $i);
}

sub store_segments
{
    my ($traPk,$flight) = @_;
    my $coords;
    my $sth;
    my $seg;
    my $i;
    my $sz;

    #$sth = $dbh->prepare("select max(traPk) from tblTrack");
    #$sth->execute();
    #$traPk  = $sth->fetchrow_array();

    $dbh->do("delete from tblSegment where traPk=?", undef, $traPk);

    $sz = scalar @$flight;
    for ($i = 0; $i < $sz; $i++)
    {
        $seg = $flight->[$i];
        $dbh->do("INSERT INTO tblSegment (traPk, wptLatDecimal, wptLongDecimal, wptTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'entry'}->{'centre'}->{'dlat'}, $seg->{'entry'}->{'centre'}->{'dlong'}, $seg->{'entry'}->{'centre'}->{'time'});
        #$dbh->do("INSERT INTO tblSegment (traPk, wptLatDecimal, wptLongDecimal, wptTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'exit'}->{'centre'}->{'dlat'}, $seg->{'exit'}->{'centre'}->{'dlong'}, $seg->{'exit'}->{'centre'}->{'time'});
    }

    $i = $sz - 1;
    $seg = $flight->[$i];
    # Add the exit of the last segment too ...
    $dbh->do("INSERT INTO tblSegment (traPk, wptLatDecimal, wptLongDecimal, wptTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'exit'}->{'centre'}->{'dlat'}, $seg->{'exit'}->{'centre'}->{'dlong'}, $seg->{'exit'}->{'centre'}->{'time'});
}

#
# Store waypoints associated with track
#
sub store_buckets
{
    my ($traPk,$flight) = @_;
    my $coords;
    my $sth;
    my $seg;
    my $i;
    my $sz;

    #$sth = $dbh->prepare("select max(traPk) from tblTrack");
    #$sth->execute();
    #$traPk  = $sth->fetchrow_array();

    $dbh->do("delete from tblBucket where traPk=?", undef, $traPk);

    $sz = scalar @$flight;
    for ($i = 0; $i < $sz; $i++)
    {
        $seg = $flight->[$i];
        #print Dumper($seg);
        $dbh->do("INSERT INTO tblBucket (traPk, bucLatDecimal, bucLongDecimal, bucTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'centre'}->{'dlat'}, $seg->{'centre'}->{'dlong'}, $seg->{'centre'}->{'time'});
    }

    #$i = $sz - 1;
    #$seg = $flight->[$i];
    # Add the exit of the last segment too ...
    #$dbh->do("INSERT INTO tblWaypoint (traPk, wptLatDecimal, wptLongDecimal, wptTime) VALUES (?,?,?,?)", undef, $traPk, $seg->{'exit'}->{'centre'}->{'dlat'}, $seg->{'exit'}->{'centre'}->{'dlong'}, $seg->{'exit'}->{'centre'}->{'time'});
}

sub score_track
{
    my ($track,$totlen) = @_;
    my $totlen;
    my $polarea;
    my $ascore;
    my $gap;
    my $sz;
    
    $totlen=0;
    foreach my $seg (@$track)
    {
        #print Dumper($seg);
        $totlen = $totlen + $seg->{'length'};
    }

    # check if "closed" (20% leeway) ..
    $sz = scalar @$track;
    $gap = distance($track->[0]->{'entry'}->{'centre'}, $track->[$sz-1]->{'exit'}->{'centre'});
    print "scoring: gap=$gap totlen=$totlen\n";
    if (($gap/$totlen) < 0.2)
    {
        $polarea = polygon_area($track);
        $areabit = (4*$pi*$polarea) / ($totlen*$totlen);
        $ascore = (1.4 + $areabit) * $totlen - $gap;
        if ($ascore > $totlen)
        {
            print("areabit=$areabit, totlen=$totlen, polarea=$polarea, ascore=$ascore, gap=$gap\n");
            return $ascore;
        }
    }

    return $totlen;
}

#
# OLC scoring after this ..
#
#
#

my $flight;
my $task;
my $traPk;
my $turnpoints;
my $unreduced;
my $numb;

if (scalar(@ARGV) < 1)
{
    print "optimise_flight.pl <traPk> [tasPk] [turnpoints]\n";
    exit(1);
}
$traPk = $ARGV[0];
$tasPk = $ARGV[1];
$turnpoints = $ARGV[2];
if ($turnpoints eq '')
{
    $turnpoints = 3;
}
$dbh = db_connect();
$flight = read_track($traPk);
$bucket_radius = $flight->{'traDuration'} / 10 + 50;
$track_width = $track_width + $flight->{'traDuration'} / 20;
print "read traPk=", $flight->{'traPk'}, "\n";
print "bucket_radius=$bucket_radius\n";

if ($tasPk > 0)
{
    $flight->{'tasPk'} = $tasPk;
    $task = read_task($tasPk);
    if ($task->{'type'} eq 'olc' or 
        $task->{'type'} eq 'free')
    {
        $flight = task_trim($task, $flight);
    }
}

# Reduce into buckets
$reduced = reduce_flight($flight, $pilPk, $bucket_radius);
$numb = scalar @$reduced;
if ($numb == 1)
{
    print "Only one bucket - redo\n";
    $reduced = reduce_flight($flight, $pilPk, $bucket_radius/4);
}
#print Dumper($reduced);
print "num buckets=$numb\n";

$traPk = $flight->{'traPk'};
store_buckets($traPk, $reduced);

# Reduce into line segments
$segmented = segment_flight($reduced);
if (!defined($segmented) || scalar @$segmented == 0)
{
    print "Unable to segment flight\n";
    exit(1);
}
print "Number of unreduced segments=", scalar @$segmented, "\n";
#store_waypoints($traPk, $segmented);

# Ok .. work out total length
foreach my $seg (@$segmented)
{
    #print Dumper($seg);
    $totlen = $totlen + $seg->{'length'};
}
$numb = scalar @$segmented;
print "Total flight length of un-reduced segments($numb)=$totlen\n";
store_segments($traPk, $segmented);

# Reduce segments to numbers of required segments
if (scalar(@$segmented) > $turnpoints)
{
    $segmented = bf_select_segments($segmented,$turnpoints+1);
    #$segmented = select_segments($segmented,$turnpoints+1);
    $segmented = optimise_waypoints($segmented);
    print "Number of reduced segments=", scalar @$segmented, "\n";
}
store_waypoints($traPk, $segmented);

# Ok .. output flight segments for a looksy
$totlen=0;
foreach my $seg (@$segmented)
{
    #print Dumper($seg);
    #print "seg=", $seg->{'length'}, "\n";
    $totlen = $totlen + $seg->{'length'};
}
print "Total flight length of $turnpoints reduced segments=$totlen\n";

#print Dumper($segmented);
$score = score_track($segmented,$totlen);

if ($tasPk > 0)
{
    my %result;

    $result{'start'} = $task->{'sstart'};
    $result{'goal'} = 0;
    $result{'startSS'} = $task->{'sstart'};
    $result{'endSS'} = $task->{'sstart'};
    $result{'distance'} = $totlen;
    $result{'closest'} = 0;
    $result{'waypoints_made'} = 0;
    $result{'coeff'} = 0;
    
    store_result($flight, \%result);
}

$dbh->do("update tblTrack set traLength=?, traScore=? where traPk=?",
    undef, $totlen, $score, $traPk);

print "traPk=$traPk\n";

