<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<div id="vhead"><h1>airScore admin</h1></div>
<?php
require 'authorisation.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

$comPk = reqival('comPk');
adminbar($comPk);

if ($comPk > 0)
{
    echo "<p><h2>Track Administration ($comPk)</h2></p>";
}
else
{
    echo "<p><h2>Track Administration (global)</h2></p>";
}

$usePk=auth('system');
$link = db_connect();

if (array_key_exists('delete', $_REQUEST))
{
    $id = intval($_REQUEST['delete']);
    echo "Delete track: $id<br>";

    $lco = -1;
    $comcl = '';
    if ($comPk > 0)
    {
        $comcl = " and comPk=$comPk";
    }
    $query = "SELECT TK.comPk FROM tblTask TK, tblTaskResult TR where TR.tasPk=TK.tasPk and TR.traPk=$id$comcl";
//    $result = mysql_query($query) or die('Cant get track info: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Track Info failed: ' . mysqli_connect_error());
//    if (mysql_num_rows($result) == 0)
    if (mysqli_num_rows($result) == 0)
    {
        $query = "SELECT comPk FROM tblComTaskTrack where traPk=$id$comcl";
//        $result = mysql_query($query) or die('Cant get track info: ' . mysql_error());
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Track info failed: ' . mysqli_connect_error());
    }
//    if (mysql_num_rows($result) > 0)
    if (mysqli_num_rows($result) > 0)
    {
//        $lco = mysql_result($result,0,0);
        $lco = mysqli_result($result,0,0);
    }

    if (!check_admin('admin',$usePk, $lco))
    {
        die("You cannot delete tracks for that competition($lco)<br>");
        return;
    }

    $query = "delete from tblTaskResult where traPk=$id";
    // $result = mysql_query($query) or die('TaskResult delete failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' TaskResult delete failed: ' . mysqli_connect_error());

    $query = "delete from tblTrack where traPk=$id";
    // $result = mysql_query($query) or die('Track delete failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Track delete failed: ' . mysqli_connect_error());

    $query = "delete from tblTrackLog where traPk=$id";
    // $result = mysql_query($query) or die('Tracklog delete failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Tracklog delete failed: ' . mysqli_connect_error());

    $query = "delete from tblWaypoint where traPk=$id";
    // $result = mysql_query($query) or die('Waypoint delete update failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' aypoint delete failed: ' . mysqli_connect_error());

    $query = "delete from tblBucket where traPk=$id";
    // $result = mysql_query($query) or die('Bucket delete failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Bucket delete failed: ' . mysqli_connect_error());

    $query = "delete from tblComTaskTrack where traPk=$id$comcl";
    // $result = mysql_query($query) or die('ComTaskTrack delete failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' ComTaskTrack delete failed: ' . mysqli_connect_error());
}

if ($comPk > 0)
{
    $query = "select comType from tblCompetition where comPk=$comPk";
    // $result = mysql_query($query) or die('Com type query failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Com type query failed: ' . mysqli_connect_error());
//    $comType = mysql_result($result, 0, 0);
    $comType = mysqli_result($result, 0, 0);

    if ($comType == 'RACE')
    {
        #$sql = "SELECT T.*, P.* FROM tblTaskResult CTT left join tblTrack T on CTT.traPk=T.traPk left outer join tblPilot P on T.pilPk=P.pilPk where CTT.tasPk in (select tasPk from tblTask TK where TK.comPk=$comPk) order by T.traStart desc";
        $sql = "(
                SELECT T.*, P.* FROM tblTrack T 
                    left outer join tblTaskResult CTT on CTT.traPk=T.traPk 
                    left outer join tblPilot P on T.pilPk=P.pilPk 
                where CTT.tasPk in (select tasPk from tblTask TK where TK.comPk=$comPk)
            )
            union
            (
                SELECT T.*, P.* FROM tblComTaskTrack CTT 
                    join tblTrack T on CTT.traPk=T.traPk 
                    left outer join tblPilot P on T.pilPk=P.pilPk 
                where CTT.comPk=$comPk
            ) 
            order by traStart desc";
    }
    else
    {
        $sql = "SELECT T.*, P.* 
            FROM tblComTaskTrack CTT 
            join tblTrack T 
                on CTT.traPk=T.traPk 
            left outer join tblPilot P 
                on T.pilPk=P.pilPk 
            where CTT.comPk=$comPk order by T.traStart desc";
    }
    echo "<form action=\"track_admin.php?comPk=$comPk\" name=\"trackadmin\" method=\"post\">";
}
else
{
    $limit = '';
    if (!array_key_exists('limit', $_REQUEST))
    {
        $limit = ' limit 100';
    }
    else
    {
        $limval = intval($_REQUEST['limit']);
        if ($limval > 0)
        {
            $limit = " limit $limval";
        }
    }

    $sql = "SELECT T.*, P.*, CTT.comPk from
        tblTrack T
        left outer join tblPilot P on T.pilPk=P.pilPk
        left outer join tblComTaskTrack CTT on CTT.traPk=T.traPk
        order by T.traPk desc$limit";
    
#    $sql = "SELECT T.*, P.*, CTT.comPk 
#            from tblComTaskTrack CTT 
#            left join tblTrack T on CTT.traPk=T.traPk 
#            left outer join tblPilot P on T.pilPk=P.pilPk 
#            order by T.traPk desc$limit";

    echo "<form action=\"track_admin.php\" name=\"trackadmin\" method=\"post\">";
}

// $result = mysql_query($sql,$link) or die ("Track query failed: " . mysql_error());
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Track query failed: ' . mysqli_connect_error());

$count = 1;
echo "<ol>";
// while($row = mysql_fetch_array($result))
while($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $id = $row['traPk'];
    $dist = round($row['traLength']/1000,2);
    $name = $row['pilFirstName'] . " " . $row['pilLastName'];
    $date = $row['traStart'];
    $cpk = 0;
    if (array_key_exists('comPk', $row))
    {
        $cpk = $row['comPk'];
    }
    if ($cpk == 0)
    {
        $cpk = $comPk;
    }
    echo "<li><button type=\"submit\" name=\"delete\" value=\"$id\">del</button>";
    echo "<a href=\"tracklog_map.php?trackid=$id&comPk=$cpk\"> $dist kms by $name at $date.</a><br>\n";
    # echo a delete button ...

    $count++;
}
echo "</ol>";
echo "</form>";
?>
</div>
</body>
</html>

