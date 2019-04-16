<?php
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Content-type: application/json');

require 'authorisation.php';

function get_region($regPk, $trackid)
{
    $link = db_connect();

    // task info ..
    if ($trackid > 0)
    {
        $sql = "SELECT max(T.trlLatDecimal) as maxLat, max(T.trlLongDecimal) as maxLong, min(T.trlLatDecimal) as minLat, min(T.trlLongDecimal) as minLong from tblTrackLog T where T.traPk=$trackid";
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Track query failed: ' . mysqli_connect_error());
        $row = mysqli_fetch_assoc($result);
    
        $maxLat = $row['maxLat'] + 0.02;
        $maxLong = $row['maxLong'] + 0.02;
        $minLat = $row['minLat'] - 0.02;
        $minLong = $row['minLong'] - 0.02;
        $crad = 400;
    
        $sql = "SELECT W.* FROM tblRegionWaypoint W where W.regPk=$regPk and W.rwpLatDecimal between $minLat and $maxLat and W.rwpLongDecimal between $minLong and $maxLong";
    }
    else
    {
        $crad = 0;
        $sql = "SELECT W.* FROM tblRegionWaypoint W where W.regPk=$regPk";
    }
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Region waypoint query failed: ' . mysqli_connect_error());
    $ret = array();
    while ($row = mysqli_fetch_assoc($result))
    {
    
        $lasLat = 0.0 + $row['rwpLatDecimal'];
        $lasLon = 0.0 + $row['rwpLongDecimal'];
        $cname = $row["rwpName"];
        $ret[] = array( $lasLat, $lasLon, $cname, $crad, '', 0 );
    }

    $res = array();
    $res['region'] = $ret;
    $jret = json_encode($res);
    return $jret;
}

$regPk = reqival('regPk');
$trackid = reqival('trackid');

$sorted = get_region($regPk, $trackid);
$data = array( 'region' => $sorted );
print json_encode($data);
?>

