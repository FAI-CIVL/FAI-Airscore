<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<?php
require 'authorisation.php';

// Return a list of the pilots top (4) results 
function generate_ladder($top,$restrict,$link)
{
    $lastpil = 0;
    $toptasks = [];
    $topscores = [];

    $sql = "SELECT P.*, T.traPk, T.traScore FROM tblTrack T, tblPilot P, tblComTaskTrack CTT where CTT.traPk=T.traPk and T.pilPk=P.pilPk and T.traScore is not null $restrict order by P.pilPk, T.traScore desc";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Top score failed: ' . mysqli_connect_error());
    ;

    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        // another pilot .. finish it off
        $pilPk = $row['pilPk'];
        if (!$toptasks[$pilPk])
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
            $total = $total + $row['traScore'];
            $first = $row['pilFirstName'];
            $last = $row['pilLastName'];
        }

        $total = $total . $last;
        $topscores[$total] = array( 
                    'total' => $total,
                    'tasks' => $scores,
                    'firstname' => $first,
                    'lastname' => $last
            );
    }

    krsort($topscores, SORT_NUMERIC);

    return $topscores;
}


$restrict='';
$comPk = 0;
if (array_key_exists('comPk', $_REQUEST))
{
    $comPk = addslashes($_REQUEST['comPk']);
    $restrict = " and CTT.comPk=$comPk";
}

menubar($comPk);

$link = db_connect();

if ($comPk != 0)
{
     $sql = "select C.comName from tblCompetition C where C.comPk=$comPk";
     $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Top scores failed: ' . mysqli_connect_error());
     $comName = mysqli_result($result,0);
     $title = " - $comName";
}
echo "<p><h2>Top Scores$title</h2></p>";

$topscores = generate_ladder(4,$restrict,$link);
echo "<table border=\"5\" cellpadding=\"3\" alternate-colours=\"yes\" align=\"center\">";
echo "<tr class=\"h\"><td><b>Place</b></td><td><b>Pilot</b></td><td><b>Total</b></td><td><b>Task 1</b1></td><td><b>Task 2</b></td><td><b>Task 3</b></td><td><b>Task 4</b></td></tr>\n";
$count = 1;
foreach ($topscores as $total => $row)
{
    if ($count % 2)
    {
        echo "<tr class=\"d\">";
    }
    else
    {
        echo "<tr class=\"l\">";
    }
    $name = $row['firstname'] . " " . $row['lastname'];
    $total = round($total/1000,2);
    echo "<td>$count</td><td>$name</td><td>$total</td>\n";
    foreach ($row['tasks'] as $task)
    {
        $score = round($task['traScore']/1000,1);
        $id = $task['traPk'];
        echo "<td><a href=\"tracklog_map.php?comPk=$comPk&trackid=$id\">$score</a></td>";
    }
    $count++;
    echo "</tr>";
}
echo "</table>";

if ($count == 1)
{
    echo "<b>No tracks submitted for $comName yet.</b>\n";
}
?>
</div>
</body>
</html>

