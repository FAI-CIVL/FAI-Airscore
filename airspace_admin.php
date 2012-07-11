<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<div id="vhead"><h1>airScore admin</h1></div>
<?php
require 'authorisation.php';
require 'format.php';

adminbar(0);
?>
<p><h2>Airspace Administration</h2></p>
<?php

auth('system');
$link = db_connect();

if (array_key_exists('add', $_REQUEST))
{
    $region = $_FILES['waypoints']['tmp_name'];
    $out = '';
    $retv = 0;
    exec(BINDIR . "airspace_openair.pl $region", $out, $retv);

    if ($retv)
    {
        echo "<b>Failed to upload your airspace properly.</b><br>\n";
        foreach ($out as $txt)
        {
            echo "$txt<br>\n";
        }
        echo "</div></body></html>\n";
        exit(0);
    }

    foreach ($out as $row)
    {
        echo $row ."<br>";
    }
}

if (array_key_exists('delete', $_REQUEST))
{
    // implement a nice 'confirm'
    $regPk = intval($_REQUEST['delete']);
    $query = "select * from tblAirspace where airPk=$regPk";
    $result = mysql_query($query) or die('Airspace check failed: ' . mysql_error());
    $row = mysql_fetch_array($result);
    $region = $row['airName'];
    #$query = "select * from tblTaskWaypoint T, tblRegionWaypoint W, tblRegion R where R.regPk=W.regPk and R.regPk=$regPk limit 1";
    #$result = mysql_query($query) or die('Delete check failed: ' . mysql_error());
    #if (mysql_num_rows($result) > 0)
    #{
    #    echo "Unable to delete $region ($regPk) as it is in use.\n";
    #    return;
    #}

    $query = "delete from tblAirspaceWaypoint where airPk=$regPk";
    $result = mysql_query($query) or die('AirspaceWaypoint delete failed: ' . mysql_error());
    $query = "delete from tblAirspace where airPk=$regPk";
    $result = mysql_query($query) or die('Airspace delete failed: ' . mysql_error());
    echo "Airspace $region deleted\n";
}

if (array_key_exists('download', $_REQUEST))
{
    // implement a nice 'confirm'
    $id=intval($_REQUEST['download']);
    // airspace_openair.pl      
}

echo "<form enctype=\"multipart/form-data\" action=\"airspace_admin.php\" name=\"waypoint\" method=\"post\">";
echo "<input type=\"hidden\" name=\"MAX_FILE_SIZE\" value=\"1000000000\">";
$count = 1;

$airtab = array();

$airtab[] =  array(fb('Id'), '', '', '', fb('Name'), fb('Class'), fb('Shape'), fb('Base(m)'), fb('Top(m)'));
$sql = "SELECT * from tblAirspace R order by R.airName";
$result = mysql_query($sql,$link);
while($row = mysql_fetch_array($result))
{
    $id = $row['airPk'];
    $name = $row['airName'];
    $airtab[] = array($id,
        fbut('submit', 'update', $id, 'up'),
        fbut('submit', 'delete', $id, 'del'),
        fbut('submit', 'download', $id, 'download'),
        "<a href=\"airspace_map.php?airPk=$id\">$name</a>",
        fb($row['airClass']),
        fb($row['airShape']),
        fb($row['airBase']),
        fb($row['airTops'])
        );

    //waypoint_select($link, $tasPk, "waypoint$tawPk", $waypt);
    //echo " centre: $centname</a>";
    $count++;
}
echo ftable($airtab, '', '', '');
echo "<hr>";

echo "Load Airspace: " . fin('region', '', 10);
echo "OpenAir File: <input type=\"file\" name=\"waypoints\">";
echo fis('add', 'Add Airspace', 10);
echo "<br>";
echo "</form>";
?>
</div>
</body>
</html>

