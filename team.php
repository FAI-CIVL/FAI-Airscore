<?php

function taskcmp($a, $b)
{
    if (!is_array($a)) return 0;
    if (!is_array($b)) return 0;

    if ($a['tname'] == $b['tname']) 
    {
        return 0;
    }
    return ($a['tname'] < $b['tname']) ? -1 : 1;
}

function team_gap_result($comPk, $how, $param)
{
    $sql = "select TK.*,TR.*,P.* from tblTeamResult TR, tblTask TK, tblTeam P, tblCompetition C where C.comPk=$comPk and TR.tasPk=TK.tasPk and TK.comPk=C.comPk and P.teaPk=TR.teaPk order by P.teaPk, TK.tasPk";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task result query failed: ' . mysqli_connect_error());
    $results = [];
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $score = round($row['terScore']);
        $validity = $row['tasQuality'] * 1000;
        $pilPk = $row['teaPk'];
        $tasName = $row['tasName'];
    
        if (!$results[$pilPk])
        {
            $results[$pilPk] = [];
            $results[$pilPk]['name'] = $row['teaName'];
        }
        //echo "pilPk=$pilPk tasname=$tasName, result=$score<br>\n";
        $perf = 0;
        if ($how == 'ftv') 
        {
            $perf = 0;
            if ($validity > 0)
            {
                $perf = round($score / $validity, 3) * 1000;
            }
        }
        else
        {
            $perf = round($score, 0);
        }
        $results[$pilPk]["${perf}${tasName}"] = array('score' => $score, 'validity' => $validity, 'tname' => $tasName);
    }

    // Do the scoring totals (FTV/X or Y tasks etc)
    $sorted = [];
    foreach ($results as $pil => $arr)
    {
        krsort($arr, SORT_NUMERIC);

        $pilscore = 0;
        if ($how != 'ftv')
        {
            # Max rounds scoring
            $count = 0;
            foreach ($arr as $perf => $taskresult)
            {
                if ($perf == 'name') 
                {
                    continue;
                }
                if ($count < $param)
                {
                    $arr[$perf]['perc'] = 100;
                    $pilscore = $pilscore + $taskresult['score'];
                }
                else
                {
                    $arr[$perf]['perc'] = 0;
                }
                $count++;
                
            }
        }
        else
        {
            # FTV scoring
            $pilvalid = 0;
            foreach ($arr as $perf => $taskresult)
            {
                if ($perf == 'name') 
                {
                    continue;
                }

                //echo "pil=$pil perf=$perf valid=", $taskresult['validity'], " score=", $taskresult['score'], "<br>";
                if ($pilvalid < $param)
                {
                    $gap = $param - $pilvalid;
                    $perc = 0;
                    if ($taskresult['validity'] > 0)
                    {
                        $perc = $gap / $taskresult['validity'];
                    }
                    if ($perc > 1)
                    {
                        $perc = 1;
                    }
                    $pilvalid = $pilvalid + $taskresult['validity'] * $perc;
                    $pilscore = $pilscore + $taskresult['score'] * $perc;
                    $arr[$perf]['perc'] = $perc * 100;
                }
            }   
        }
        // resort arr by task?
        uasort($arr, "taskcmp");
        #echo "pil=$pil pilscore=$pilscore<br>";
        foreach ($arr as $key => $res)
        {
            if ($key != 'name')
            {
                $arr[$res['tname']] = $res;
                unset($arr[$key]);
            }
        }
        $pilscore = round($pilscore,0);
        $sorted["${pilscore}!${pil}"] = $arr;
    }

    krsort($sorted, SORT_NUMERIC);
    return $sorted;
}


function team_agg_result($comPk, $teamsize)
{
    $query = "select TM.teaPk,TK.tasPk,TK.tasName,TM.teaName,P.pilLastName,P.pilFirstName,P.pilPk,TR.tarScore*TP.tepModifier as tepscore from tblTaskResult TR, tblTask TK, tblTrack K, tblPilot P, tblTeam TM, tblTeamPilot TP, tblCompetition C where TP.teaPk=TM.teaPk and P.pilPk=TP.pilPk and C.comPk=TK.comPk and K.traPk=TR.traPk and K.pilPk=P.pilPk and TR.tasPk=TK.tasPk and TM.comPk=C.comPk and C.comPk=$comPk order by TM.teaPk,TK.tasPk,TR.tarScore*TP.tepModifier desc";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Team aggregate query failed: ' . mysqli_connect_error());
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    $htable = [];
    $hres = [];
    $sorted = [];
    $teaPk = 0;
    $tasPk = 0;
    $tastot = 0;
    $total = 0;
    $size = 0;
    while ($row)
    {
        //$tasName = $row['tasName'];
        if ($tasPk != $row['tasPk'])
        {
            if ($size != 0)
            {
                $arr["${tasName}"] = array('score' => round($tastotal,0), 'perc' => 100, 'tname' => $tasName);
            }
            $tasName = $row['tasName'];
            $size = 0;
            $tastotal = 0;
            $tasPk = $row['tasPk'];
            //$arr = [];
        }
        if ($teaPk != $row['teaPk'])
        {
            if ($teaPk == 0)
            {
                $teaPk = $row['teaPk'];
                $tasPk = $tow['tasPk'];
                $arr = [];
                $arr['name'] = $row['teaName'];
            }
            else
            {
                // wrap up last one
                $total = round($total,0);
                $sorted["${total}!${teaPk}"] = $arr;
                $tastotal = 0;
                $total = 0;
                $size = 0;
                $arr = [];
                $arr['name'] = $row['teaName'];
                $teaPk = $row['teaPk'];
            }
        }

        if ($size < $teamsize)
        {
            $total = round($total + $row['tepscore'],2);
            $tastotal = round($tastotal + $row['tepscore'],2);
            $size = $size + 1;
        }
    	$row = mysqli_fetch_array($result, MYSQLI_BOTH);
    }

    // wrap up last one
    $total = round($total,0);
    $arr["${tasName}"] = array('score' => round($tastotal,0), 'perc' => 100, 'tname' => $tasName);
    $sorted["${total}!${teaPk}"] = $arr;

    krsort($sorted, SORT_NUMERIC);
    return $sorted;
}

function team_handicap_result($comPk,$how,$param)
{
    $query = "select T.tasPk, T.tasName, max(TR.tarScore) as maxScore from tblTaskResult TR, tblTask T where T.tasPk=TR.tasPk and T.comPk=$comPk group by TR.tasPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Team aggregate query failed: ' . mysqli_connect_error());
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    $tinfo = [];
    while ($row)
    {
        $tinfo[$row['tasPk']] = array( 'name' => "<a href=\"team_task_result.php?tasPk=" . $row['tasPk'] . "\">" . $row['tasName'] . "</a>", 'maxscore' => $row['maxScore']);
    	$row = mysqli_fetch_array($result, MYSQLI_BOTH);
    }

    $hteams = [];
    $count = 0;
    foreach ($tinfo as $task => $tasinfo)
    {
        $maxscore = intval($tasinfo['maxscore']);
        if ($maxscore < 1)
        {
            next;
        }
        $query = "select TM.teaPk,TK.tasPk,TK.tasName,TM.teaName,sum(TR.tarScore-H.hanHandicap*$maxscore) as handiscore from tblTaskResult TR, tblTask TK, tblTrack K, tblPilot P, tblTeam TM, tblTeamPilot TP, tblHandicap H, tblCompetition C where TP.teaPk=TM.teaPk and P.pilPk=TP.pilPk and C.comPk=TK.comPk and K.traPk=TR.traPk and K.pilPk=P.pilPk and H.pilPk=P.pilPk and TR.tasPk=TK.tasPk and TM.comPk=C.comPk and TK.tasPk=$task and H.comPk=$comPk group by TM.teaPk";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Team handicap query failed: ' . mysqli_connect_error());
    	$row = mysqli_fetch_array($result, MYSQLI_BOTH);
        while ($row)
        {
            //echo "task=$task teaPk=" . $row['teaPk'] . "=" . $row['handiscore'] . "<br>";
            if (array_key_exists($row['teaPk'], $hteams))
            {
                $htable = $hteams[$row['teaPk']];
                $htable['scores'][$count] = $row['handiscore'];
                $htable['total'] = round($htable['total'] + $row['handiscore'],0);
                $hteams[$row['teaPk']] = $htable;
            }
            else
            {
                $htable = [];
                $htable['team'] = $row['teaName'];
                $htable['scores'] = [];
                for ($i = 0; $i < $count; $i++)
                {
                    $htable['scores'][$i] = 0;
                }
                $htable['scores'][$count] = $row['handiscore'];
                $htable['total'] =  round($row['handiscore'],0);
                $hteams[$row['teaPk']] = $htable;
            }

    		$row = mysqli_fetch_array($result, MYSQLI_BOTH);
        }
        $count++;
    
    }
    $hres = [];
    foreach ($hteams as $res)
    {
        $total = $res['total'];
        $team = $res['team'];
        $hres["${total}${team}"] = $res;
    }
    krsort($hres, SORT_NUMERIC);

    $sorted = [];
    $place = 1;
    $htable = [];
    $title = array( fb("Res"), fb("Team"), fb("Total"));
    foreach ($tinfo as $task => $tasinfo)
    {
        $title[] = fb($tasinfo['name']);
    }
    $htable[] = $title;

    foreach ($hres as $res => $pils)
    {
        $row = array( fb("$place"), $pils['team'], $pils['total'] );
        foreach ($pils['scores'] as $tas => $sco)
        {
            $row[] = round($sco,0);
        }
        $htable[] = $row;
        $place = $place + 1;
    }

    echo ftable($htable, "border=\"0\" cellpadding=\"3\" alternate-colours=\"yes\" align=\"center\"", array('class="l"', 'class="d"'), '');
}
?>
