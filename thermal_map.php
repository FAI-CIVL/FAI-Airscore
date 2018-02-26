<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml">
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<title>Skyhigh Cup Tracklog</title>
<script src="http://maps.google.com/maps?file=api&amp;v=2&amp;key=ABQIAAAAPyz1XxP2rM79ZhAH2EmgwxQ1ylNcivz9k-2ubmbv1YwdT5nh3RQJsyJo_kuVL1UAWoydxDkwo_zsKw" type="text/javascript"></script>
<script src="elabel.js" type="text/javascript"></script>
<script src="einsert.js" type="text/javascript"></script>
<script type="text/javascript">
    //<![CDATA[

function load() 
{
    if (GBrowserIsCompatible()) 
    {
<?php
require 'authorisation.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

echo "var map = new GMap2(document.getElementById(\"map\"));\n";
echo "map.addMapType(G_PHYSICAL_MAP);\n";
echo "map.setMapType(G_PHYSICAL_MAP);\n";
echo "map.addControl(new GSmallMapControl());\n";
echo "map.addControl(new GMapTypeControl());\n";
echo "map.addControl(new GScaleControl());\n";

$usePk = check_auth('system');
$link = db_connect();
$trackid = intval($_REQUEST['trackid']);
$comPk = intval($_REQUEST['comPk']);
$isadmin = is_admin('admin',$usePk,$comPk);
$interval = intval($_REQUEST['int']);
$action = $_REQUEST['action'];
$extra = 0;

$tasPk=0;
$comName='Highcloud OLC';
$tasName='';
$sql = "SELECT CTT.tasPk,C.comName,T.tasName,C.comPk,T.tasTaskType FROM tblCompetition C, tblComTaskTrack CTT left outer join tblTask T on T.tasPk=CTT.tasPk where C.comPk=CTT.comPk and CTT.traPk=$trackid";
// $result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task add failed: ' . mysqli_connect_error());
// if (mysql_num_rows($result) > 0)
if (mysqli_num_rows($result) > 0)
{
//    $tasPk = mysql_result($result,0,0);
//    $comName = mysql_result($result,0,1);
//    $tasName = mysql_result($result,0,2);
//    //$comPk = mysql_result($result,0,3);
//    $tasType = mysql_result($result,0,4);
    $tasPk = mysqli_result($result,0,0);
    $comName = mysqli_result($result,0,1);
    $tasName = mysqli_result($result,0,2);
    $tasType = mysqli_result($result,0,4);
    if ($tasName)
    {
        $comName = $comName . ' - ' . $tasName;
    }
    else
    {
        $tasName = '';
    }
}
if (($tasPk > 0) and ($tasType == 'race' || $tasType == 'speedrun' || $tasType == 'speedrun-interval' ))
{
    $sql = "SELECT T.*,W.* FROM tblTaskWaypoint T, tblRegionWaypoint W where T.tasPk=$tasPk and W.rwpPk=T.rwpPk order by T.tawNumber";
    // $result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
    $prefix='rwp';
    $first = 1;
    $extra = 1;
}
else
{
    $sql = "SELECT max(trlTime) - min(trlTime) FROM tblTrackLog where traPk=$trackid";
    // $result = mysql_query($sql,$link) or die('Time query failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Time query failed: ' . mysqli_connect_error());
//    $gtime = mysql_result($result, 0, 0);
    $gtime = mysqli_result($result, 0, 0);

    $sql = "SELECT * FROM tblWaypoint where traPk=$trackid order by wptTime";
    // $result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
    $prefix='wpt';
    $first = 1;
}


echo "var polyline = new GPolyline(["; 
$count = 0;
$wayptarr = [];
// while($row = mysql_fetch_array($result))
while($row = mysqli_fetch_array($result, MYSQLI_BOTH))
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
    $wayptarr[$count++] = $row;
}
echo "],\"#0000ff\", 2, 1);\n";

// Did we award from turnpoints?
if ($action == 'award')
{
    $sql = "select tarTurnpoints from tblTaskResult where traPk=$trackid";
    // $result = mysql_query($sql,$link) or die('Task turnpoints failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task turnpoints failed: ' . mysqli_connect_error());
//    $turnpoints = mysql_result($result, 0, 0);
    $turnpoints = mysqli_result($result, 0, 0);

    $upto = intval($_REQUEST['turnpoint']);
    $gt = addslashes($_REQUEST['goaltime']);
    # now convert to seconds ...
    $timarr = split(':', $gt);
    $goaltime = $timarr[0] * 3600 + $timarr[1] * 60 + $timarr[2];

    $tadTime = 0;
    for ($cnt = $turnpoints; $cnt < $upto+1; $cnt++)
    {
        $row = $wayptarr[$cnt];

        $tawPk = $row['tawPk'];
        if ($cnt == $upto)
        {
            $tadTime = $goaltime;
        }
        $sql = "insert into tblTaskAward (tawPk, traPk, tadTime) values ($tawPk, $trackid, $tadTime)";
        // $result = mysql_query($sql,$link) or die('Award waypoint failed: ' . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Award waypoint failed: ' . mysqli_connect_error());
    }
    $sql = "update tblTaskResult set tarTurnpoints=($upto+1) where traPk=$trackid";
    // $result = mysql_query($sql,$link) or die('Task turnpoint award failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task turnpoint award failed: ' . mysqli_connect_error());

    # Re-verify with new awarded waypoint(s)
    $out = '';
    $retv = 0; 
    exec(BINDIR . "track_verify_sr.pl $trackid", $out, $retv);

    # rescore task ..
}

//
if (!$clat)
{
    // FIX THIS HACK
    $clat = -36.75;
    $clong= 146.9;
}
echo "map.setCenter(new GLatLng($clat, $clong), 13);\n";
echo "map.addOverlay(polyline);\n\n";

if ($interval < 1)
{
    $interval = 20;
    $segment = 25;
}
if ($interval == 1)
{
    $sql = "SELECT *, trlTime as bucTime FROM tblTrackLog where traPk=$trackid order by trlTime";
    $segment = 10;
}
else
{
    $sql = "SELECT *, trlTime div $interval as bucTime FROM tblTrackLog where traPk=$trackid group by trlTime div $interval order by trlTime";
}
// $result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql);
$first = 1;
$clat=0;
$clong=0;

$count = 0;
$lasLat = 0;
$lasLon = 0;
$lasAlt = "00";
echo "var polyline;\n";
// while($row = mysql_fetch_array($result))
while($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{

    if ($count % $segment == 0)
    {
        if ($first == 0)
        {
            echo "],\"#ff${lasAlt}00\", 3, 1);\n";
            echo "map.addOverlay(polyline);\n\n";
        }
        echo "var polyline = new GPolyline(["; 
        if ($first == 0)
        {
            echo "new GLatLng(" . $lasLat . "," . $lasLon . "),\n";
        }
    }
    else
    {
        echo ",\n";
    }

    if ($first == 1)
    {
        $first = 0;
    }

    $count++;
    $lasLat = $row['trlLatDecimal'];
    $lasLon = $row['trlLongDecimal'];
    $lasAlt = dechex(($row['trlAltitude']/10)%256);
    while (strlen($lasAlt) < 2)
    {
        $lasAlt = "0" . $lasAlt;
    }
    echo "new GLatLng(" . $lasLat . "," . $lasLon . ")";
}
echo "],\"#ff0000\", 3, 1);\n";
echo "map.addOverlay(polyline);\n\n";

if ($extra) 
{
    foreach ($wayptarr as $cnt => $row)
    {
        $clat = $row["rwpLatDecimal"];
        $clong = $row["rwpLongDecimal"];
        $cname = $row["rwpName"];
        $crad = $row["tawRadius"];
        $tawPk = $row["tawPk"];
        $tawType = $row["tawType"];

        // tlabel.js stuff
        //echo "var tlabel = new TLabel();";
        //echo "tlabel.id = '$cname';";
        //echo "tlabel.anchorLatLng = new GLatLng ($clat, $clong);";
        //echo "tlabel.anchorPoint = 'bottomLeft';";
        //echo "tlabel.percentOpacity = 70;";
        //echo "tlabel.content = '<div style=\"padding: 0px 0px 8px 8px; background: url(images/point_bottom_left.png) no-repeat bottom left;\"><div style=\"background-color: #6666ff; padding: 2px; font-size: 0.7em;\"><nobr><a href=\"blackbirds.html?bird=924\">$cname</a></nobr></div></div>';";
        //echo "map.addTLabel(tlabel);";

        // An ELabel with all optional parameters in use 
        echo "var pos = new GLatLng($clat,$clong);\n";
        echo "var label = new ELabel(pos, \"$cname\", \"waypoint\", new GSize(-40,0), 60);\n";
        echo "map.addOverlay(label);\n";

        // add a radius circle
        echo "var sz = GSizeFromMeters(map, pos, $crad*2,$crad*2);\n";
        echo "map.addOverlay(new EInsert(pos, \"circle.png\", sz, 13));\n";
    }
}

?>
    }
}

    //]]>
</script>
</head>
<body onload="load()" onunload="GUnload()">
<div id="container">

<?php
menubar($comPk);

$link = db_connect();
$trackid = $_REQUEST['trackid'];

$sql = "SELECT T.*, P.*, TR.* FROM tblPilot P, tblTrack T left outer join tblTaskResult TR on TR.traPk=T.traPk where T.pilPk=P.pilPk and T.traPk=$trackid limit 1";
// $result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql);
// if ($row = mysql_fetch_array($result))
if ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $name = $row['pilFirstName'] . " " . $row['pilLastName'];
    $date = $row['traDate'];
    $glider = $row['traGlider'];
    $turnpoints = $row['tarTurnpoints'];
    if ($glider == '')
    {
        $glider = 'unknown glider';
    }
    if ($tasPk > 0)
    {
        $ggoal = $row['tarES'] - $row['tarSS'];
        $gtime = $ggoal;
    }
    $ghour = floor($gtime / 3600);
    $gmin = floor($gtime / 60) - $ghour*60;
    $gsec = $gtime % 60;
    if ($tasPk == 0)
    {
        $dist = round($row['traLength'] / 1000, 2);
    }
    else
    {
        $dist = round($row['tarDistance'] / 1000, 2);
    }
    if ($ggoal > 0)
    {
        echo "<p><h3>$tasName: $name, $date (goal: $dist kms, ${ghour}h${gmin}m${gsec}s), $glider</h3></p>";
    }
    else
    {
        if ($gtime > 0)
        {
            echo "<p><h3>$name on $date ($dist kms, ${ghour}h${gmin}m, $glider)</h3></p>";
        }
        else
        {
            echo "<p><h3>$name on $date ($dist kms, $glider)</h3></p>";
        }
    }
}
echo "<div id=\"map\" style=\"width: 800px; height: 600px\"></div>";

echo "<form action=\"tracklog_map.php?trackid=$trackid&comPk=$comPk&int=1\" name=\"trackdown\" method=\"post\">";
echo "<input type=\"submit\" value=\"See Exact Track\">";
echo "</form>";
echo "<form action=\"download_tracks.php?traPk=$trackid\" name=\"trackdown\" method=\"post\">";
echo "<input type=\"submit\" value=\"Download Track\">";
echo "</form>";

if ($isadmin && $extra && $turnpoints < count($wayptarr))
{
    echo "<h3>Extra Waypoints - select furthest on task:</h3><p>";
    echo "<form action=\"tracklog_map.php?trackid=$trackid&comPk=$comPk&action=award\" name=\"trackdown\" method=\"post\">\n";
    foreach ($wayptarr as $cnt => $arr)
    {
        $key = $arr['tawPk'];
        $name = $arr['rwpName'];
        if ($cnt >= $turnpoints)
        {
            echo "$cnt. <input type=\"checkbox\" name=\"turnpoint\" value=\"$cnt\"> $name ";
            if ($arr['tawType'] == 'endspeed' ||
                $arr['tawType'] == 'goal')
            {
                echo "<input type=\"text\" name=\"goaltime\" size=6>";
            }
            echo "<br>\n";
        }
    }
    echo "<input type=\"submit\" value=\"Add Extra\"><br>";
    echo "</form>";
    echo "</p>";
}

echo "</div>\n";
// mysql_close($link);
mysqli_close($link);
?>
</body>
</html>

