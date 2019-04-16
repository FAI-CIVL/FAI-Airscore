<?php
require 'startup.php';
require LIBDIR.'xcdb.php';

$page = 'LP AirScore';
$title = 'AirScore - Online Scoring Tool';
$trackid = reqival('trackid');
$tasPk = reqival('tasPk');
$usePk = check_auth('system');

$link = db_connect();

$file = __FILE__;
$row = get_comtask($link,$tasPk);

$out = '';
$retv = 0;
exec("python3 " . BINDIR . "design_map.py $trackid $tasPk", $out, $retv);

$iframe = "<iframe src='map.html' scrolling='no' style='width:100%;min-width:800px;height:100%;min-height:800px;overflow:hidden; margin-top:-4px; margin-left:-4px; border:none;'></iframe>";

//initializing template header
tpinit($link,$file,$row);
#echo "python3 " . BINDIR . "design_map.py $trackid $tasPk";
echo $iframe;

tpfooter($file);

?>
