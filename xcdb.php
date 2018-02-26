<?php

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

function get_comtask($link,$tasPk)
{
    $query = "select C.*, T.* from tblCompetition C, tblTask T where T.tasPk=$tasPk and T.comPk=C.comPk";
//    $result = mysql_query($query,$link) or die('get_comtask failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' get_comtask failed: ' . mysqli_connect_error());
//    $row = mysql_fetch_array($result, MYSQL_ASSOC);
    $row = mysqli_fetch_assoc($result);
    return $row;
}

function get_taskwaypoints($link,$tasPk)
{
    $sql = "SELECT T.*,SR.*,W.* FROM tblTaskWaypoint T, tblShortestRoute SR, tblRegionWaypoint W where T.tasPk=$tasPk and SR.tawPk=T.tawPk and W.rwpPk=T.rwpPk order by T.tawNumber";
//    $result = mysql_query($sql,$link) or die('get_task failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' get_task failed: ' . mysqli_connect_error());

    $ret = [];
//    while ($row = mysql_fetch_array($result, MYSQL_ASSOC))
    while ($row = mysqli_fetch_assoc($result))
    {
        $ret[] = $row;
    }

    return $ret;
}
?>
