
<?php
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Content-type: application/json');

require 'authorisation.php';
require 'xcdb.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

$usePk = check_auth('system');
$tasPk = reqival('tasPk');
$trackid = reqival('trackid');

function track_progress($tasPk, $trackid)
{
    $res = [];
    $turnpoints = 0;
    $merge = 0;
    $link = db_connect();
    if ($trackid > 0)
    {
        $sql = "select tarTurnpoints from tblTaskResult where traPk=$trackid";
//        $result = mysql_query($sql,$link) or die('Task turnpoints failed: ' . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task turnpoints failed: ' . mysqli_connect_error());
//        $turnpoints = mysql_result($result, 0, 0);
        $turnpoints = mysqli_result($result, 0, 0);

        $sql = "select T2.traPk from tblTrack T1, tblTrack T2 where T2.pilPk=T1.pilPk and T2.traStart between date_sub(T1.traStart, interval 6 hour) and date_add(T1.traStart, interval 6 hour) and T1.traPk=$trackid and T2.traPk<>T1.traPk";
//        $result = mysql_query($sql,$link) or die('Duplicate track select failed: ' . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Duplicate track select failed: ' . mysqli_connect_error());
//        if (mysql_num_rows($result) > 0)
        if (mysqli_num_rows($result) > 0)
        {
//            $merge = mysql_result($result, 0, 0);
            $merge = mysqli_result($result, 0, 0);
        }
    }

    $res['turnpoints']= $turnpoints;
    $res['merge']= $merge;
    $res['task']= get_taskwaypoints($link,$tasPk);

    return $res;
}

$res = track_progress($tasPk,$trackid);
$data = $res;
print json_encode($data);
?>


