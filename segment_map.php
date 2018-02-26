<?php
require 'authorisation.php';
require 'hc2.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

hchead();
echo '<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">';
echo '<title>Skyhigh Cup Tracklog</title>';
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

$link = db_connect();

$trackid = $_REQUEST['trackid'];

$tasPk=0;
$comName='airScore OLC';
$tasName='';
$sql = "SELECT CTT.tasPk,C.comName,T.tasName,T.tasTaskType FROM tblCompetition C, tblComTaskTrack CTT left outer join tblTask T on T.tasPk=CTT.tasPk where C.comPk=CTT.comPk and CTT.traPk=$trackid";
//$result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
$result = mysqli_query($link, $sql,$link) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
//if (mysql_num_rows($result) > 0)
if (mysqli_num_rows($result) > 0)
{
//    $tasPk = mysql_result($result,0,0);
    $tasPk = mysqli_result($result,0,0);
//    $comName = mysql_result($result,0,1);
    $comName = mysqli_result($result,0,1);
//    $tasName = mysql_result($result,0,2);
    $tasName = mysqli_result($result,0,2);
//    $tasTaskType = mysql_result($result,0,3);
    $tasTaskType = mysqli_result($result,0,3);
    if ($tasName)
    {
        $tasName = ' - ' . $tasName;
    }
    else
    {
        $tasName = '';
    }
}
if ($tasPk > 0 && $tasTaskType == 'RACE')
{
    $sql = "SELECT W.* FROM tblTaskWaypoint T, tblRegionWaypoint W where T.tasPk=$tasPk and W.rwpPk=T.rwpPk order by T.tawNumber";
//    $result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
    $result = mysqli_query($link, $sql,$link) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
    $prefix='rwp';
    $first = 1;
}
else
{
    $sql = "SELECT * FROM tblSegment where traPk=$trackid order by wptTime";
//    $result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
    $result = mysqli_query($link, $sql,$link) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
    $prefix='wpt';
    $first = 1;
}
echo "var polyline = new GPolyline(["; 
//while($row = mysql_fetch_array($result))
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
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

echo "map.setCenter(new GLatLng($clat, $clong), 13);\n";
echo "map.addOverlay(polyline);\n\n";

$sql = "SELECT * FROM tblBucket where traPk=$trackid order by bucTime";
//$result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql);
$first = 1;
$clat=0;
$clong=0;

echo "var polyline = new GPolyline(["; 
//while($row = mysql_fetch_array($result))
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    if ($first)
    {
        $first = 0;
    }
    else
    {
        echo ",\n";
    }
    echo "new GLatLng(" . $row['bucLatDecimal'] . "," . $row['bucLongDecimal'] . ")";
}
echo "],\"#ff0000\", 3, 1);\n";
echo "map.addOverlay(polyline);\n\n";

if ($tasPk > 0)
{
    $sql = "SELECT W.* FROM tblTaskWaypoint T, tblRegionWaypoint W where T.tasPk=$tasPk and W.rwpPk=T.rwpPk order by T.tawNumber";
//    $result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
    $result = mysqli_query($link, $sql,$link) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
    $prefix='rwp';
    $first = 1;
//    while($row = mysql_fetch_array($result))
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $clat = $row["${prefix}LatDecimal"];
        $clong = $row["${prefix}LongDecimal"];
        $cname = $row["${prefix}Name"];


        // tlabel.js stuff
        //echo "var tlabel = new TLabel();";
        //echo "tlabel.id = '$cname';";
        //echo "tlabel.anchorLatLng = new GLatLng ($clat, $clong);";
        //echo "tlabel.anchorPoint = 'bottomLeft';";
        //echo "tlabel.percentOpacity = 70;";
        //echo "tlabel.content = '<div style=\"padding: 0px 0px 8px 8px; background: url(images/point_bottom_left.png) no-repeat bottom left;\"><div style=\"background-color: #6666ff; padding: 2px; font-size: 0.7em;\"><nobr><a href=\"blackbirds.html?bird=924\">$cname</a></nobr></div></div>';";
        //echo "map.addTLabel(tlabel);";

        // An ELabel with all optional parameters in use 
        echo "var label = new ELabel(new GLatLng($clat,$clong), \"$cname\", \"waypoint\", new GSize(-40,0), 60);\n";
        echo "map.addOverlay(label);\n";
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
echo "<div id=\"vhead\"><h1>$comName $tasName</h1></div>\n";
$trackid = $_REQUEST['trackid'];
$comPk = intval($_REQUEST['comPk']);
menubar($comPk);

$link = db_connect();

$sql = "SELECT T.*, P.*, TR.* FROM tblPilot P, tblTrack T left outer join tblTaskResult TR on TR.traPk=T.traPk where T.pilPk=P.pilPk and T.traPk=$trackid limit 1";
//$result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql);
//if ($row = mysql_fetch_array($result))
if ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $name = $row['pilFirstName'] . " " . $row['pilLastName'];
    $date = $row['traStart'];
    $gmin = floor(($row['tarES'] - $row['tarSS']) / 60);
    $gsec = (($row['tarES'] - $row['tarSS'])/60 - $gmin) * 60;;
    if ($tasPk == 0)
    {
        $dist = round($row['traLength'] / 1000, 2);
    }
    else
    {
        $dist = round($row['tarDistance'] / 1000, 2);
    }
    if ($gmin > 0)
    {
        echo "<p><h2>$name at $date (goal: $dist kms, ${gmin}m ${gsec}s)</h2></p>";
    }
    else
    {
        echo "<p><h2>$name at $date ($dist kms)</h2></p>";
    }
}
// mysql_close($link);
mysqli_close($link);
?>
<div id="map" style="width: 100%; height: 600px"></div>
</div>
</body>
</html>

