<?php
require_once 'Sajax.php';
require 'authorisation.php';
require 'format.php';
require 'template.php';
require 'plot_track.php';
require 'xcdb.php';

$comPk = intval($_REQUEST['comPk']);
$tasPk = intval($_REQUEST['tasPk']);
$usePk = check_auth('system');

$link = db_connect();
$cval = null;
$tarPk = null;

$file = __FILE__;
$row = get_comtask($link,$tasPk);

//initializing template header
tpinit($link,$file,$row);

?>

<script>
var map;
//<![CDATA[
function initialize() 
{
    var moptions =
        {
            zoom: 12,
            center: new google.maps.LatLng(42, 12.644),
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

<?php

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

    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
    if ($row = mysqli_fetch_assoc($result))
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
        $comClass = $row['comClass'];
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
        if ($comClass == 'sail')
        {
            echo "do_track_speed($trackid,5);\n";
        }
        else
        {
            echo "do_add_track($trackid);\n";
        }
    }

    if ($tasType == 'airgain')
    {
            echo "do_add_region($regPk,$trackid);\n";
    }
    else
    {
        if ($isadmin)
        {
            echo "plot_task($tasPk, 0, $trackid);\n";
        }
        else
        {
            echo "plot_task($tasPk, 0, 0);\n";
        }
    }
}
else if ($trackid > 0)
{
    echo "do_add_track_wp($trackid);\n";
    echo "do_add_track($trackid);\n";
    $sql = "SELECT max(trlTime) - min(trlTime) FROM tblTrackLog where traPk=$trackid";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Time query failed: ' . mysqli_connect_error());
    $gtime = mysqli_result($result, 0, 0);
}


?>
}
google.maps.event.addDomListener(window, 'load', initialize);

    //]]>
</script>

<?php

if ($trackid > 0)
{
    $okay = '';
    if ($trackok == 1)
    {
        $okay = "<i>Track Accepted</i>";
    }
}

echo "<div id=\"map\" style=\"width: 100%; height: 600px\"></div>";
echo "<input type=\"text\" name=\"foo\" id=\"foo\" size=\"8\">";
if ($tasPk > 0)
{
    $sql = "select TR.*, T.*, P.* from tblTaskResult TR, tblTrack T, tblPilot P where TR.tasPk=$tasPk and T.traPk=TR.traPk and P.pilPk=T.pilPk order by TR.tarScore desc limit 20";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task result selection failed: ' . mysqli_connect_error());
    $addable = [];
    while ($row = mysqli_fetch_assoc($result))
    {
        $addable[$row['pilHGFA'].' : '.$row['pilFirstName'].' '.$row['pilLastName']] = $row['traPk'];
    }
    echo fselect('trackid', '', $addable);
}
else if ($trackid > 0)
{
    $sql = "select T2.*, P.* from tblTrack T, tblTrack T2, tblPilot P where T2.traStart>date_sub(T.traStart, interval 6 hour) and T2.traStart<date_add(T.traStart, interval 6 hour) and T.traPk=$trackid and P.pilPk=T2.pilPk order by T2.traLength desc limit 10";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task result selection failed: ' . mysqli_connect_error());
    $addable = [];
    while ($row = mysqli_fetch_assoc($result))
    {
        $addable[$row['pilHGFA'].' : '.$row['pilFirstName'].' '.$row['pilLastName']] = $row['traPk'];
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
echo "<br>";

$airspaces = array();
if ($tasPk > 0)
{
    $sql = "select * from tblTaskAirspace TA, tblAirspace A, tblAirspaceWaypoint AW where TA.tasPk=$tasPk and A.airPk=TA.airPk and A.airPk=AW.airPk order by A.airPk,AW.airOrder";
}
else
{
    $sql = "SELECT *, trlTime as bucTime FROM tblTrackLog where traPk=$trackid order by trlTime limit 1";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Tracklog location failed: ' . mysqli_connect_error());
    $row = mysqli_fetch_assoc($result);
    $tracklat = $row['trlLatDecimal'];
    $tracklon = $row['trlLongDecimal'];

    $sql = "select * from tblAirspace R 
                where R.airPk in (             
                    select airPk from tblAirspaceWaypoint W, tblAirspaceRegion R where
                    $tracklat between (R.argLatDecimal-R.argSize) and (R.argLatDecimal+R.argSize) and
                    $tracklon between (R.argLongDecimal-R.argSize) and (R.argLongDecimal+R.argSize) and
                    W.awpLatDecimal between (R.argLatDecimal-R.argSize) and (R.argLatDecimal+R.argSize) and
                    W.awpLongDecimal between (R.argLongDecimal-R.argSize) and (R.argLongDecimal+R.argSize)
                    group by (airPk))
                order by R.airName";
}

$result = mysqli_query($link, $sql);
if ($result)
{
    $addable = [];
    while ($row = mysqli_fetch_assoc($result))
    {   
        $airspaces[$row['airName']] = $row['airPk'];
    }
}
if (sizeof($airspaces) > 0)
{
    echo fselect('airspaceid', '', $airspaces);
    //echo "<input type=\"text\" name=\"airspaceid\" id=\"airspaceid\" size=\"8\"\">";
    echo "<input type=\"button\" name=\"check\" value=\"Add Airspace\" onclick=\"do_add_air(0); return false;\">";
}
    
if ($trackid > 0)
{
    echo "<form action=\"download_tracks.php?traPk=$trackid\" name=\"trackdown\" method=\"post\">";
    echo "<input type=\"submit\" value=\"Download Track\">";
    echo "</form>";
}

mysqli_close($link);

tpfooter($file);

?>
