<?php
require 'authorisation.php';
require 'template.php';

$comPk = reqival('comPk');
$file = __FILE__;
$usePk=auth('system');
$link = db_connect();

//initializing template header
$query = "SELECT * FROM tblCompetition where comPk=$comPk";
$result = mysqli_query($link, $query);
$row = mysqli_fetch_assoc($result);
tpadmin($link,$file,$row);

if ($comPk > 0)
{
    $comName = $row['comName'];
    echo "<h3>Track Administration ($comName)</h3>\n";
}
else
{
    echo "<h3>Track Administration (global)</h3>\n";
}

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
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Track Info failed: ' . mysqli_connect_error());
    if (mysqli_num_rows($result) == 0)
    {
        $query = "SELECT comPk FROM tblComTaskTrack where traPk=$id$comcl";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Track info failed: ' . mysqli_connect_error());
    }
    if (mysqli_num_rows($result) > 0)
    {
        $lco = mysqli_result($result,0,0);
    }

    if (!check_admin('admin',$usePk, $lco))
    {
        die("You cannot delete tracks for that competition($lco)<br>");
        return;
    }

    $query = "delete from tblTaskResult where traPk=$id";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' TaskResult delete failed: ' . mysqli_connect_error());

    $query = "delete from tblTrack where traPk=$id";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Track delete failed: ' . mysqli_connect_error());

    $query = "delete from tblTrackLog where traPk=$id";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Tracklog delete failed: ' . mysqli_connect_error());

    $query = "delete from tblWaypoint where traPk=$id";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' aypoint delete failed: ' . mysqli_connect_error());

    $query = "delete from tblBucket where traPk=$id";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Bucket delete failed: ' . mysqli_connect_error());

    $query = "delete from tblComTaskTrack where traPk=$id$comcl";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' ComTaskTrack delete failed: ' . mysqli_connect_error());
}

if ($comPk > 0)
{
    $query = "select comType from tblCompetition where comPk=$comPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Com type query failed: ' . mysqli_connect_error());
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

$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Track query failed: ' . mysqli_connect_error());

$count = 1;
echo "<ol>";
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

tpfooter($file);

?>


