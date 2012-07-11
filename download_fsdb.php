<?php
require 'authorisation.php';

my $out;
my $retv;
my $comPk;
my $res;
//auth('system');
$link = db_connect();

$comPk=intval($_REQUEST['download']);

exec(BINDIR . "fsdb_export.pl $comPk", $out, $retv);

header("Content-type: text/wpt");
header("Content-Disposition: attachment; filename=\"waypoints-$regPk.wpt\"");
header("Cache-Control: no-store, no-cache");

print $out;
?>

