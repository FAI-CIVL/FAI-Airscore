<?php

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

require 'authorisation.php';
require 'hc2.php'

hchead();
echo '<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">';
echo '<title>Waypoint Map</title>';
hcmapjs();
?>
<script type="text/javascript">
    //<![CDATA[

function load() 
{
    if (GBrowserIsCompatible()) 
    {
<?php

$link = db_connect();
$regPk = intval($_REQUEST['regPk']);

echo "var map = new GMap2(document.getElementById(\"map\"));\n";
echo "map.addMapType(G_PHYSICAL_MAP);\n";
echo "map.setMapType(G_PHYSICAL_MAP);\n";
echo "map.addControl(new GSmallMapControl());\n";
echo "map.addControl(new GMapTypeControl());\n";

$sql = "SELECT * FROM tblRegion where regPk=$regPk";
// $result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' MySQL connection failed: ' . mysqli_connect_error());
// $rcentre = mysql_result($result,0,1);
// $regdesc = mysql_result($result,0,3);
$rcentre = mysqli_result($result,0,1);
$regdesc = mysqli_result($result,0,3);

$prefix = 'rwp';
$sql = "SELECT * FROM tblRegionWaypoint where regPk=$regPk";
// $result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' MySQL connection failed: ' . mysqli_connect_error());

$first = 0;
// while($row = mysql_fetch_array($result))
while($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $clat = $row["${prefix}LatDecimal"];
    $clong = $row["${prefix}LongDecimal"];
    $cname = $row["${prefix}Name"];

    if ($first == 0)
    {
        echo "map.setCenter(new GLatLng($clat, $clong), 11);\n";
        $first = 1;
    }

    echo "var label = new ELabel(new GLatLng($clat,$clong), \"$cname\", \"waypoint\", new GSize(0,0), 60);\n";
    echo "map.addOverlay(label);\n";
}

//echo "map.addOverlay(polyline);\n\n";

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
echo "<div id=\"vhead\"><h1>$regdesc Waypoints</h1></div>\n";
adminbar(0);

// mysql_close($link);
mysqli_close($link);
?>
<div id="map" style="width: 800px; height: 600px"></div>
</div>
</body>
</html>

