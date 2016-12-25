#!/usr/bin/perl -I..

require Vector;
use Test::More;
use Data::Dumper;
use strict;

# Helper function tests

my $v1 = Vector->new(3,4,2);
my $v2 = Vector->new(1,1,1);
my $v3 = Vector->new(4,4,2);
my $v4 = Vector->new(1,1,1);
my $v5 = Vector->new(2,4,4);

my $res = $v1 - $v2;
is_deeply($res, { 'x' => 2, 'y' => 3, 'z' => 1 }, "Vector subtraction");

my $resadd = $v1 + $v2;
is_deeply($resadd, { 'x' => 4, 'y' => 5, 'z' => 3 }, "Vector addition");

is($v3->length(), 6, "Vector length");

is($v1 == $v2, 0, "Vector comparison 1");

is($v2 == $v4, 1, "Vector comparison 2");

is(sprintf("%.3f", $v3 . $v5), "0.889", "Vector dot product");

done_testing;

