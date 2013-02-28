<?php
require 'authorisation.php';
require 'format.php';
require 'hc2v3.php';

hchead();
echo '<title>Submit Landing Pin</title>';
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

$link = db_connect();
$regPk = intval($_REQUEST['comPk']);
$regPk = intval($_REQUEST['regPk']);

if (array_key_exists('submitpin', $_REQUEST))
{
    $hgfa = addslashes($_REQUEST['hgfanum']);
    $name = addslashes(strtolower($_REQUEST['lastname']));
    $route = reqival('route');
    $comid = reqival('comid');

    $link = db_connect();
    $query = "select pilPk, pilHGFA from tblPilot where pilLastName='$name'";
    $result = mysql_query($query) or die('Query failed: ' . mysql_error());

    $member = 0;
    while ($row=mysql_fetch_array($result))
    {
        if ($hgfa == $row['pilHGFA'])
        {
            $pilPk = $row['pilPk'];
            $member = 1;
        }
    }

#    if ($restrict == 'registered')
#    {
#        $query = "select * from tblRegistration where comPk=$comid and pilPk=$pilPk";
#        $result = mysql_query($query) or die('Registration query failed: ' . mysql_error());
#        if (mysql_num_rows($result) == 0)
##        {
#            $member = 0;
#        }
#    }
##

    $gmtimenow = time() - (int)substr(date('O'),0,3)*60*60;
    if ($gmtimenow > ($until + 7*24*3600))
    {
        echo "<b>The submission period for tracks has closed ($until).</b><br>\n";
        echo "Contact $contact if you're having an access problem.<br>\n";
        echo "</div></body></html>\n";
        exit(0);
    }
    if ($member == 0)
    {
        echo "<b>Only registered pilots may submit tracks.</b><br>\n";
        echo "Contact $contact if you're having an access problem.<br>\n";
        echo "</div></body></html>\n";
        exit(0);
    }
}

$sql = "SELECT * FROM tblRegion WHERE regPk=$regPk";
$result = mysql_query($sql,$link);
$row = mysql_fetch_array($result);
$rcentre = intval($row['regCentre']);
$regdesc = $row['regDescription'];

$xlat = -37.0;
$xlon = 143.644;
$xname = 'Somewhere';
if ($rcentre != 0)
{
    $sql = "SELECT rwpLatDecimal, rwpLongDecimal, rwpName FROM tblRegionWaypoint WHERE rwpPk=$rcentre";
    $result = mysql_query($sql,$link) or die("Failed to get waypoint for region centre: " . mysql_error());
    $xlat = mysql_result($result,0,0);
    $xlon = mysql_result($result,0,1);
    $xname = mysql_result($result,0,2);
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

echo "points[\"$cname\"] = add_label(map,0,$xlat,$xlon,\"$xname\",\"0\",\"\",\"0\");\n";

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

//$waylist[$cname] = array( 'lat' => $clat, 'lon' => $clon, 'alt' => $calt, 'desc' => $cdesc );
//echo "points[\"$cname\"] = add_label(map,$authorised,$clat,$clon,\"$cname\",\"$calt\",\"$cdesc\",\"$crwppk\");\n";
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

echo "<form action=\"submit_pin.php?comPk=$comPk\" name=\"wayptadmin\" method=\"post\">";
$igcarr[] = array('HGFA Number', "<input name=\"hgfanum\" type=\"text\">", 'Last Name', "<input name=\"lastname\" type=\"text\">");

if ($comClass == 'PG')
{
    $classarr = fselect('dhv', '2/3', array('novice' => '1', 'fun' => '1/2', 'sports' => '2', 'serial' => '2/3', 'competition' => 'competition' ));
}
elseif ($comClass == 'HG')
{
    $classarr = fselect('dhv', 'open', array('floater' => 'floater', 'kingpost' => 'kingpost', 'open' => 'open', 'rigid' => 'rigid' ));
}
else 
{
    $classarr = fselect('dhv', '2', array('pg-novice' => '1', 'pg-fun' => '1/2', 'pg-sport' => '2', 'pg-serial' => '2/3', 'pg-comp' => 'competition', 'hg-floater' => 'floater', 'hg-kingpost' => 'kingpost', 'hg-open' => 'open', 'hg-rigid' => 'rigid' ));
}
$igcarr[] = array('Glider', '<input name="glider" type="text">', '', $classarr, fis("submitpin", "Submit PIN", 10));

echo ftable($igcarr, '', '', '');
echo "</form>";
?>

</div>
</body>
</html>

