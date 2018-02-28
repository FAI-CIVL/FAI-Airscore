<?php
require 'authorisation.php';


//auth('system');
$link = db_connect();

// CompeGPS format
//G  WGS 84
//U  1
//W  1D-027 A 36.4402500000ºS 146.3607333333ºE 27-MAR-62 00:00:00 885.000000 WHITF RD/SNO
//W  1G-020 A 36.5787000000ºS 146.3786833333ºE 27-MAR-62 00:00:00 656.000000 MOYHU
//W  6S-034 A 36.7462000000ºS 146.9788500000ºE 27-MAR-62 00:00:00 1115.000000 MYSTIC LZ
// etc.
function ozi_header()
{
    return "OziExplorer Waypoint File Version 1.1\r\nWGS 84\r\nReserved 2\r\nReserved 3\r\n";
}

// Ozi Explorer format
//OziExplorer Waypoint File Version 1.1
//WGS 84
//Reserved 2
//Reserved 3
//1,ave016,-36.908967,145.245433,25569.00000,0,1,3,0,65535,Avenel,0,0,0,492,6,0,17
//2,ben016,-36.580660,145.991478,25569.00000,0,1,3,0,65535,Benalla,0,0,0,525,6,0,17
//3,bfd009,-37.191502,145.072060,25569.00000,0,1,3,0,65535,Broadford airspace,0,0,0,295,6,0,17
//4,bon030,-37.028333,145.850000,25569.00000,0,1,3,0,65535,Bonnie Doon,0,0,0,984,6,0,17
// etc
function compegps_header()
{
    return "G  WGS 84\r\nU  1\r\n";
}

if (array_key_exists('download', $_REQUEST))
{
    $regPk=intval($_REQUEST['download']);
    $format=addslashes($_REQUEST['format']);

    $sql = "SELECT N.*, R.* from tblRegion N, tblRegionWaypoint R where N.regPk=R.regPk and R.regPk=$regPk order by R.rwpName";

    $result = mysqli_query($link, $sql);
    $row = mysqli_fetch_assoc($result);
    $regname = $row['regDescription'];
    $regname = preg_replace('/\s+/', '', $regname);

    # nuke normal header ..
    header("Content-type: text/wpt");
    header("Content-Disposition: attachment; filename=\"$regname.wpt\"");
    header("Cache-Control: no-store, no-cache");

    if ($format == 'ozi')
    {
        print ozi_header();
    }
    else
    {
        print compegps_header();
    }

    $count = 1;
    do 
    {
        $name = $row['rwpName'];
        $lat = floatval($row['rwpLatDecimal']);
        $lon = floatval($row['rwpLongDecimal']);
        $alt = $row['rwpAltitude'];
        $falt = round($alt * 3.281);
        $desc = $row['rwpDescription'];
        $date = '01-JAN-00 00:00:00';
        # convert lat/lon to NESW appropriately
        # get some decent date ..
        if ($format == 'ozi')
        {
            $lat = round($lat,6);
            $lon = round($lon,6);
            print "$count,$name,$lat,$lon,25569.00000,0,1,3,0,65535,$desc,0,0,0,$falt,6,0,17\r\n";
        }
        else
        {
            // compegps
            if ($lat < 0)
            {
                $alat = abs($lat);
                $slat = "$alat" . "\272S";
            }
            else
            {
                $slat = "$lat" . "\272N";
            }
            if ($lon < 0)
            {
                $alon = abs($lon);
                $slon = "$alon" . "\272W";
            }
            else
            {
                $slon = "$lon" . "\272E";
            }
            print "W  $name A $slat $slon $date $alt $desc\r\n";
        }

        $count++;
    }
    while ($row = mysqli_fetch_assoc($result));
}
?>
