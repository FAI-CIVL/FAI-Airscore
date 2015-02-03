<?php
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Content-type: application/json');

require 'authorisation.php';
require 'xcdb.php';
require 'rjson.php';

function get_airspace($airPk)
{
    $ret = array();
    $link = db_connect();

    $sql = "SELECT A.*, AW.* from tblAirspace A, tblAirspaceWaypoint AW where A.airPk=$airPk and AW.airPk=A.airPk order by AW.airOrder";
    $result = mysql_query($sql,$link);

    while ($row = mysql_fetch_array($result, MYSQL_ASSOC))
    {
    
        $lasLat = $row['awpLatDecimal'];
        $lasLon = $row['awpLongDecimal'];
        $base = $row['airBase'];
        $tops = $row['airTops'];
        $radius = $row['airRadius'];
        $class = $row['airClass'];
        $shape = $row['airShape'];
        $connect = $row['awpConnect'];
        $astart = $row['awpAngleStart'];
        $aend = $row['awpAngleEnd'];
    
        #$ret[] = array( 'class' => $class, 'latitude' => $lasLat, 'longitude' => $lasLon, 'base' => $base, 'tops' => $tops, 'shape' => $shape, 'radius' => $radius );
        $ret[] = array( $class, $lasLat, $lasLon, $base, $tops, $shape, $radius, $connect, $astart, $aend );
    }
    
    mysql_close($link);
    
    return $ret;
}


$airPk = intval($_REQUEST['airPk']);
$retarr = get_airspace($airPk);
$jret = rjson_pack($retarr);

#print rjson_pack($retarr);
print $jret;
?>
