<?php
require 'authorisation.php';
require 'format.php';
require 'hc2v3.php';
require 'plot_track.php';
hchead();
echo "<title>Tracklog Map</title>\n";
hccss();
hcmapjs();
hcscripts(array('json2.js', 'sprintf.js', 'plot_trackv3.js'));
echo '<script type="text/javascript">';
sajax_show_javascript();
echo "</script>\n";
?>
<script type="text/javascript">
var map;
//<![CDATA[
function initialize() 
{
    var moptions =
        {
            zoom: 12,
            center: new google.maps.LatLng(-37, 143.644),
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
    map = new google.maps.Map(document.getElementById("map"), moptions);
    //map.setMapTypeId(google.maps.MapTypeId.TERRAIN);

<?php
//echo "map.addControl(new GSmallMapControl());\n";
//echo "map.addControl(new GMapTypeControl());\n";
//echo "map.addControl(new GScaleControl());\n";

$usePk = check_auth('system');
$link = db_connect();
$trackid = reqival('trackid');
$comPk = reqival('comPk');
$tasPk = reqival('tasPk');
$trackok = reqsval('ok');
$isadmin = is_admin('admin',$usePk,$comPk);
$interval = reqival('int');
$action = reqsval('action');
$extra = 0;

$comName='Highcloud OLC';
$tasName='';
$offset = 0;
if ($tasPk > 0 || $trackid > 0)
{
    if ($tasPk > 0)
    {
        $sql = "SELECT C.*, T.*,T.regPk as tregPk FROM tblCompetition C, tblTask T where T.tasPk=$tasPk and C.comPk=T.comPk";
    }
    else
    {
        $sql = "SELECT CTT.tasPk as ctask,C.*,CTT.*,T.*,T.regPk as tregPk FROM tblCompetition C, tblComTaskTrack CTT left outer join tblTask T on T.tasPk=CTT.tasPk where C.comPk=CTT.comPk and CTT.traPk=$trackid";
    }

    $result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
    if ($row = mysql_fetch_array($result))
    {
        if ($tasPk == 0)
        {
            $tasPk = $row['ctask'];
        }
        if ($comPk == 0)
        {
            $comPk = $row['comPk'];
        }
        $comName = $row['comName'];
        $tasName = $row['tasName'];
        $tasDate = $row['tasDate'];
        $tasType = $row['tasTaskType'];
        $regPk = $row['tregPk'];
        $offset = $row['comTimeOffset'];
        if ($tasName)
        {
            $comName = $comName . ' - ' . $tasName;
        }
        else
        {
            $tasName = '';
        }
    }
}

if (($tasPk > 0) and ($tasType == 'race' || $tasType == 'speedrun' || $tasType == 'speedrun-interval' || $tasType == 'airgain' ))
{
    if ($trackid > 0)
    {
        echo "do_add_track($trackid);\n";
    }

    if ($tasType == 'airgain')
    {
            echo "do_add_region($regPk,$trackid);\n";
    }
    else
    {
        if ($isadmin)
        {
            echo "do_award_task($tasPk,$trackid);\n";
        }
        else
        {
            echo "do_add_task($tasPk);\n";
        }
    }
}
else if ($trackid > 0)
{
    echo "do_add_track_wp($trackid);\n";
    echo "do_add_track($trackid);\n";
    $sql = "SELECT max(trlTime) - min(trlTime) FROM tblTrackLog where traPk=$trackid";
    $result = mysql_query($sql,$link) or die('Time query failed: ' . mysql_error());
    $gtime = mysql_result($result, 0, 0);
}


?>
}
google.maps.event.addDomListener(window, 'load', initialize);

    //]]>
</script>
</head>
<body>
<div id="container">
<?php
hcheadbar($comName,2);
echo "<div id=\"content\">";

if ($trackid > 0)
{
    $okay = '';
    if ($trackok == 1)
    {
        $okay = "<i>Track Accepted</i>";
    }
}

echo "<div id=\"map\" style=\"width: 100%; height: 600px\"></div>";
echo "<input type=\"text\" name=\"foo\" id=\"foo\" size=\"8\"\">";
if ($tasPk > 0)
{
    $sql = "select TR.*, T.*, P.* from tblTaskResult TR, tblTrack T, tblPilot P where TR.tasPk=$tasPk and T.traPk=TR.traPk and P.pilPk=T.pilPk order by TR.tarScore desc limit 10";
    $result = mysql_query($sql,$link) or die('Task Result selection failed: ' . mysql_error());
    $addable = Array();
    while ($row = mysql_fetch_array($result))
    {
        $addable[$row['pilLastName']] = $row['traPk'];
    }
    echo fselect('trackid', '', $addable);
}
else if ($trackid > 0)
{
    $sql = "select T2.*, P.* from tblTrack T, tblTrack T2, tblPilot P where T2.traStart>date_sub(T.traStart, interval 6 hour) and T2.traStart<date_add(T.traStart, interval 6 hour) and T.traPk=$trackid and P.pilPk=T2.pilPk order by T2.traLength desc limit 10";
    $result = mysql_query($sql,$link) or die('Task Result selection failed: ' . mysql_error());
    $addable = Array();
    while ($row = mysql_fetch_array($result))
    {
        $addable[$row['pilLastName']] = $row['traPk'];
    }

    # Add others in region ..
    #if (sizeof($row) < 10)
    #{
    #}
    echo fselect('trackid', '', $addable);
}
else
{
    echo "<input type=\"text\" name=\"trackid\" id=\"trackid\" size=\"8\"\">";
}
echo "<input type=\"button\" name=\"check\" value=\"Add Track\" onclick=\"do_add_track(0); return false;\">&nbsp;";
echo "<input type=\"button\" name=\"reset\" value=\"<<\" onclick=\"reset_map(); return false;\">";
echo "<input type=\"button\" name=\"pause\" id=\"pause\" value=\">>\" onclick=\"pause_map(); return false;\">";
//echo "<input type=\"button\" name=\"pause\" id=\"pause\" value=\"=\" onclick=\"pause_map(); return false;\">";
echo "<input type=\"button\" name=\"back\" id=\"back\" value=\"<\" onclick=\"back(); return false;\">";
echo "<input type=\"button\" name=\"forward\" id=\"forward\" value=\">\" onclick=\"forward(); return false;\">";
echo "&nbsp;&nbsp;";
echo "<input type=\"button\" name=\"clear\" value=\"Clear\" onclick=\"clear_map(); return false;\">";
if ($trackid > 0)
{
    echo "<form action=\"download_tracks.php?traPk=$trackid\" name=\"trackdown\" method=\"post\">";
    echo "<input type=\"submit\" value=\"Download Track\">";
    echo "</form>";
}
echo "</div>\n";
mysql_close($link);
?>
</body>
</html>

