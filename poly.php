<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml">
<head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8"/>
<title>Skyhigh Cup</title>
<style type="text/css">
v\:* {
behavior:url(#default#VML);
}
</style>
<script src="http://maps.google.com/maps?file=api&v=2&key=abcdefg" type="text/javascript">

var map = new GMap2(document.getElementById("map"));
map.addMapType(G_PHYSICAL_MAP);
map.setMapType(G_PHYSICAL_MAP);
map.addControl(new GSmallMapControl());
map.addControl(new GMapTypeControl());
map.setCenter(new GLatLng(37.4419, -122.1419), 13); 

// Add 10 markers in random locations on the map
var bounds = map.getBounds();
var southWest = bounds.getSouthWest();
var northEast = bounds.getNorthEast();
var lngSpan = northEast.lng() - southWest.lng();
var latSpan = northEast.lat() - southWest.lat();
for (var i = 0; i < 10; i++) 
{
  var point = new GLatLng(southWest.lat() + latSpan * Math.random(),
                          southWest.lng() + lngSpan * Math.random());
  map.addOverlay(new GMarker(point));
}

// Add a polyline with five random points. Sort the points by
// longitude so that the line does not intersect itself.
//var points = [];
//for (var i = 0; i < 5; i++) 
//{
//  points.push(new GLatLng(southWest.lat() + latSpan * Math.random(),
//                          southWest.lng() + lngSpan * Math.random()));
//}
//points.sort(function(p1, p2) 
//{
//  return p1.lng() - p2.lng();
//});

<?php

$link = mysql_connect('localhost', 'xc', '%MYSQLPASSWORD%')
    or die("Could not connect: " . mysql_error());

mysql_select_db('xcdb',$link) 
    or die ("Can\'t use database : " . mysql_error());

//$trackid = $_REQUEST['trackid'];
$trackid = 1;
$sql = "SELECT * FROM tblTrackLog where traPk=$trackid";

$result = mysql_query($sql,$link);
if (!$result)
{
    //echo "no results";
}

$first = 1;
while($row = mysql_fetch_array($result))
{
    if ($first == 1)
    {
        echo "map.setCenter(new GLatLng(37.4419, -122.1419), 13);";
        $first = 0;
    }
    $geometry = str_replace("LINESTRING (","", $row['geometry']);
    $geometry = str_replace(")","",$geometry);
    $points = explode(",",$geometry);
    $numpoints = sizeof($points);
    echo "var polyline = new GPolyline(["; 
    for ($i = 0; $i <= ($numpoints - 1); $i++) {
        $coordinates = explode(" ",$points[$i]);
        echo "new GPoint(" . $coordinates[0] . "," . $coordinates[1] . ")";
        if ($i != ($numpoints - 1)) {
            echo ",\n";
        } else {
            echo "\n";
        }
    }
    echo "],\"#ff0000\", 5, 1);\n";
    echo "map.addOverlay(polyline);\n\n";
}

mysql_close($link);
?>

//]]>
</script>
<body>
</body>
</html>

