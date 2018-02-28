<?php
require 'authorisation.php';
require 'xcdb.php';
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Content-type: application/json');

$link = db_connect();
$tasPk = reqival('tasPk');

$retarr = get_taskwaypoints($link,$tasPk);

#$sql = "SELECT T.* FROM tblShortestRoute T where T.tasPk=$tasPk order by T.ssrNumber";
#$result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
#
#$retarr = [];
#$srarr = [];
#while($row = mysql_fetch_array($result))
#{
#    $srarr[] = $row;
#}
#$retarr['short'] = $srarr;
#$retarr['task'] = $srarr;

mysqli_close($link);
print json_encode($retarr);
?>
