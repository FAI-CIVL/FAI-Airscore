<?php
function get_comtask($link,$tasPk)
{
    $query = "select C.*, T.* from tblCompetition C, tblTask T where T.tasPk=$tasPk and T.comPk=C.comPk";
    $result = mysql_query($query,$link) or die('get_comtask failed: ' . mysql_error());
    $row = mysql_fetch_array($result);
    return $row;
}

function get_taskwaypoints($link,$tasPk)
{
    $sql = "SELECT T.*,SR.*,W.* FROM tblTaskWaypoint T, tblShortestRoute SR, tblRegionWaypoint W where T.tasPk=$tasPk and SR.tawPk=T.tawPk and W.rwpPk=T.rwpPk order by T.tawNumber";
    $result = mysql_query($sql,$link) or die('get_task failed: ' . mysql_error());

    $ret = array();
    while($row = mysql_fetch_array($result))
    {
        $ret[] = $row;
    }

    return $ret;
}
?>
