<?php
require 'authorisation.php';
require 'hc2.php';

hchead();
echo '<title>Waypoint Map</title>';
hccss();
hcmapjs();
?>
<script type="text/javascript">
    //<![CDATA[
function load() 
{
    if (GBrowserIsCompatible()) 
    {
<?php
echo "var map = new GMap2(document.getElementById(\"map\"));\n";
echo "map.addMapType(G_PHYSICAL_MAP);\n";
echo "map.setMapType(G_PHYSICAL_MAP);\n";
echo "map.addControl(new GSmallMapControl());\n";
echo "map.addControl(new GMapTypeControl());\n";
echo "map.addControl(new GScaleControl());\n";

$link = db_connect();

$tasPk = intval($_REQUEST['tasPk']);
//$sr = intval($_REQUEST['sr']);

$sql = "SELECT T.regPk, C.comName, T.tasName, T.tasDistance, C.comPk FROM tblCompetition C, tblTask T where T.tasPk=$tasPk and C.comPk=T.comPk";
$result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
if (mysql_num_rows($result) > 0)
{
    $regPk = mysql_result($result,0,0);
    $comName = mysql_result($result,0,1);
    $tasName = mysql_result($result,0,2);
    $tasDistance = mysql_result($result,0,3);
    $comPk = mysql_result($result,0,4);
}
if ($tasPk > 0)
{
    $sql = "SELECT W.* FROM tblTaskWaypoint T, tblRegionWaypoint W where T.tasPk=$tasPk and W.rwpPk=T.rwpPk order by T.tawNumber";
    $result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
    $prefix='rwp';
    $first = 1;
}

echo "var polyline = new GPolyline(["; 
while($row = mysql_fetch_array($result))
{
    if ($first)
    {
        $first = 0;
        $clat = $row["${prefix}LatDecimal"];
        $clong = $row["${prefix}LongDecimal"];
    }
    else
    {
        echo ",\n";
    }
    echo "new GLatLng(" . $row["${prefix}LatDecimal"] . "," . $row["${prefix}LongDecimal"] . ")";
}
echo "],\"#0000ff\", 2, 1);\n";

$sr = 0;
if ($tasPk > 0)
{
    $sql = "SELECT T.* FROM tblShortestRoute T where T.tasPk=$tasPk order by T.ssrNumber";
    $result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
    $first = 1;
    $prefix = 'ssr';

    echo "var sroute = new GPolyline(["; 
    while($row = mysql_fetch_array($result))
    {
        $sr = 1;
        if ($first)
        {
            $first = 0;
            $clat = $row["${prefix}LatDecimal"];
            $clong = $row["${prefix}LongDecimal"];
        }
        else
        {
            echo ",\n";
        }
        echo "new GLatLng(" . $row["${prefix}LatDecimal"] . "," . $row["${prefix}LongDecimal"] . ")";
    }
    echo "],\"#333333\", 2, 1);\n";

}

echo "map.setCenter(new GLatLng($clat, $clong), 13);\n";
echo "map.addOverlay(polyline);\n\n";
if ($sr > 0)
{
    echo "map.addOverlay(sroute);\n\n";
}


if ($tasPk > 0)
{
    $sql = "SELECT T.tawRadius, W.* FROM tblTaskWaypoint T, tblRegionWaypoint W where T.tasPk=$tasPk and W.rwpPk=T.rwpPk order by T.tawNumber";
    $result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
    $prefix='rwp';
    $first = 1;
    while($row = mysql_fetch_array($result))
    {
        $clat = $row["${prefix}LatDecimal"];
        $clong = $row["${prefix}LongDecimal"];
        $cname = $row["${prefix}Name"];
        $crad = $row["tawRadius"];

        // An ELabel with all optional parameters in use 
        echo "var pos = new GLatLng($clat,$clong);\n";
        echo "var label = new ELabel(pos, \"$cname\", \"waypoint\", new GSize(-40,0), 60);\n";
        echo "map.addOverlay(label);\n";

        // add a radius circle
        echo "var sz = GSizeFromMeters(map, pos, $crad*2,$crad*2);\n";
        #echo "map.addOverlay(new EInsert(pos, \"circle.png\", sz, map.getZoom()));\n";
        echo "map.addOverlay(new EInsert(pos, \"circle.png\", sz, 13));\n";
    }
}

// mysql_close($link);
?>
    }
}

    //]]>
</script>
</head>
<body onload="load()" onunload="GUnload()">
<div id="container">
<?php
$taskm = round($tasDistance/1000,1);
hcheadbar("$tasName - $comName",2);
echo "<div id=\"content\">";
echo "<div id=\"map\" style=\"width: 800px; height: 600px\"></div>";
$link = db_connect();
$count = 1;
$sql = "select T.*, RW.* from tblTaskWaypoint T, tblRegionWaypoint RW where T.tasPk=$tasPk and RW.rwpPk=T.rwpPk order by T.tawNumber";
$result = mysql_query($sql,$link) or die('Task Waypoint Selection failed: ' . mysql_error());
while ($row = mysql_fetch_array($result))
{
    $tawPk = $row['tawPk'];
    $number = $row['tawNumber'];
    $name = $row['rwpName'];
    $rwpPk = $row['rwpPk'];
    $wtype = $row['tawType'];
    $how = $row['tawHow'];
    $shape = $row['tawShape'];
    $radius = $row['tawRadius'];

    echo "$number. $name - $wtype - ${radius}m ($how $shape).";
    echo "<br>\n";

    $count++;
}
echo "<b>Total distance: $taskm kms</b>";
echo "<form action=\"download_routes.php?tasPk=$tasPk\" name=\"down\" method=\"post\">";
echo "<input type=\"submit\" name=\"downway\" value=\"Download Route\"></form>";
echo "<form action=\"waypoint_map.php?regPk=$regPk\" name=\"way\" method=\"post\">";
echo "<input type=\"submit\" name=\"view\" value=\"View Waypoints\"></form>";
mysql_close($link);
?>
</div>
</div>
</body>
</html>

