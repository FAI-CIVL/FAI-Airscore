<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<div id="vhead"><h1>airScore admin</h1></div>
<?php
require 'authorisation.php';
require 'format.php';
$comPk = intval($_REQUEST['comPk']);
adminbar($comPk);

$usePk = auth('system');
$link = db_connect();
$query = "select comName from tblCompetition where comPk=$comPk";
$result = mysql_query($query) or die('Task add failed: ' . mysql_error());
$comName = mysql_result($result,0);

echo "<p><h2>Competition - $comName</h2></p>";

// Add a task
if (array_key_exists('add', $_REQUEST))
{
    $Name = addslashes($_REQUEST['taskname']);
    $Date = addslashes($_REQUEST['date']);
    $StartTime = addslashes($_REQUEST['starttime']);
    $FinishTime = addslashes($_REQUEST['finishtime']);
    $TaskType = addslashes($_REQUEST['tasktype']);
    $Interval = intval($_REQUEST['interval']);
    $regPk = addslashes($_REQUEST['region']);

    check_admin('admin',$usePk,$comPk);

    $query = "insert into tblTask (comPk, tasName, tasDate, tasStartTime, tasFinishTime, tasSSInterval, tasTaskType, regPk) values ($comPk, '$Name', '$Date', '$Date $StartTime', '$Date $FinishTime', $Interval, '$TaskType', $regPk)";
    $result = mysql_query($query) or die('Task add failed: ' . mysql_error());

    // Get the task we just inserted
    $tasPk = mysql_insert_id();

    #$query = "select max(tasPk) from tblTask";
    #$result = mysql_query($query) or die('Cant get max tasPk: ' . mysql_error());
    #$tasPk = mysql_result($result,0,0);

    // Now check for pre-submitted tracks ..
    $query = "select traPk from tblComTaskTrack where comPk=$comPk and tasPk is null";
    $result = mysql_query($query,$link);
    $tracks = array();
    while($row = mysql_fetch_array($result))
    {
        $tracks[] = $row['traPk'];
    }

    if (sizeof($tracks) > 0)
    {
        // Give them a task number 
        $sql = "update tblComTaskTrack set tasPk=$tasPk where comPk=$comPk and tasPk is null";
        $result = mysql_query($sql,$link);

        // Now verify the pre-submitted tracks against the task
        foreach ($tracks as $tpk)
        {
            echo "Verifying pre-submitted track: $tpk<br>";
            $out = '';
            $retv = 0;
            exec(BINDIR . "track_verify.pl $tpk", $out, $retv);
        }
    }
}

// Delete a task
if (array_key_exists('delete', $_REQUEST))
{
    $id = intval($_REQUEST['delete']);
    check_admin('admin',$usePk,$comPk);

    if ($id > 0)
    {
        $query = "delete from tblTask where tasPk=$id";
        $result = mysql_query($query) or die('Task delete failed: ' . mysql_error());
    
        $query = "delete from tblComTaskTrack where tasPk=$id";
        $result = mysql_query($query) or die('Task CTT delete failed: ' . mysql_error());
    
        $query = "delete from tblTaskWaypoint where tasPk=$id";
        $result = mysql_query($query) or die('Task TW delete failed: ' . mysql_error());
    
        $query = "delete from tblTaskResult where tasPk=$id";
        $result = mysql_query($query) or die('Task TR delete failed: ' . mysql_error());

        echo "Task Removed\n";
    }
    else
    {
        echo "Unable to remove task: $id\n";
    }
}

// Update the competition
if (array_key_exists('update', $_REQUEST))
{
    check_admin('admin',$usePk,$comPk);

    $comname = addslashes($_REQUEST['comname']);
    $datefrom = addslashes($_REQUEST['datefrom']);
    $dateto = addslashes($_REQUEST['dateto']);
    $location = addslashes($_REQUEST['location']);
    $director = addslashes($_REQUEST['director']);
    $sanction = addslashes($_REQUEST['sanction']);
    $comptype = addslashes($_REQUEST['comptype']);
    $comcode = addslashes($_REQUEST['code']);
    $timeoffset = floatval($_REQUEST['timeoffset']);
    $overallscore = addslashes($_REQUEST['overallscore']);
    $overallparam = floatval($_REQUEST['overallparam']); 

    $query = "update tblCompetition set comName='$comname', comLocation='$location', comDateFrom='$datefrom', comDateTo='$dateto', comMeetDirName='$director', comTimeOffset=$timeoffset, comType='$comptype', comCode='$comcode', comOverallScore='$overallscore', comOverallParam=$overallparam where comPk=$comPk";

    $result = mysql_query($query) or die('Competition update failed: ' . mysql_error());
}

// Add/update the formula
if (array_key_exists('upformula', $_REQUEST))
{
    $forPk = intval($_REQUEST['forPk']) + 0;
    $formula = addslashes($_REQUEST['formula']);
    $version = addslashes($_REQUEST['version']);
    $nomdist = addslashes($_REQUEST['nomdist']);
    $mindist = addslashes($_REQUEST['mindist']);
    $nomtime = addslashes($_REQUEST['nomtime']);
    $nomgoal = addslashes($_REQUEST['nomgoal']);

    if ($forPk < 1)
    {
        $query = "insert into tblFormula (forClass, forVersion, forNomDistance, forMinDistance, forNomTime, forNomGoal, comPk) values ('$formula', '$version', $nomdist, $mindist, $nomtime, $nomgoal, $comPk)";
        $result = mysql_query($query) or die('Formula addition failed: ' . mysql_error());
        $forPk = mysql_insert_id();

        #$query = "select max(forPk) from tblFormula";
        #$result = mysql_query($query) or die('Cant get max forPk: ' . mysql_error());
        #$forPk = mysql_result($result,0,0);

        $query = "update tblCompetition set forPk=$forPk where comPk=$comPk";
        $result = mysql_query($query) or die('Competition formula addition failed: ' . mysql_error());
    }
    else
    {
        $query = "update tblFormula set forClass='$formula', forVersion='$version', forNomDistance=$nomdist, forMinDistance=$mindist, forNomTime=$nomtime, forNomGoal=$nomgoal where comPk=$comPk";
        $result = mysql_query($query) or die('Formula update failed: ' . mysql_error());
    }
}

$forPk = 0;
$sql = "SELECT T.* FROM tblCompetition T where T.comPk=$comPk";
$result = mysql_query($sql,$link);
$row = mysql_fetch_array($result);
if ($row)
{
    echo "<form action=\"competition.php?comPk=$comPk\" name=\"comedit\" method=\"post\">";
    $cname = $row['comName'];
    $cdfrom = substr($row['comDateFrom'],0,10);
    $cdto = substr($row['comDateTo'],0,10);
    $cdirector = $row['comMeetDirName'];
    $clocation = $row['comLocation'];
    $csanction = $row['comSanction'];
    $ctimeoffset = $row['comTimeOffset'];
    $overallscore = $row['comOverallScore'];
    $overallparam = $row['comOverallParam'];
    $ccode = $row['comCode'];
    $ctype = $row['comType'];
    $forPk = $row['forPk'];

    $out = ftable(
        array(
            array('Name:', fin('comname', $cname, 14), 'Type:', fselect('comptype', $ctype, array('OLC', 'RACE', 'Free', 'Route' ))),
            array('Date From:', fin('datefrom', $cdfrom, 10), 'Date To:', fin('dateto', $cdto, 10)),
            array('Director:', fin('director', $cdirector, 14), 'Location:', fin('location', $clocation, 10)),
            array('Abbrev:', fin('code', $ccode, 10), 'Time Offset:', fin('timeoffset', $ctimeoffset, 10)),
            array('Scoring:', fselect('overallscore', $overallscore, array('all', 'ftv', 'round', 'round-perc' )), 'Score param:', fin('overallparam', $overallparam, 4))
        ), '', '', ''
    );

    echo $out;
    echo fis('update', 'Update Competition', '');
    echo "</form>\n";
}
// Formula
if ($ctype == 'RACE')
{
    $sql = "SELECT F.* FROM tblFormula F where F.comPk=$comPk";
    $result = mysql_query($sql,$link);
    $row = mysql_fetch_array($result);
    if ($row)
    {
        $class = $row['forClass'];
        $version = $row['forVersion'];
        $nomdist = $row['forNomDistance'];
        $mindist = $row['forMinDistance'];
        $nomtime = $row['forNomTime'];
        $nomgoal = $row['forNomGoal'];
    }
    echo "<hr><h3>RACE Formula</h3>";
    echo "<form action=\"competition.php?comPk=$comPk\" name=\"formulaadmin\" method=\"post\">";
    $out = ftable(
        array(
          array('Formula:', fselect('formula', $class, array('gap', 'ozgap', 'pwd', 'sahpa' )), 'Year:', fin('version', $version, 4)),
          array('Nom Dist (km):', fin('nomdist',$nomdist,4), 'Min Dist (km):', fin('mindist', $mindist, 4)),
          array('Nom Goal (%):', fin('nomgoal',$nomgoal,4), 'Nom Time (min):', fin('nomtime', $nomtime, 4))
        ), '', '', ''
      );
    echo $out;
    echo "<input type=\"hidden\" name=\"forPk\" value=\"$forPk\">";
    echo "<input type=\"submit\" name=\"upformula\" value=\"Update Formula\">";
    echo "</form>";
}


if ($ctype == 'RACE' || $ctype == 'Route')
{
// Tasks
echo "<hr><h3>Tasks</h3><form action=\"competition.php?comPk=$comPk\" name=\"taskadmin\" method=\"post\">";
echo "<ol>";
$count = 1;
$sql = "SELECT T.* FROM tblTask T where T.comPk=$comPk order by T.tasDate";
$result = mysql_query($sql,$link);

while($row = mysql_fetch_array($result))
{
    $tasPk = $row['tasPk'];
    $tasDate = $row['tasDate'];
    $tasName = $row['tasName'];
    $tasDistance = $row['tasDistance'];
    $tasStartTime = $row['tasStartTime'];
    $tasFinishTime = $row['tasFinishTime'];
    $tasResultsType = $row['tasResultsType'];
    $tasTaskType = $row['tasTaskType'];
    $tasDistance = $row['tasDistance'];
    $tasSSDistance = $row['tasSSDistance'];
    $tasSSOpen = $row['tasSSOpen'];
    $tasSSClose = $row['tasSSClose'];
    $tasESClose = $row['tasESClose'];
    $tasDistFlown = $row['tasTotalDistanceFlown'];

    echo "<li><button type=\"submit\" name=\"delete\" value=\"$tasPk\">del</button>";
    echo "<a href=\"task.php?comPk=$comPk&tasPk=$tasPk\">$tasName: " . round($tasDistance/1000,1) . " kms on " . $tasDate . " (" . substr($tasStartTime,11) . " - " . substr($tasFinishTime,11) . ")</a></li>\n";

    $count++;
}
echo "</ol>";

$sql = "SELECT * FROM tblRegion R";
$result = mysql_query($sql,$link);
$regions = array();
while ($row = mysql_fetch_array($result))
{
    $regPk = $row['regPk'];
    $regDesc = $row['regDescription'];
    $regions[$regDesc] = $regPk;
}
echo "<hr>";
$out = ftable(
    array(
        array('Task Name:', fin('taskname', '', 10), 'Date:', fin('date', '', 10)),
        array('Region:', fselect('region', '', $regions), 'Task Type:', fselect('tasktype', 0, array('olc', 'race', 'speedrun', 'speedrun-interval', 'free', 'free-bearing'))),
        array('Start Time:', fin('starttime', '', 10), 'Finish Time:', fin('finishtime', '', 10), 'Gate Interval:', fin('interval', '', 4)), 
        array('Depart Bonus:', fin('depart', '', 10), 'Arrival Bonus:', fin('arrival', '', 10))
    ), '', '', '');

echo $out;
echo "<input type=\"submit\" name=\"add\" value=\"Add Task\">";

echo "</form>";
}
?>
</div>
</body>
</html>

