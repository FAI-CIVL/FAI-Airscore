<?php
require 'authorisation.php';
require 'format.php';
require 'hc2.php';
require 'plot_track.php';

hchead();
echo '<title>Waypoint Map</title>';
hccss();
hcmapjs();
hcscripts(array('json2,js', 'sprintf.js', 'plot_track.js'));
echo '<script type="text/javascript">';
sajax_show_javascript();
echo '</script>'
?>
<script type="text/javascript">

var map;

//<![CDATA[

function load() 
{
    if (GBrowserIsCompatible()) 
    {
<?php
echo "map = new GMap2(document.getElementById(\"map\"));\n";
echo "map.addMapType(G_PHYSICAL_MAP);\n";
echo "map.setMapType(G_PHYSICAL_MAP);\n";
echo "map.addControl(new GSmallMapControl());\n";
echo "map.addControl(new GMapTypeControl());\n";
echo "map.addControl(new GScaleControl());\n";

$usePk = check_auth('system');
$link = db_connect();
$trackid = intval($_REQUEST['trackid']);
$comPk = intval($_REQUEST['comPk']);
$tasPk = intval($_REQUEST['tasPk']);
$isadmin = is_admin('admin',$usePk,$comPk);
$interval = intval($_REQUEST['int']);
$action = addslashes($_REQUEST['action']);
$extra = 0;

$comName='Highcloud OLC';
$tasName='';
if ($tasPk > 0 || $trackid > 0)
{
    if ($tasPk > 0)
    {
        $sql = "SELECT C.*, T.* FROM tblCompetition C, tblTask T where T.tasPk=$tasPk and C.comPk=T.comPk";
    }
    else
    {
        $sql = "SELECT CTT.tasPk as ctask,C.*,CTT.*,T.* FROM tblCompetition C, tblComTaskTrack CTT left outer join tblTask T on T.tasPk=CTT.tasPk where C.comPk=CTT.comPk and CTT.traPk=$trackid";
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
        $tasType = $row['tasTaskType'];
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

if (($tasPk > 0) and ($tasType == 'race' || $tasType == 'speedrun' || $tasType == 'speedrun-interval' ))
{
    echo "do_add_task($tasPk);\n";
    if ($trackid > 0)
    {
        echo "do_add_track($trackid);\n";
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
}

    //]]>
</script>
</head>
<body onload="load()" onunload="GUnload()">
<div id="container">
<?php
hcheadbar($comName,2);
echo "<div id=\"content\">";

if ($trackid > 0)
{
    $sql = "SELECT T.*, P.*, TR.* FROM tblPilot P, tblTrack T left outer join tblTaskResult TR on TR.traPk=T.traPk where T.pilPk=P.pilPk and T.traPk=$trackid limit 1";
$result = mysql_query($sql,$link);
    if ($row = mysql_fetch_array($result))
    {
        $name = $row['pilFirstName'] . " " . $row['pilLastName'];
        if ($tasDate != '')
        {
            $date = $tasDate; 
        }
        else
        {
            $date = $row['traStart'];
        }
    
        $glider = htmlspecialchars($row['traGlider']);
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
            echo "<h3>$tasName: $name, $date (goal: $dist kms, ${ghour}h${gmin}m${gsec}s), $glider</h3>";
        }
        else
        {
            if ($gtime > 0)
            {
                echo "<h3>$name on $date ($dist kms, ${ghour}h${gmin}m, $glider)</h3>";
            }
            else
            {
             echo "<h3>$name on $date ($dist kms, $glider)</h3>";
            }
        }
    }
}

echo "<div id=\"map\" style=\"width: 800px; height: 600px\"></div>";
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
echo "<input type=\"button\" name=\"check\" value=\"Add Track\" onclick=\"do_add_track(0); return false;\">";
echo "&nbsp;<input type=\"button\" name=\"animate\" value=\"Animate\" onclick=\"animate(); return false;\">";
echo "<input type=\"button\" name=\"pause\" value=\"Pause\" onclick=\"pause_map(); return false;\">";
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

