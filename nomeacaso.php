<?php
require 'startup.php';

$page = 'LP AirScore';
$title = 'AirScore - Online Scoring Tool';

$out = '';
$retv = 0;
exec("python3 " . BINDIR . "design_map.py 1484 56", $out, $retv);

$iframe = "<iframe src='map.html' scrolling='no' style='width:100%;min-width:800px;height:100%;min-height:800px;overflow:hidden; margin-top:-4px; margin-left:-4px; border:none;'></iframe>";
//initializing template header
tpinit($link,$file,$row);

echo $iframe;

tpfooter($file);

?>
