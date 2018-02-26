<?php
require 'authorisation.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

//auth('system');
$link = db_connect();

if (array_key_exists('tasPk', $_REQUEST))
{
    // implement a nice text file output
    #G  WGS 84
    #U  1
    #W  1D-027 A 36.4402500000ºS 146.3607333333ºE 27-MAR-62 00:00:00 885.000000 WHITF RD/SNO
    #W  1G-020 A 36.5787000000ºS 146.3786833333ºE 27-MAR-62 00:00:00 656.000000 MOYHU
    #W  6S-034 A 36.7462000000ºS 146.9788500000ºE 27-MAR-62 00:00:00 1115.000000 MYSTIC LZ
    # etc.

    $tasPk=intval($_REQUEST['tasPk']);

    $sql = "SELECT T.tasName from tblTask T where T.tasPk=$tasPk";
//    $result = mysql_query($sql,$link) or die("Can't get task: " . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Cannot get task: ' . mysqli_connect_error());
//    $tname = mysql_result($result, 0, 0);
    $tname = mysqli_result($result, 0, 0);

    $sql = "SELECT T.*, R.* from tblTaskWaypoint T, tblRegionWaypoint R where T.tasPk=$tasPk and R.rwpPk=T.rwpPk order by T.tawNumber";

//    $result = mysql_query($sql,$link);
    $result = mysqli_query($link, $sql);
    # nuke normal header ..
    header("Content-type: text/wpt");
    header("Cache-Control: no-store, no-cache");
    header("Content-Disposition: attachment; filename=\"task-$tasPk.wpt\"");

    print "G  WGS 84\n";
    print "U  1\n";
    print "R  16711680,$tname,1,-1\n";
//    while($row = mysql_fetch_array($result))
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $name = $row['rwpName'];
        $lat = floatval($row['rwpLatDecimal']);
        if ($lat < 0)
        {
            $alat = abs($lat);
            $slat = "$alat" . "\272S";
        }
        else
        {
            $slat = "$lat" . "\272N";
        }
        $lon = floatval($row['rwpLongDecimal']);
        if ($lon < 0)
        {
            $alon = abs($lon);
            $slon = "$alon" . "\272W";
        }
        else
        {
            $slon = "$lon" . "\272E";
        }
        $alt = $row['rwpAltitude'];
        $desc = $row['rwpDescription'];
        $date = '01-JAN-00 00:00:00';
        # convert lat/lon to NESW appropriately
        # get some decent date ..
        print "W  $name A $slat $slon $date $alt $desc\n";
    }
}

?>

