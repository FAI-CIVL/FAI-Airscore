<?php
require 'authorisation.php';
require 'format.php';
require 'hc2v3.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

hchead();
echo '<title>Waypoint Map</title>';
hccss();
hcmapjs();

?>

<script type="text/javascript">
    //<![CDATA[
var map;
function add_label(map,auth,lat,lon,name,alt,desc,key)
{
    var label;

    label = new ELabel(map, new google.maps.LatLng(lat,lon), name, "waypoint", new google.maps.Size(0,0), 60);
    if (auth)
    {
        label.makeDraggable();
    }
    google.maps.event.addListener(label, "dragend", function() {
        document.forms['wayptadmin'].elements["upname"].value = name;
        document.forms['wayptadmin'].elements["uplat"].value = label.getPosition().lat().toFixed(6);
        document.forms['wayptadmin'].elements["uplon"].value = label.getPosition().lng();
        document.forms['wayptadmin'].elements["upalt"].value = alt;
        document.forms['wayptadmin'].elements["updesc"].value = desc;
        document.forms['wayptadmin'].elements["rwpPk"].value = key;

        // get the new elevation
        var elevator = new google.maps.ElevationService();
        var locations = [];
        locations.push(label.getPosition());
        var positionalRequest = {'locations': locations};
        // Initiate the location request
        elevator.getElevationForLocations(positionalRequest, function(results, status) {
                if (status == google.maps.ElevationStatus.OK)
                {
                    // Retrieve the first result
                    if (results[0])
                    {
                        var alt = results[0].elevation.toFixed(1);
                        document.forms['wayptadmin'].elements["upalt"].value = alt;
                    }
                }
            });

        //echo "    this.forms['wayptadmin'].alt_$cname = ";
        //alert("object moved to " + label.getPosition().lat() + " " + label.getPosition().lng());
        });
    return label;
}
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

if ($authorised && array_key_exists('centre', $_REQUEST))
{
    $cent = intval($_REQUEST['centrerwp']);
    $sql = "update tblRegion set regCentre=$cent where regPk=$regPk";
//    $result = mysql_query($sql,$link) or die("Failed to update region centre: " . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Failed to update region centre: ' . mysqli_connect_error());
}

$sql = "SELECT * FROM tblRegion WHERE regPk=$regPk";
// $result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql);
// $row = mysql_fetch_array($result);
$row = mysqli_fetch_array($result, MYSQLI_BOTH);
$rcentre = intval($row['regCentre']);
$regdesc = $row['regDescription'];

$xlat = -37.0;
$xlon = 143.644;
if ($rcentre != 0)
{
    $sql = "SELECT rwpLatDecimal, rwpLongDecimal FROM tblRegionWaypoint WHERE rwpPk=$rcentre";
//    $result = mysql_query($sql,$link) or die("Failed to get waypoint for region centre: " . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Failed to get waypoint for region centre: ' . mysqli_connect_error());
//    $xlat = mysql_result($result,0,0);
//    $xlon = mysql_result($result,0,1);
    $xlat = mysqli_result($result,0,0);
    $xlon = mysqli_result($result,0,1);
}


// Ok - do the map stuff
echo "
function initialize() 
{
    var points = new Object();
    var marker;
    var moptions =
        {
            zoom: 10,
            center: new google.maps.LatLng($xlat, $xlon),
            mapTypeId: google.maps.MapTypeId.TERRAIN,
            mapTypeControl: true,
            mapTypeControlOptions: {
                style: google.maps.MapTypeControlStyle.DROPDOWN_MENU
            },
            zoomControl: true,
            zoomControlOptions: {
                style: google.maps.ZoomControlStyle.SMALL
            },
            panControl: true,
            zoomControl: true,
            scaleControl: true
        };
    map = new google.maps.Map(document.getElementById(\"map\"), moptions);
    //map.setMapTypeId(google.maps.MapTypeId.TERRAIN);
    ";

$waypoints = [];
$prefix = 'rwp';
$sql = "SELECT * FROM tblRegionWaypoint WHERE regPk=$regPk";
// $result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql);

$first = 0;
$count = 0;
$waylist = [];
// while($row = mysql_fetch_array($result))
while($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $clat = $row["${prefix}LatDecimal"];
    $clon = $row["${prefix}LongDecimal"];
    $calt = $row["${prefix}Altitude"];
    $cname = $row["${prefix}Name"];
    $cdesc = rtrim($row["${prefix}Description"]);
    $crwppk = $row["${prefix}Pk"];
    $waypoints[$cname] = $crwppk;
    $count++;

    if ($first == 0)
    {
        if ($xlat == 0)
        {
            $xlat = $clat;
            $xlon = $clon;
        }
        //echo "map.setCenter(new google.maps.LatLng($xlat, $xlong), 10);\n";
    }

    $waylist[$cname] = array( 'lat' => $clat, 'lon' => $clon, 'alt' => $calt, 'desc' => $cdesc );
    echo "points[\"$cname\"] = add_label(map,$authorised,$clat,$clon,\"$cname\",\"$calt\",\"$cdesc\",\"$crwppk\");\n";
}


        if ($authorised)
        {
            echo "marker = new google.maps.Marker({
                position: new google.maps.LatLng($xlat, $xlon),
                map: map, 
                draggable: true});\n";
            echo "marker.setMap(map);\n";
            echo "google.maps.event.addListener(marker, \"dragend\", function() {
                document.forms['wayptadmin'].elements[\"lat\"].value = marker.getPosition().lat().toFixed(6);
                document.forms['wayptadmin'].elements[\"lon\"].value = marker.getPosition().lng().toFixed(6);
                // get the new elevation
                var elevator = new google.maps.ElevationService();
                var locations = [];
                locations.push(marker.getPosition());
                var positionalRequest = {'locations': locations};
                // Initiate the location request
                elevator.getElevationForLocations(positionalRequest, function(results, status) {
                        if (status == google.maps.ElevationStatus.OK)
                        {
                            // Retrieve the first result
                            if (results[0])
                            {
                                var alt = results[0].elevation.toFixed(1);
                                document.forms['wayptadmin'].elements[\"alt\"].value = alt;
                            }
                        }
                    });
            });\n";
            $first = 1;
        }
//echo "var next_point = $count;\n";

// mysql_close($link);
echo "}\n";
echo "google.maps.event.addDomListener(window, 'load', initialize);";
echo "    //]]>
</script>
</head>
<body>\n";
hcheadbar("$regdesc Waypoints",3);
echo "<div id=\"content\">";
// Put the map on ..
echo "<div id=\"map\" style=\"width: 100%; height: 600px\"></div>";

if ($authorised)
{
echo "<form action=\"waypoint_map.php?regPk=$regPk\" name=\"wayptadmin\" method=\"post\">";
echo "Name:" . fin('name', '', 10);
echo "Desc:" . fin('desc', '', 15);
echo "Lat:" . fin('lat', '0', 11);
echo "Lon:" . fin('lon', '0', 11);
echo "Alt:" . fin('alt', '100', 4) . "&nbsp;";
echo fis('add', 'Add Waypoint', '') . "<br>";
echo "Name:" . fin('upname', '', 10);
echo "<input type=\"hidden\" name=\"rwpPk\">";
echo "Desc:" . fin('updesc', '', 15);
echo "Lat:" . fin('uplat', '0', 11);
echo "Lon:" . fin('uplon', '0', 11);
echo "Alt:" . fin('upalt', '100', 4) . "&nbsp;";
echo fis('update', 'Update', '') . fis('delete', 'Delete', '') . "<br>";
echo "Centre: ";
ksort($waypoints);
output_select('centrerwp',$rcentre,$waypoints);
echo "<input type=\"submit\" name=\"centre\" value=\"Set Centre\"><br>";
echo "</form>";
}

echo "<form action=\"download_waypoints.php?download=$regPk\" name=\"down\" method=\"post\">";
echo "<input type=\"submit\" name=\"downway\" value=\"Download CompeGPS\"></form>";
echo "<form action=\"download_waypoints.php?download=$regPk&format=ozi\" name=\"down\" method=\"post\">";
echo "<input type=\"submit\" name=\"downway\" value=\"Download Ozi\"></form>";
?>

</div>
</body>
</html>

