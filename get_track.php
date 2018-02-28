<?php
require 'authorisation.php';

$usePk = check_auth('system');
$link = db_connect();
$trackid = reqival('trackid');
$comPk = reqival('comPk');
$isadmin = is_admin('admin',$usePk,$comPk);
$interval = reqival('int');
$action = reqsval('action');
$extra = 0;


if ($interval < 1)
{
    $interval = 20;
    $segment = 25;
}
if ($interval == 1)
{
    $sql = "SELECT *, trlTime as bucTime FROM tblTrackLog where traPk=$trackid order by trlTime";
    $segment = 10;
}
else
{
    $sql = "SELECT *, trlTime div $interval as bucTime FROM tblTrackLog where traPk=$trackid group by trlTime div $interval order by trlTime";
}

$ret = [];

$result = mysqli_query($link, $sql);
while ($row = mysqli_fetch_assoc($result))
{

    $bucTime = $row['bucTime'];
    $lasLat = $row['trlLatDecimal'];
    $lasLon = $row['trlLongDecimal'];
    $lasAlt = dechex(($row['trlAltitude']/10)%256);
    $ret[] = array( 'time' => $bucTime, 'latitude' => $lasLat, 'longitude' => $lasLon, 'altitude' => $lasAlt );
}

$jret = json_encode($ret);

# nuke normal header ..
header("Content-type: text/plain");
header("Cache-Control: no-store, no-cache");

print $jret;
?>

