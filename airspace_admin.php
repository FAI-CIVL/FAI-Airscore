<?php
require 'authorisation.php';
require 'format.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

auth('system');
$argPk = reqival('argPk');

function dms($pos, $ext)
{
    $h = floor($pos);
    $m = floor(($pos - $h) * 60);
    $s = floor( ((($pos - $h) * 60)  - $m) * 60 );

    if ($h < 0) 
    {
        $h = - $h;
    }

    $ret = sprintf("%02d:%02d:%02d ", $h, $m, $s);

    if ($pos > 0)
    {
        return $ret . substr($ext, 0, 1);
    }
    return $ret . substr($ext, 1, 1);
}

function nautical_miles($km)
{
    return $km / 1852.0;
}

if (reqexists('download'))
{
    //AC Q
    //AT 
    //AD 
    //AR1 
    //AN PARA 128.55
    //WD 400
    //AL 0
    //AH 40000
    //CO 
    //V D=+
    //V X=53:15.100 N 007:07.333 W
    //DB 53:18.098 N 007:07.333 W , 53:18.098 N 007:07.333 W

    $link = db_connect();
    $sql = "select * from tblAirspaceRegion where argPk=$argPk";
//    $result = mysql_query($sql,$link);
    $result = mysqli_query($link, $sql);
//    $row = mysql_fetch_array($result, MYSQL_ASSOC);
    $row = mysqli_fetch_assoc($result);
    $regname = $row['argRegion'];

    # nuke normal header ..
    header("Content-type: text/air");
    header("Content-Disposition: attachment; filename=\"CTR-$regname.txt\"");
    header("Cache-Control: no-store, no-cache");

    $sql = "select * from tblAirspace A, tblAirspaceRegion R
            where A.airPk in (             
                select airPk from tblAirspaceWaypoint W, tblAirspaceRegion R where
                R.argPk=$argPk and
                W.awpLatDecimal between (R.argLatDecimal-R.argSize) and (R.argLatDecimal+R.argSize) and
                W.awpLongDecimal between (R.argLongDecimal-R.argSize) and (R.argLongDecimal+R.argSize)
                group by (airPk))
            group by A.airName
            order by A.airName";
//    $result = mysql_query($sql,$link);
    $result = mysqli_query($link, $sql);

    $first = 0;
//    while ($air = mysql_fetch_array($result, MYSQL_ASSOC))
    while ($air = mysqli_fetch_assoc($result))
    {
        $airPk = $air['airPk'];
        $class = $air['airClass'];
        $name = $air['airName'];
        $base = $air['airBase'];
        $tops = $air['airTops'];
        $shape = $air['airShape'];
        $centrepk = $air['airCentreWP'];
        $radius = $air['airRadius'];

        echo "\nAC $class\n";
        echo "AN $name\n";
        echo "AL $base\n";
        echo "AH $tops\n";

        if ($shape == "circle")
        {
            $subsql = "SELECT AW.* from tblAirspaceWaypoint AW where AW.awpPk=$centrepk by AW.airOrder";
//            $subresult = mysql_query($subsql,$link);
            $subresult = mysqli_query($link, $subsql);
//            $subrow = mysql_fetch_array($subresult, MYSQL_ASSOC);
            $subrow = mysqli_fetch_assoc($subresult);
            $lat = $subrow['awpLatDecimal'];
            $lon = $subrow['awpLongDecimal'];
            echo "V X=" . dms($lat, "NS") . " " . dms($lon, "EW") . "\n";
            echo "DC " . nautical_miles($radius) . "\n";
        }
        else
        {
            // do waypoints ...
            $subsql = "SELECT A.*, AW.* from tblAirspace A, tblAirspaceWaypoint AW where A.airPk=$airPk and AW.airPk=A.airPk order by AW.airOrder";
//            $subresult = mysql_query($subsql,$link);
            $subresult = mysqli_query($link, $subsql);
//            while ($subrow = mysql_fetch_array($subresult, MYSQL_ASSOC))
            while ($subrow = mysqli_fetch_assoc($subresult))
            {
                $lat = $subrow['awpLatDecimal'];
                $lon = $subrow['awpLongDecimal'];
                echo "V X=" . dms($lat, "NS") . " " . dms($lon, "EW") . "\n";
            }
        }
    }
	exit(0);
}

function display_airspace_region($link, $argPk)
{
    $count = 1;
    $airtab = [];
    $airtab[] =  array(fb('Id'), fb('Name'), fb('Class'), fb('Shape'), fb('Base(m)'), fb('Top(m)'), '');

    if ($argPk == -1)
    {
        $sql = "select * from tblAirspace R order by R.airName";
    }
    else
    {
        $sql = "select * from tblAirspace R 
            where R.airPk in (             
                select airPk from tblAirspaceWaypoint W, tblAirspaceRegion R where
                R.argPk=$argPk and
                W.awpLatDecimal between (R.argLatDecimal-R.argSize) and (R.argLatDecimal+R.argSize) and
                W.awpLongDecimal between (R.argLongDecimal-R.argSize) and (R.argLongDecimal+R.argSize)
                group by (airPk))
            order by R.airName";
    }

//    $result = mysql_query($sql,$link);
    $result = mysqli_query($link, $sql);
//    while ($row = mysql_fetch_array($result, MYSQL_ASSOC))
    while ($row = mysqli_fetch_assoc($result))
    {
        $id = $row['airPk'];
        $name = $row['airName'];
        $airtab[] = array($id . ".",
         //fbut('submit', 'update', $id, 'up'),
         //fbut('submit', 'download', $id, 'download'),
         "<a href=\"airspace_map.php?airPk=$id&argPk=$argPk\">$name</a>",
         fb($row['airClass']),
         fb($row['airShape']),
         fb($row['airBase']),
         fb($row['airTops']),
         fbut('submit', 'delete', $id, 'del')
        );

        //waypoint_select($link, $tasPk, "waypoint$tawPk", $waypt);
        //echo " centre: $centname</a>";
        $count++;
    }
    echo ftable($airtab, '', '', '');
}

function display_regions($link)
{
    $count = 1;
    $airtab = [];
    $airtab[] =  array(fb('Id'), fb('Region Name'), fb('Latitude'), fb('Longitude'), fb('Size'));
    $sql = "SELECT * from tblAirspaceRegion R order by R.argRegion";
//    $result = mysql_query($sql,$link);
    $result = mysqli_query($link, $sql);
//    while ($row = mysql_fetch_array($result, MYSQL_ASSOC))
    while ($row = mysqli_fetch_assoc($result))
    {
        $id = $row['argPk'];
        $name = "<a href=\"airspace_admin.php?argPk=$id\">" . $row['argRegion'] . '</a>';
        $airtab[] = array($count . ".",
         //fbut('submit', 'update', $id, 'up'),
         //fbut('submit', 'delete', $id, 'del'),
         //fbut('submit', 'download', $id, 'download'),
         fb($name),
         fb($row['argLatDecimal']),
         fb($row['argLongDecimal']),
         fb($row['argSize'])
        );

        //waypoint_select($link, $tasPk, "waypoint$tawPk", $waypt);
        //echo " centre: $centname</a>";
        $count++;
    }
    echo ftable($airtab, '', '', '');
}
?>
<html><head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<div id="vhead"><h1>airScore admin</h1></div>
<?php
adminbar(0);
$link = db_connect();
echo '<p><h2>Airspace Administration</h2></p>';

if (reqexists('add'))
{
    $upfile = $_FILES['waypoints']['tmp_name'];
    $out = '';
    $retv = 0;
    exec(BINDIR . "airspace_openair.pl $upfile", $out, $retv);

    if ($retv)
    {
        echo "<b>Failed to upload your airspace properly.</b><br>\n";
        foreach ($out as $txt)
        {
            echo "$txt<br>\n";
        }
        echo "</div></body></html>\n";
        exit(0);
    }

    foreach ($out as $row)
    {
        echo $row ."<br>";
    }
}

if (reqexists('delete'))
{
    // implement a nice 'confirm'
    $delPk = reqival('delete');
    $query = "select * from tblAirspace where airPk=$delPk";
//    $result = mysql_query($query) or die('Airspace check failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Airspace check failed: ' . mysqli_connect_error());
//    $row = mysql_fetch_array($result);
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    $subregion = $row['airName'];

    #$query = "select * from tblTaskWaypoint T, tblRegionWaypoint W, tblRegion R where R.regPk=W.regPk and R.regPk=$delPk limit 1";
    #$result = mysql_query($query) or die('Delete check failed: ' . mysql_error());
    #if (mysql_num_rows($result) > 0)
    #{
    #    echo "Unable to delete $region ($delPk) as it is in use.\n";
    #    return;
    #}

    $query = "delete from tblAirspaceWaypoint where airPk=$delPk";
//    $result = mysql_query($query) or die('AirspaceWaypoint delete failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' AirspaceWaypoint delete failed: ' . mysqli_connect_error());
    $query = "delete from tblAirspace where airPk=$delPk";
//    $result = mysql_query($query) or die('Airspace delete failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Airspace delete failed: ' . mysqli_connect_error());

    echo "Airspace $subregion deleted<br>";
}

if (reqexists('create'))
{
    $region = reqsval('regname');
    $rlat = reqfval('reglat');
    $rlon = reqfval('reglon');
    $rsize = reqfval('regsize');

    $sql = "insert into tblAirspaceRegion (argRegion, argLatDecimal, argLongDecimal, argSize ) values ('$region', $rlat, $rlon, $rsize)";
//    $result = mysql_query($sql) or die('AirspaceRegion creation failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' AirspaceRegion creation failed: ' . mysqli_connect_error());

    echo "Region $region added<br>";
}

$extra = "";
if ($argPk > 0)
{
    $extra = "?argPk=$argPk";
}
echo "<form enctype=\"multipart/form-data\" action=\"airspace_admin.php$extra\" name=\"waypoint\" method=\"post\">";
echo "<input type=\"hidden\" name=\"MAX_FILE_SIZE\" value=\"1000000000\">";

if ($argPk == 0)
{
    display_regions($link, $argPk);

    echo "<hr>";
    echo "Create Region: " . fin('regname', '', 10);
    echo "Latitude: " . fin('reglat', '', 8);
    echo "Longitude: " . fin('reglon', '', 8);
    echo "Size(deg): " . fin('regsize', '', 4);
    echo fis('create', 'Create', 4);
}
else
{
    display_airspace_region($link, $argPk);
    echo "<hr>";
    echo "Download Region Airspace (OpenAir Format): " . fis('download', 'Download', 10);
}

echo "<hr>";
echo "Load Airspace: " . fin('region', '', 10);
echo "OpenAir File: <input type=\"file\" name=\"waypoints\">";
echo fis('add', 'Add Airspace', 10);
echo "<hr>";

echo "</form>";
?>
</div>
</body>
</html>

