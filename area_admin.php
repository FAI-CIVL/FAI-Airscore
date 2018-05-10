<?php
require 'authorisation.php';
require 'format.php';
require 'template.php';

auth('system');
$link = db_connect();
$usePk = auth('system');
$comPk = reqival('comPk');
$delreg= reqsval('del');
$file = __FILE__;
$message = '';

if (reqexists('create'))
{
    $region = reqsval('region');
    $query = "select * from tblRegion where regDescription='$region' limit 1";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Create region failed: ' . mysqli_connect_error());
    if (mysqli_num_rows($result) > 0)
    {
        $message .= "Unable to create region $region as it already exists.\n";
    }
    else
    {
		$query = "insert into tblRegion (regDescription) values ('$region')";
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Create region failed: ' . mysqli_connect_error());
		$regPk = mysqli_insert_id($link);

		redirect("region_admin.php?regPk=$regPk&created=1");
	}
}

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

// if (reqexists('delete'))
// {
//     // implement a nice 'confirm'
//     $regPk = reqival('delete');
//     $query = "select * from tblRegion where regPk=$regPk";
//     $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Region check failed: ' . mysqli_connect_error());
//     $row = mysqli_fetch_array($result, MYSQLI_BOTH);
//     $region = $row['regDescription'];
//     $query = "select * from tblTaskWaypoint T, tblRegionWaypoint W, tblRegion R where T.rwpPk=W.rwpPk and R.regPk=W.regPk and R.regPk=$regPk limit 1";
//     $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Delete check failed: ' . mysqli_connect_error());
//     if (mysqli_num_rows($result) > 0)
//     {
//         echo "Unable to delete $region ($regPk) as it is in use.\n";
//         return;
//     }
// 
//     $query = "delete from tblRegionWaypoint where regPk=$regPk";
//     $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Waipoint delete failed: ' . mysqli_connect_error());
//     $query = "delete from tblRegion where regPk=$regPk";
//     $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Centre update failed: ' . mysqli_connect_error());
//     echo "Region $region deleted\n";
// }

$rtable = [];

if ( $delreg !== '' )
{
	$message .= "Region $delreg deleted\n";
}

$hdr = array(fb('Area'), fb('Waypoints'), fb('WPT nr.'), fb('Open Air File'), '');
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
    $nxt[] = "<a href=\"region_admin.php?regPk=$id\">manage</a>";
	$rtable[] = $nxt;
}

//initializing template header
tpadmin($link,$file);

echo "<h3>Flying Areas Administration</h3>\n";
if ( $message !== '')
{
	echo "<h4> <span style='color:red'>$message</span> </h4>";
}
echo "<hr />";
echo "<i> We have " . $count . " defined flying areas</i>";
echo "<hr />";
echo "<form enctype=\"multipart/form-data\" action=\"area_admin.php\" name=\"area\" method=\"post\">";
echo ftable($rtable,'class=areatable', '', '');
echo "</form>";
echo "<br />";
echo "<hr />";

echo "<form enctype=\"multipart/form-data\" action=\"area_admin.php\" name=\"area\" method=\"post\">";
echo "New Region: " . fin('region', '', 10);
echo fis('create', 'Create', 10);
echo "</form>";

tpfooter($file);

?>


