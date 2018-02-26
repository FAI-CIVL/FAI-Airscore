<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<div id="vhead"><h1>Skyhigh Cup</h1></div>
<div id="menu">
<ul>
<li><a href="index.php">Information</a></li>
<li><a href="recent.php">Recent Tracks</a></li>
<li><a href="submit_track.php">Submit Track</a></li>
</ul>
</div>
<p><h2>Top Tracks</h2></p>
<?php
require 'authorisation.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

$link = db_connect();
echo "<ol>";
$count = 1;
$sql = "SELECT T.*, P.* FROM tblTrack T, tblPilot P where T.pilPk=P.pilPk order by T.traScore desc limit 10";
// $result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql);
// while($row = mysql_fetch_array($result))
while($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $id = $row['traPk'];
    $dist = round($row['traLength']/1000,2);
    $name = $row['pilFirstName'] . " " . $row['pilLastName'];
    $date = $row['traDate'];
    $score = round($row['traScore']/1000,1);
    echo "<a href=\"tracklog_map.php?trackid=$id\"><li> $score Pts ($dist kms): $name on $date.</a><br>\n";

    $count++;
}
echo "</ol>";
?>
</div>
</body>
</html>

