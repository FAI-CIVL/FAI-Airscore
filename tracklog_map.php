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
$comPk = $row['comPk'];
$out = '';
$retv = 0;

$source = '';
exec("python3 " . BINDIR . "design_map.py tracklog $tasPk $trackid ", $out, $retv);

if ($out)
{
    foreach ($out as $line)
    {
        $source .= htmlentities($line, ENT_COMPAT);
    }
}

// $iframe = "<iframe id='map' src='map.html' scrolling='no' style='width:100%;min-width:800px;height:100%;min-height:800px;overflow:hidden; margin-top:-4px; margin-left:-4px; border:none;'></iframe>";
$iframe = "<iframe id='map' srcdoc=\"$source\" scrolling='no' style='width:100%;min-width:800px;height:100%;min-height:800px;overflow:hidden; margin-top:-4px; margin-left:-4px; border:none;'></iframe>";

//initializing template header
tpinit($link,$file,$row);
#echo "python3 " . BINDIR . "design_map.py $trackid $tasPk";
echo $iframe;

echo "<br>";
echo "<p>";
echo "<a href='task_result.php?comPk=$comPk&tasPk=$tasPk'>Back to Task Results</a>";
echo "</p>";

tpfooter($file);

?>
