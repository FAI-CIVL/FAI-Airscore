<?php
require 'authorisation.php';
require 'format.php';
require 'hc2v3.php';
require 'dbextra.php';

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
$comPk = reqival('comPk');
$regPk = reqival('regPk');
$tasPk = 0;

if (reqexists('tasPk'))
{
    $tasPk = reqival('tasPk');
}

$tasks = [];
if ($tasPk == 0)
{

    $today = getdate();
    $tdate = sprintf("%04d-%02d-%02d", $today['year'], $today['mon'], $today['mday']);

    $query = "select * from tblTask where comPk=$comPk and tasTaskType='free-pin' and tasDate <= '$tdate' order by tasDate";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task query failed: ' . mysqli_connect_error());
    while ($row = mysqli_fetch_assoc($result))
    {
        $tasks[$row['tasName']] = $row['tasPk'];
        if ($row['regPk'] > 0)
        {
            $regPk = $row['regPk'];
        }
        $tasPk = $row['tasPk'];
    }
}


$sql = "SELECT * FROM tblRegion WHERE regPk=$regPk";
$result = mysqli_query($link, $sql);
$row = mysqli_fetch_array($result, MYSQLI_BOTH);
$rcentre = intval($row['regCentre']);
$regdesc = $row['regDescription'];

$xlat = -37.0;
$xlon = 143.644;
$xname = 'Somewhere';
if ($rcentre != 0)
{
    $sql = "SELECT rwpLatDecimal, rwpLongDecimal, rwpName FROM tblRegionWaypoint WHERE rwpPk=$rcentre";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Failed to get waypoint for region centre: ' . mysqli_connect_error());
    $xla = mysqli_result($result,0,0);
    $xlon = mysqli_result($result,0,1);
    $xname = mysqli_result($result,0,2);
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

mysqli_close($link);

    //ovlay = new HtmlControl(ovhtml, { visible:false, selectable:true, printable:true } );
    //map.addControl(ovlay, new GControlPosition(G_ANCHOR_BOTTOM_RIGHT, new GSize(10, 10)));
    //ovlay.setVisible(true);

echo "}\n";
echo "google.maps.event.addDomListener(window, 'load', initialize);";
echo "    //]]>
</script>
</head>
<body>\n";

if (reqexists('submitpin'))
{
    $hgfa = reqsval('hgfanum');
    $name = addslashes(strtolower($_REQUEST['lastname']));
    $route = reqival('route');

    $lat = addslashes($_REQUEST["lat"]);
    $lon = addslashes($_REQUEST["lon"]);

    $query = "select pilPk, pilHGFA from tblPilot where pilLastName='$name'";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot query failed: ' . mysqli_connect_error());

    $member = 0;
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
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

#    $gmtimenow = time() - (int)substr(date('O'),0,3)*60*60;
#    if ($gmtimenow > ($until + 7*24*3600))
#    {
#        echo "<b>The submission period for tracks has closed ($until).</b><br>\n";
#        echo "Contact $contact if you're having an access problem.<br>\n";
#        echo "</div></body></html>\n";
#        exit(0);
#    }

    if ($member == 0)
    {
        echo "<b>Only registered pilots may submit tracks.</b><br>\n";
        echo "Contact $contact if you're having an access problem.<br>\n";
        echo "</div></body></html>\n";
        exit(0);
    }

    // add two point track (start+end).
    $task = reqival('task');
    $query = "select tasDate from tblTask where tasPk=$task";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task date failed: ' . mysqli_connect_error());
    if (mysqli_num_rows($result) == 0)
    {
        echo "Unable to submit pin to unknown task<br>\n";
        exit(0);
    }
    $tasDate = mysqli_result($result,0,0);
    $glider = reqsval('glider');
    $dhv = reqsval('dhv');

    $query = "insert into tblTrack (pilPk,traGlider,traDHV,traDate,traStart,traLength) values ($pilPk,'$glider','$dhv','$tasDate','$tasDate',0)";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Track Insert result failed: ' . mysqli_connect_error());
    $maxPk = mysqli_insert_id($link);

    $t1 = 43200;
    $t2 = 46800;
    $query = "insert into tblTrackLog (traPk, trlLatDecimal, trlLongDecimal, trlTime) VALUES ($maxPk,$xlat,$xlon,$t1),($maxPk,$lat,$lon,$t2)";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Tracklog insert failed: ' . mysqli_connect_error());

    $query = "insert into tblWaypoint (traPk, wptLatDecimal, wptLongDecimal, wptTime, wptPosition) VALUES ($maxPk,$xlat,$xlon,$t1,1),($maxPk,$lat,$lon,$t2,2)";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Waypoint insert failed: ' . mysqli_connect_error());


    $query = "insert into tblComTaskTrack (comPk,tasPk,traPk) values ($comPk,$task,$maxPk)";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' ComTaskTrack failed: ' . mysqli_connect_error());

    $out = '';
    $retv = 0;
    exec(BINDIR . "optimise_flight.pl $maxPk $comPk $task 0", $out, $retv);

    #$query = "select * from tblTrack where traPk=$maxPk";
    #$result = mysql_query($query) or die('Select length failed: ' . mysql_error());
    #$row=mysql_fetch_array($result);
    #$flown = $row['traLength'];
    #$query = "insert into tblTaskResult (tasPk,traPk,tarDistance,tarPenalty,tarResultType) values ($tasPk,$maxPk,$flown,0,'lo')";
    #$result = mysql_query($query) or die('Result insert failed: ' . mysql_error());

    redirect("tracklog_map.php?trackid=$maxPk&comPk=$comPk&ok=1");
}

hcheadbar("$regdesc Waypoints",3);
echo "<div id=\"content\">";
// Put the map on ..
echo "<div id=\"map\" style=\"width: 100%; height: 600px\"></div>";

echo "<div id='htmlControl'><form action=\"submit_pin.php?comPk=$comPk&regPk=$regPk\" name=\"wayptadmin\" method=\"post\">";
$igcarr[] = array('Task', fselect('task',$tasPk,$tasks), 'HGFA Number', "<input name=\"hgfanum\" type=\"text\">", 'Last Name', "<input name=\"lastname\" type=\"text\">");

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
$igcarr[] = array('Glider', '<input name="glider" type="text">', '', $classarr, '', fis("submitpin", "Submit PIN", 10));

$igcarr[] = array(fih('lat',0), fih('lon',0));

echo ftable($igcarr, '', '', '');
echo "</form></div>";
?>

</div>
</body>
</html>

