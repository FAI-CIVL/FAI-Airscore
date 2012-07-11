<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<?php
require 'authorisation.php';
$restrict='';
if (array_key_exists('comPk', $_REQUEST))
{
    $comPk = intval($_REQUEST['comPk']);
    $restrict = " and CTT.comPk=$comPk";
}
menubar($comPk);
?>
<p><h2>Recent Tracks</h2></p>
<?php

$link = db_connect();
echo "<ol>";
$count = 1;
$sql = "SELECT TR.*, T.*, P.*, C.* FROM tblComTaskTrack CTT, tblPilot P, tblCompetition C, tblTrack T left outer join tblTaskResult TR on TR.traPk=T.traPk where T.pilPk=P.pilPk and CTT.traPk=T.traPk and C.comPk=CTT.comPk $restrict order by T.traStart desc limit 40";
$result = mysql_query($sql,$link) or die('Recent query failed: ' . mysql_error());
while($row = mysql_fetch_array($result))
{
    $id = $row['traPk'];
    $tasPk = $row['tasPk'];
    if ($tasPk > 0)
    {
        $dist = round($row['tarDistance']/1000,2);
    }
    else
    {
        $dist = round($row['traLength']/1000,2);
    }
    $com = $row['comName'];
    $cpk = $row['comPk'];
    $name = $row['pilFirstName'] . " " . $row['pilLastName'];
    $date = $row['traStart'];
    echo "<a href=\"tracklog_map.php?trackid=$id&comPk=$cpk\"><li> $dist kms, $com, $name at $date.</a><br>\n";

    $count++;
}
echo "</ol>";
?>
</div>
</body>
</html>

