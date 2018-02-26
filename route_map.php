<?php
require_once 'Sajax.php';
require 'authorisation.php';
require 'format.php';
require 'hc2v3.php';
require 'plot_track.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

hchead();
echo "<title>Task Map</title>\n";
hccss();
hcmapjs();
hcscripts([ 'rjson.js', 'json2.js', 'sprintf.js', 'plot_trackv4.js', 'microajax.minified.js', 'uair.js', 'plot_task.js' ]);
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

//    $result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
//    if ($row = mysql_fetch_array($result))
    if ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
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

if ($tasPk > 0)
{
    if ($tasType == 'free-pin' || $tasType == 'free' || $tasType == 'olc')
    {
        echo "plot_task($tasPk,1,0);\n";
    }
    else
    {
        echo "plot_task($tasPk,1,0);\n";
    }
    // task header ..
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
echo "<div id=\"map\" style=\"width: 100%; height: 600px\"></div>";
echo "</div>\n";
// mysql_close($link);
mysqli_close($link);
?>
</body>
</html>

