<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<?php
require 'authorisation.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

$restrict='';
$comPk = 0;
if (array_key_exists('comPk', $_REQUEST))
{
    $comPk = intval($_REQUEST['comPk']);
    $restrict = " and CTT.comPk=$comPk";
}
menubar($comPk);

$link = db_connect();
if ($comPk != 0)
{
    $sql = "select C.comName from tblCompetition C where C.comPk=$comPk";
//    $result = mysql_query($sql,$link) or die('Top tracks: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Top tracks failed: ' . mysqli_connect_error());
//    $comName = mysql_result($result,0);
    $comName = mysqli_result($result,0);
    $title = " - $comName";
}

echo "<p><h2>Top Tracks$title</h2></p>";

echo "<ol>";
$count = 1;
$sql = "SELECT T.*, P.* FROM tblTrack T, tblPilot P, tblComTaskTrack CTT where T.pilPk=P.pilPk and CTT.traPk=T.traPk $restrict order by T.traScore desc limit 10";
// $result = mysql_query($sql,$link) or die('Top tracks: ' . mysql_error());
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Top tracks failed: ' . mysqli_connect_error());
;
// while($row = mysql_fetch_array($result))
while($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $id = $row['traPk'];
    $dist = round($row['traLength']/1000,2);
    $name = $row['pilFirstName'] . " " . $row['pilLastName'];
    $date = $row['traDate'];
    $score = round($row['traScore']/1000,1);
    echo "<a href=\"tracklog_map.php?trackid=$id&comPk=$comPk\"><li> $score Pts ($dist kms): $name on $date.</a><br>\n";

    $count++;
}
echo "</ol>";
if ($count == 1)
{
    echo "<b>No tracks submitted for $comName yet.</b>\n";
}

?>
</div>
</body>
</html>

