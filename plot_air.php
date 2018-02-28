<?php
require_once 'Sajax.php';

function get_airspace($trackid)
{
    $link = db_connect();
    $sql = "SELECT A.*, AW.* from tblAirspace A, tblAirspaceWaypoint AW where A.airPk=$trackid and AW.airPk=A.airPk order by AW.airOrder";
    
    $result = mysqli_query($link, $sql);
    $ret = [];
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
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
    
    $jret = json_encode($ret);
    
    return $jret;
}

sajax_init();
sajax_export("get_airspace");
sajax_handle_client_request();
?>

