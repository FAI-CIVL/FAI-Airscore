<?php
require 'authorisation.php';
require 'xcdb.php';
require 'rjson.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

header('Cache-Control: no-cache, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Content-type: application/json');

$link = db_connect();
$tasPk = reqival('tasPk');
$retarr = [];

$sql = "select CT.traPk, P.pilLastName from tblComTaskTrack CT, tblTrack T, tblPilot P where CT.tasPk=$tasPk and T.traPk=CT.traPk and P.pilPk=T.pilPk";
//$result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
$tracks = [];
$pilots = [];
//while($row = mysql_fetch_array($result, MYSQL_NUM))
while ($row = mysqli_fetch_row($result))
{
    $tracks[] = $row[0];
    $pilots[$row[0]] = $row[1];
}
if (sizeof($tracks) ==  0)
{
    return json_encode($retarr);
}

$allt = "(" . implode(",", $tracks) . ")";

$sql = "select TL.* from tblTrackLog TL where TL.traPk in " . $allt . " group by TL.traPk order by TL.traPk, TL.trlTime desc";
$sql = "select X.* from (select * from tblTrackLog TL where TL.traPk in " . $allt . " order by TL.traPk, TL.trlTime desc) X group by X.traPk";
//$result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());

$retarr = [];
//while($row = mysql_fetch_array($result, MYSQL_ASSOC))
while ($row = mysqli_fetch_assoc($result))
{
    $row['name'] = $pilots[$row['traPk']];
    $retarr[] = $row;
}


// mysql_close($link);
mysqli_close($link);
print rjson_pack($retarr);
?>
