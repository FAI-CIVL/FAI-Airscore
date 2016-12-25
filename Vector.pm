#!/usr/bin/perl -I/home/bin/geoff

#
# Basic mathematical vector class with some overloaded operators
# Geoff Wong 2016
#
package Vector;

require Exporter;
our @ISA       = qw(Exporter);
#our @EXPORT = qw(:all);

require DBD::mysql;
use POSIX qw(ceil floor);
use Math::Trig;
use Data::Dumper;
use strict;

use overload
    '+' => \&vecadd,
    '-' => \&vecsub,
    '*' => \&vecmult,
    '/' => \&vecdiv,
    '==' => \&vecequal,
    '.' => \&vecdot;

sub new
{
    my $class = shift;
    my $self = {};
    my ($x, $y, $z) = @_;

    # Setup the vector
    $self->{'x'} = $x;
    $self->{'y'} = $y;
    $self->{'z'} = $z;

    # set any defaults here ...
    bless ($self, $class);
    return $self;
}

sub vecadd
{
    my ($self, $other, $swap) = @_;

    my $cart = {};
    #my $result = $$self - $other;

    $cart->{'x'} = $self->{'x'} + $other->{'x'};
    $cart->{'y'} = $self->{'y'} + $other->{'y'};
    $cart->{'z'} = $self->{'z'} + $other->{'z'};

    #my $result = -$result if $swap;
    ref $cart ? $cart : bless \$cart;
}

sub vecsub
{
    my ($self, $other, $swap) = @_;

    my $cart = {};
    #my $result = $$self - $other;

    $cart->{'x'} = $self->{'x'} - $other->{'x'};
    $cart->{'y'} = $self->{'y'} - $other->{'y'};
    $cart->{'z'} = $self->{'z'} - $other->{'z'};

    #my $result = -$result if $swap;
    ref $cart ? $cart : bless \$cart;
}

sub vecmult
{
    my ($self, $other, $swap) = @_;

    my $cart = {};

    if ($swap)
    {
        $cart = $other * $$self;
    }
    else
    {
        $cart->{'x'} = $self->{'x'} * $other;
        $cart->{'y'} = $self->{'y'} * $other;
        $cart->{'z'} = $self->{'z'} * $other;
    }
    ref $cart ? $cart : bless \$cart;
}

sub vecdiv
{
    my ($self, $other, $swap) = @_;

    my $result = $$self - $other;
    my $result = -$result if $swap;
    ref $result ? $result : bless \$result;
}

sub vecdot
{
    my ($self, $other, $swap) = @_;

    my ($v, $w) = @_;

    my $tl = $v->{'x'} * $w->{'x'} + $v->{'y'} * $w->{'y'} + $v->{'z'} * $w->{'z'};
    my $bl = $v->length() * $w->length();

    if ($bl == 0)
    {
        return 1.0;
    }

    return $tl/$bl;
}

sub vecequal
{
    my ($self, $other, $swap) = @_;

    if ($self->{'x'} == $other->{'x'} &&
        $self->{'y'} == $other->{'y'} &&
        $self->{'z'} == $other->{'z'})
    {
        return 1;
    }

    return 0;
}

sub length
{
    my ($self) = @_;

    return sqrt($self->{'x'}*$self->{'x'} + $self->{'y'}*$self->{'y'} + $self->{'z'}*$self->{'z'}); 
}

sub size
{
    my ($self) = @_;

    return scalar $self;
}

1;
