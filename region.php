<?php
require 'authorisation.php';
require 'format.php';
require 'template.php';

$link = db_connect();
$file = __FILE__;
$message = '';

if (reqexists('downloadwpt'))
{
    // implement a nice 'confirm'
    $id=reqival('downloadwpt');
    redirect("download_waypoints.php?download=$id");
}

if (reqexists('downloadopenair'))
{
    // implement a nice 'confirm'
    $id=reqival('downloadopenair');
    redirect("download_openair.php?download=$id");
}

$rtable = [];

$hdr = array(fb('Area'), fb('Waypoints'), fb('WPT nr.'), fb('Open Air File'));
$rtable[] = $hdr;

$sql = "SELECT R.*, COUNT(RW.rwpPk) AS regWptNum FROM tblRegion R LEFT JOIN tblRegionWaypoint RW on RW.regPk = R.regPk GROUP BY R.regPk ORDER BY R.regDescription";
$result = mysqli_query($link, $sql);
$count = mysqli_num_rows($result);
while ( $row = mysqli_fetch_array($result, MYSQLI_BOTH) )
{
    $nxt = [];
    $id = $row['regPk'];
    $nxt[] = $row['regWptFileName'] !== '' ? "<a href=\"waypoint_map.php?regPk=$id\">" . str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['regDescription'])))) . "</a>" : str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['regDescription']))));
    $nxt[] = $row['regWptFileName'] !== '' ? fbut('submit', 'downloadwpt', $id, $row['regWptFileName']) : '';
    $nxt[] = $row['regWptFileName'] !== '' ? $row['regWptNum'] : '';
    $nxt[] = $row['regOpenAirFile'] !== '' ? fbut('submit', 'downloadopenair', $id, $row['regOpenAirFile']) : '';
	$rtable[] = $nxt;
}

//initializing template header
tpadmin($link,$file);

echo "<h3>Flying Areas</h3>\n";
if ( $message !== '')
{
	echo "<h4> <span style='color:red'>$message</span> </h4>";
}
echo "<hr />";
echo "<i> We have " . $count . " defined flying areas</i>";
echo "<hr />";
echo "<form enctype=\"multipart/form-data\" action=\"area_admin.php\" name=\"area\" method=\"post\">";
echo ftable($rtable,"class=format areatable", '', '');
echo "</form>";

tpfooter($file);

?>