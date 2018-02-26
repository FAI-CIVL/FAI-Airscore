<?php

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

function olc_sort($result,$top)
{
    $lastpil = 0;
    $topscores = [];
    $toptasks = [];

    // fetch the rows from the db
//    while ($row = mysql_fetch_array($result,MYSQL_ASSOC))
    while ($row = mysqli_fetch_assoc($result))
    {
        // another pilot .. finish it off
        $pilPk = $row['pilPk'];
        if (!array_key_exists($pilPk, $toptasks))
        {
            $toptasks[$pilPk] = [];
        }
        array_push($toptasks[$pilPk], $row);
    }

    // do the totals ...
    foreach ($toptasks as $pilPk => $scores)
    {
        // cut to max ..
        $scores = array_slice($scores,0,$top);
        $total = 0;

        foreach ($scores as $row)
        {
            $total = $total + $row['adjScore'];
            $first = $row['pilFirstName'];
            $last = $row['pilLastName'];
        }

        $total = $total . $last;
        $topscores[$total] = array( 
                    'total' => $total,
                    'tasks' => $scores,
                    'pilpk' => $pilPk,
                    'firstname' => $first,
                    'lastname' => $last
            );
    }

    krsort($topscores, SORT_NUMERIC);

    return $topscores;
}
function olc_result($link,$top,$restrict)
{
    $sql = "SELECT P.*, T.traPk, T.traScore as adjScore FROM tblTrack T, tblPilot P, tblComTaskTrack CTT, tblCompetition C where CTT.comPk=C.comPk and CTT.traPk=T.traPk and T.pilPk=P.pilPk and T.traScore is not null $restrict order by P.pilPk, T.traScore desc";
//    $result = mysql_query($sql,$link) or die('olc_result: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' olc_result: ' . mysqli_connect_error());

    return olc_sort($result,$top);
}
function olc_handicap_result($link,$top,$restrict)
{
    $sql = "SELECT P.*, T.traPk, (T.traScore * H.hanHandicap) as adjScore FROM 
                tblTrack T, tblPilot P, tblComTaskTrack CTT, 
                tblCompetition C, tblHandicap H
            where 
                H.comPk=C.comPk and H.pilPk=P.pilPk and
                CTT.comPk=C.comPk and CTT.traPk=T.traPk and T.pilPk=P.pilPk 
                and T.traScore is not null $restrict 
            order by P.pilPk, T.traScore desc";
//    $result = mysql_query($sql,$link) or die('Top score: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Top score: ' . mysqli_connect_error());

    return olc_sort($result,$top);
}
function display_olc_result($comPk, $rtable, $sorted, $top, $count, $start)
{
    $rdec = [];
    $rdec[] = 'class="h"';
    $rdec[] = 'class="h"';

    foreach ($sorted as $total => $row)
    {
        $nxt = [];
        if ($count % 2)
        {
            $rdec[] = 'class="d"';
        }
        else
        {
            $rdec[] = 'class="l"';
        }
        $name = $row['firstname'] . " " . $row['lastname'];
        $key = $row['pilpk'];
        $total = round($total/1000,0);
        $nxt[] = $count;
        $nxt[] = "<a href=\"pilot.php?pil=$key\">$name</a>";
        $nxt[] = "<b>$total</b>";
        foreach ($row['tasks'] as $task)
        {
            $score = round($task['adjScore']/1000,1);
            $id = $task['traPk'];
            $nxt[] = "<a href=\"tracklog_map.php?comPk=$comPk&trackid=$id\">$score</a>";
        }
        $count++;
        if ($count >= $top + $start + 2) 
        {
            break;
        }
        $rtable[] = $nxt;
    }
    echo ftable($rtable, "class=\"olc\" alternate-colours=\"yes\" align=\"center\"", $rdec, '');

    return $count;
}
function olc_team_result($link,$top,$restrict)
{
    $sql = "SELECT M.teaPk as pilPk, M.teaName as pilFirstName, T.traPk, T.traScore as adjScore FROM tblTrack T, tblComTaskTrack CTT, tblCompetition C, tblTeam M, tblTeamPilot TP, tblPilot P where M.comPk=C.comPk and TP.teaPk=M.teaPk and P.pilPk=TP.pilPk and CTT.comPk=C.comPk and CTT.traPk=T.traPk and T.pilPk=P.pilPk and T.traScore is not null $restrict order by M.teaPk, T.traScore desc";
//    $result = mysql_query($sql,$link) or die('olc_result: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' olc_result: ' . mysqli_connect_error());

    return olc_sort($result,$top);
}
?>
