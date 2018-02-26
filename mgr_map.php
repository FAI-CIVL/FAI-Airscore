<?php
require 'authorisation.php';
require 'hc2.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

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
$authorised = check_auth('system');

$link = db_connect();
$regPk = intval($_REQUEST['regPk']);

if ($authorised && array_key_exists('add', $_REQUEST))
{
    $name = addslashes($_REQUEST['name']);
    $lat = addslashes($_REQUEST["lat"]);
    $lon = addslashes($_REQUEST["lon"]);
    $alt = addslashes($_REQUEST["alt"]);
    $desc = rtrim(addslashes($_REQUEST["desc"]));
    $sql = "insert into tblRegionWaypoint (regPk, rwpName, rwpLatDecimal, rwpLongDecimal, rwpAltitude, rwpDescription) values ($regPk,'$name',$lat,$lon,$alt,'$desc')";
    if ($name != '' && $lat != 0)
    {
//        $result = mysql_query($sql,$link) or die("Failed to insert waypoint ($name): " . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Failed to insert waypoint ($name): ' . mysqli_connect_error());
    }
    else
    {
        echo "alert('Can\'t add 0 waypoint');\n";
    }
}

if ($authorised && array_key_exists('delete', $_REQUEST))
{
    $delname = addslashes($_REQUEST['upname']);
    if ($delname != '')
    {
        $sql = "delete from tblRegionWaypoint where regPk=$regPk and rwpName='$delname'";
//        $result = mysql_query($sql,$link) or die("Failed to delete waypoint ($delname): " . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Failed to delete waypoint ($delname): ' . mysqli_connect_error());

    }
}

if ($authorised && array_key_exists('update', $_REQUEST))
{
    $name = addslashes($_REQUEST['upname']);
    $rwpPk = intval($_REQUEST["rwpPk"]);
    $lat = floatval($_REQUEST["uplat"]);
    $lon = floatval($_REQUEST["uplon"]);
    $alt = floatval($_REQUEST["upalt"]);
    $desc = rtrim(addslashes($_REQUEST["updesc"]));
    $sql = "update tblRegionWaypoint set rwpName='$name', rwpLatDecimal=$lat, rwpLongDecimal=$lon, rwpAltitude=$alt, rwpDescription='$desc' where rwpPk=$rwpPk";
    if ($name != '' && $lat != 0)
    {
//        $result = mysql_query($sql,$link) or die("Failed to update waypoint ($name): " . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Failed to update waypoint ($name): ' . mysqli_connect_error());
    }
    else
    {
        echo "alert('Can\'t update 0 waypoint');\n";
    }
}

// Ok - do the map stuff
echo "var map = new GMap2(document.getElementById(\"map\"));\n";
echo "var points = new Object();\n";
echo "var marker;\n";
echo "map.addMapType(G_PHYSICAL_MAP);\n";
echo "map.setMapType(G_PHYSICAL_MAP);\n";
echo "map.addControl(new GSmallMapControl());\n";
echo "map.addControl(new GMapTypeControl());\n";
echo "map.addControl(new GScaleControl());\n";
echo "var mgr = new GMarkerManager(map);\n";

$sql = "SELECT * FROM tblRegion WHERE regPk=$regPk";
//$result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql);
//$rcentre = mysql_result($result,0,1);
$rcentre = mysqli_result($result,0,1);
//$regdesc = mysql_result($result,0,3);
$regdesc = mysqli_result($result,0,3);

$prefix = 'rwp';
$sql = "SELECT * FROM tblRegionWaypoint WHERE regPk=$regPk";
//$result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql);

$first = 0;
$count = 0;
$waylist = [];
//while($row = mysql_fetch_array($result))
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $clat = $row["${prefix}LatDecimal"];
    $clong = $row["${prefix}LongDecimal"];
    $calt = $row["${prefix}Altitude"];
    $cname = $row["${prefix}Name"];
    $cdesc = rtrim($row["${prefix}Description"]);
    $crwppk = $row["${prefix}Pk"];
    $count++;

    if ($first == 0)
    {
        echo "map.setCenter(new GLatLng($clat, $clong), 10);\n";
    }

    echo "var label$count = new ELabel(new GLatLng($clat,$clong), \"$cname\", \"waypoint\", new GSize(20,10), 60);\n";
    //echo "map.addOverlay(label$count);\n";
    echo "label$count.makeDraggable();\n";
    echo "GEvent.addListener(label$count, \"dragend\", function() {\n";
    echo "    document.forms['wayptadmin'].elements[\"upname\"].value = \"$cname\";";
    echo "    document.forms['wayptadmin'].elements[\"uplat\"].value = label$count.getPoint().lat();";
    echo "    document.forms['wayptadmin'].elements[\"uplon\"].value = label$count.getPoint().lng();";
    echo "    document.forms['wayptadmin'].elements[\"upalt\"].value = $calt;";
    echo "    document.forms['wayptadmin'].elements[\"updesc\"].value = \"$cdesc\";";
    echo "    document.forms['wayptadmin'].elements[\"rwpPk\"].value = \"$crwppk\";";
    //echo "    this.forms['wayptadmin'].alt_$cname = ";
    echo "    alert(\"object moved to \" + label$count.getPoint().lat() + \" \" + label$count.getPoint().lng());\n";
    //echo "    alert(\"object moved\");\n";
    echo "});\n";

    if ($authorised && ($first == 0))
    {
        echo "marker = new GMarker(new GLatLng($clat, $clong),{draggable: true});\n";
        echo "map.addOverlay(marker);\n";
        echo "marker.enableDragging();\n";
        echo "GEvent.addListener(marker, \"dragend\", function() {\n";
        echo "    document.forms['wayptadmin'].elements[\"lat\"].value = marker.getPoint().lat();";
        echo "    document.forms['wayptadmin'].elements[\"lon\"].value = marker.getPoint().lng();";
        //echo "    this.forms['wayptadmin'].alt_$cname = ";
        echo "    alert(\"new waypoint marker moved to \" + marker.getPoint().lat() + \" \" + marker.getPoint().lng());\n";
        //echo "    alert(\"object moved\");\n";
        echo "});\n";

        $first = 1;
    }
    $waylist[$cname] = array( lat => $clat, lon => $clong, alt => $calt, desc => $cdesc );
    echo "points[\"$cname\"] = label$count;\n";
}

echo "mgr.addMarkers(points, 0, 17);\n";
echo "mgr.refresh();\n";


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

//mysql_close($link);
?>
<div id="map" style="width: 800px; height: 600px"></div>
<?php
if ($authorised)
{
echo "<form action=\"waypoint_map.php?regPk=$regPk\" name=\"wayptadmin\" method=\"post\">";
echo "Name:<input type=\"text\" name=\"name\" size=10>";
echo "Desc:<input type=\"text\" name=\"desc\" size=15>";
echo "Lat:<input type=\"text\" name=\"lat\" value=\"0\" size=10>";
echo "Lon:<input type=\"text\" name=\"lon\" value=\"0\" size=10>";
echo "Alt:<input type=\"text\" name=\"alt\" value=\"100\" size=3>";
echo "<input type=\"submit\" name=\"add\" value=\"Add Waypoint\"><br>";
echo "Name:<input type=\"text\" name=\"upname\" size=10>";
echo "<input type=\"hidden\" name=\"rwpPk\">";
echo "Desc:<input type=\"text\" name=\"updesc\" size=15>";
echo "Lat:<input type=\"text\" name=\"uplat\" value=\"0\" size=10>";
echo "Lon:<input type=\"text\" name=\"uplon\" value=\"0\" size=10>";
echo "Alt:<input type=\"text\" name=\"upalt\" value=\"100\" size=3>";
echo "<input type=\"submit\" name=\"update\" value=\"Update\">";
echo "<input type=\"submit\" name=\"delete\" value=\"Delete\"><br>";
echo "</form>";
}
?>

</div>
</body>
</html>

