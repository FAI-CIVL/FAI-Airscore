<?php

function get_comtask($link,$tasPk)
{
    $query = "	SELECT 
					C.*, 
					T.* 
				FROM 
					tblTask T 
					JOIN tblCompetition C USING (comPk)
				WHERE 
					T.tasPk = $tasPk ";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' get_comtask failed: ' . mysqli_connect_error());
    $row = mysqli_fetch_assoc($result);
    return $row;
}

function get_taskwaypoints($link,$tasPk)
{
    $sql = "SELECT 
				T.comPk, 
				T.tasPk, 
				F.forMargin, 
				TW.*, 
				SR.*, 
				W.* 
			FROM 
				tblTask T 
				JOIN tblForComp FC USING (comPk) 
				LEFT OUTER JOIN tblFormula F USING (forPk) 
				JOIN tblTaskWaypoint TW USING (tasPk) 
				JOIN tblShortestRoute SR USING (tawPk) 
				JOIN tblRegionWaypoint W USING (rwpPk) 
			WHERE 
				T.tasPk = $tasPk 
			ORDER BY 
				TW.tawNumber";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' get_task failed: ' . mysqli_connect_error());

    $ret = [];
    while ($row = mysqli_fetch_assoc($result))
    {
        $ret[] = $row;
    }

    return $ret;
}
?>
