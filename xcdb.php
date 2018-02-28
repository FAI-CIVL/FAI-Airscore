<?php

function get_comtask($link,$tasPk)
{
    $query = "select C.*, T.* from tblCompetition C, tblTask T where T.tasPk=$tasPk and T.comPk=C.comPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' get_comtask failed: ' . mysqli_connect_error());
    $row = mysqli_fetch_assoc($result);
    return $row;
}

function get_taskwaypoints($link,$tasPk)
{
    $sql = "SELECT T.comPk, T.tasPk, F.forMargin, TW.*,SR.*,W.* FROM tblTask T, tblFormula F, tblTaskWaypoint TW, tblShortestRoute SR, tblRegionWaypoint W where T.tasPk=$tasPk and TW.tasPk=T.tasPk and SR.tawPk=TW.tawPk and W.rwpPk=TW.rwpPk and F.comPk=T.comPk order by TW.tawNumber";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' get_task failed: ' . mysqli_connect_error());

    $ret = [];
    while ($row = mysqli_fetch_assoc($result))
    {
        $ret[] = $row;
    }

    return $ret;
}
?>
