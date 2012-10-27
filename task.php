<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<div id="vhead"><h1>airScore admin</h1></div>
<?php
require_once 'authorisation.php';
require_once 'format.php';

function waypoint($link,$tasPk, $tawPk, $num, $waypt, $type, $how, $shape, $radius)
{
    echo "<input type=\"text\" name=\"number$tawPk\" value=\"$num\" size=1>";
    echo "Way ";
    waypoint_select($link, $tasPk, "waypoint$tawPk", $waypt);
    echo "Type ";
    output_select("waytype$tawPk", $type, array('waypoint', 'start', 'speed', 'endspeed', 'goal')); 
    echo "How ";
    output_select("how$tawPk", $how, array('entry', 'exit')); 
    echo "Shape ";
    output_select("shape$tawPk", $shape, array('circle', 'semicircle', 'line')); 
    echo "Size <input type=\"text\" name=\"radius$tawPk\" size=2 value=\"$radius\">";
}

function update_task($link,$tasPk, $old)
{
    $out = '';
    $retv = 0;

    // Get the old values
    $oldstart = $old['tasStartTime'];
    $oldclose = $old['tasStartCloseTime'];
    $oldfinish = $old['tasFinishTime'];
    $oldtype = $old['tasTaskType'];

    $sql = "select T.*, TW.* from tblTask T left outer join tblTaskWaypoint TW on T.tasPk=TW.tasPk and TW.tawType='goal' where T.tasPk=$tasPk";
    $result = mysql_query($sql,$link) 
        or die('Task not associated correctly with a competition: ' . mysql_error());
    $row = mysql_fetch_array($result);

    # we should re-verify all tracks if start/finish changed!
    $newstart = $row['tasStartTime'];
    $newclose = $row['tasStartCloseTime'];
    $newfinish = $row['tasFinishTime'];
    $newtype = $row['tasTaskType'];
    $goal = $row['tawType'];

    # FIX: how about Free-bearing?
    if ($oldtype == 'OLC' && $newtype == 'Free')
    {
        $out = '';
        $retv = 0;
        exec(BINDIR . "task_up.pl $tasPk 0", $out, $retv);
    }
    elseif ($oldtype == 'Free' && $newtype == 'OLC')
    {
        $out = '';
        $retv = 0;
        exec(BINDIR . "task_up.pl $tasPk 3", $out, $retv);
    }
    elseif ($goal == 'goal' && ($newstart != $oldstart or $newfinish != $oldfinish or $oldtype != $newtype or $oldclose != $newclose))
    {
        $out = '';
        $retv = 0;
        exec(BINDIR . "task_up.pl $tasPk", $out, $retv);
    }
}

function update_tracks($link,$tasPk)
{
    // Now check for pre-submitted tracks ..
    $query = "select traPk from tblComTaskTrack where tasPk=$tasPk";
    $result = mysql_query($query,$link);
    $tracks = array();
    while($row = mysql_fetch_array($result))
    {
        $tracks[] = $row['traPk'];
    }

    if (sizeof($tracks) > 0)
    {
        // Now verify the pre-submitted tracks against the task
        foreach ($tracks as $tpk)
        {
            #echo "Verifying effected track: $tpk<br>";
            $out = '';
            $retv = 0;
            exec(BINDIR . "track_verify.pl $tpk", $out, $retv);
        }
    }
}

function nice_date($today, $date)
{
    if ($today == substr($date, 0, 10))
    {
        $ret = substr($date, 11);
    }
    else
    {
        $ret = $date;
    }
    return $ret;
}

$usePk = auth('system');
$link = db_connect();
$tasPk = intval($_REQUEST['tasPk']);

$query = "select comPk from tblTask where tasPk=$tasPk";
$result = mysql_query($query) or die('Task not associated with a competition: ' . mysql_error());
$comPk = mysql_result($result,0,0);
adminbar($comPk);
$link = db_connect();


if (array_key_exists('airspace', $_REQUEST))
{
    check_admin('admin',$usePk,$comPk);
    $out = '';
    $retv = 0;
    exec(BINDIR . "airspace_check.pl $tasPk", $out, $retv);
    foreach ($out as $row)
    {  
        echo $row . "<br>";
    }
}

if (array_key_exists('addair', $_REQUEST))
{
    check_admin('admin',$usePk,$comPk);
    $airPk = intval($_REQUEST['airnew']);
    $query = "insert into tblTaskAirspace (tasPk, airPk) values ($tasPk, $airPk)";
    $result = mysql_query($query) or die('Failed to connect airspace to task ' . mysql_error());
}

if (array_key_exists('airdel', $_REQUEST))
{
    $taPk = intval($_REQUEST['airnew']);
    if ($taPk > 0)
    {
        $query = "delete from tblTaskAirspace where taPk=$taPk";
        $result = mysql_query($query) or die('Failed to delete airspace association ' . mysql_error());
    }
}

// Update the task itself 
if (array_key_exists('updatetask', $_REQUEST))
{
    #$tasPk = intval($_REQUEST['updatetask']);
    check_admin('admin',$usePk,$comPk);

    $query = "select tasStartTime, tasStartCloseTime, tasFinishTime, tasTaskType from tblTask where tasPk=$tasPk";
    $result = mysql_query($query) 
        or die('Task not associated with a competition: ' . mysql_error());
    $old = mysql_fetch_array($result);

    $Name = addslashes($_REQUEST['taskname']);
    $Date = addslashes($_REQUEST['date']);

    // Task Start/Finish
    $TaskStart = addslashes($_REQUEST['taskstart']);
    if (strlen($TaskStart) < 10)
    {
        $TaskStart = $Date . ' ' . $TaskStart;
    }
    $FinishTime = addslashes($_REQUEST['taskfinish']);
    if (strlen($FinishTime) < 10)
    {
        $FinishTime = $Date . ' ' . $FinishTime;
    }

    // FIX: Launch Close

    // Start gate open/close
    $StartTime = addslashes($_REQUEST['starttime']);
    if (strlen($StartTime) < 10)
    {
        $StartTime = $Date . ' ' . $StartTime;
    }
    $StartClose = addslashes($_REQUEST['startclose']);
    if (strlen($StartClose) < 10)
    {
        $StartClose = $Date . ' ' . $StartClose;
    }

    $TaskType = addslashes($_REQUEST['tasktype']);
    $Interval = intval($_REQUEST['interval']);
    $regPk = addslashes($_REQUEST['region']);
    $departure = addslashes($_REQUEST['departure']);
    $arrival = addslashes($_REQUEST['arrival']);

    $query = "update tblTask set tasName='$Name', tasDate='$Date', tasTaskStart='$TaskStart', tasStartTime='$StartTime', tasStartCloseTime='$StartClose', tasFinishTime='$FinishTime', tasTaskType='$TaskType', regPk=$regPk, tasSSInterval=$Interval, tasDeparture='$departure', tasArrival='$arrival' where tasPk=$tasPk";

    $result = mysql_query($query) or die('Task add failed: ' . mysql_error());

    update_task($link, $tasPk, $old);

    #update_tracks($link,$tasPk);
}

$query = "select C.comPk, C.comName, T.* from tblCompetition C, tblTask T where T.tasPk=$tasPk and T.comPk=C.comPk";
$result = mysql_query($query) or die('Task select failed: ' . mysql_error());
$row = mysql_fetch_array($result);
if ($row)
{
    $comName = $row['comName'];
    $comPk = $row['comPk'];
    $tasName = $row['tasName'];
    $tasDate = $row['tasDate'];
    $tasTaskType = $row['tasTaskType'];

    $tasTaskStart = nice_date($tasDate, $row['tasTaskStart']);
    $tasTaskFinish = nice_date($tasDate, $row['tasFinishTime']);

    $tasStartTime = substr($row['tasStartTime'], 11);
    $tasStartCloseTime = nice_date($tasDate,$row['tasStartCloseTime']);

    $tasSSInterval = $row['tasSSInterval'];
    $tasDeparture = $row['tasDeparture'];
    $tasArrival = $row['tasArrival'];
    $regPk = $row['regPk'];
}

echo "<p><h2><a href=\"task_result.php?comPk=$comPk&tasPk=$tasPk\">$comName - $tasName ($tasDate)</a></h2></p>";


// Manage waypoints for task ..
if (array_key_exists('add', $_REQUEST))
{
    check_admin('admin',$usePk,$comPk);

    $waynum = addslashes($_REQUEST['number']);
    $waytype = addslashes($_REQUEST['waytype']);
    $how = addslashes($_REQUEST['how']);
    $shape = addslashes($_REQUEST['shape']);
    $radius = addslashes($_REQUEST['radius']);
    $rwppk = addslashes($_REQUEST['waypoint']);
    if ($waynum == '')
    {
        $sql = "SELECT max(tawNumber) as maxNum FROM tblTaskWaypoint where tasPk=$tasPk";
        $result = mysql_query($sql,$link);
        $row = mysql_fetch_array($result);
        $waynum = 1 + $row['maxNum'];
    }
    $query = "insert into tblTaskWaypoint (tasPk, rwpPk, tawNumber, tawType, tawHow, tawShape, tawTime, tawRadius) values ($tasPk, $rwppk, $waynum, '$waytype', '$how', '$shape', '$waytime', $radius)";
    //echo "$query <br>";

    $result = mysql_query($query) or die('Add Task waypoint failed: ' . mysql_error());
    // update tasDistance ...
    $old = array();
    update_task($link, $tasPk, $old);
}

if (array_key_exists('delete', $_REQUEST))
{
    check_admin('admin',$usePk,$comPk);

    $tawPk = intval($_REQUEST['delete']);
    $query = "delete from tblTaskWaypoint where tawPk=$tawPk";
    $out = '';
    $retv = 0;
    exec(BINDIR . "task_up.pl $tasPk", $out, $retv);
    $result = mysql_query($query) or die('Delete TaskWaypoint failed: ' . mysql_error());
}

if (array_key_exists('update', $_REQUEST))
{
    check_admin('admin',$usePk,$comPk);

    $tawPk = intval($_REQUEST['update']);
    $waypt = addslashes($_REQUEST["waypoint$tawPk"]);
    $waynum = addslashes($_REQUEST["number$tawPk"]);
    $waytype = addslashes($_REQUEST["waytype$tawPk"]);
    $how = addslashes($_REQUEST["how$tawPk"]);
    $shape = addslashes($_REQUEST["shape$tawPk"]);
    $radius = addslashes($_REQUEST["radius$tawPk"]);

    $query = "update tblTaskWaypoint set tawNumber=$waynum, rwpPk=$waypt, tawType='$waytype', tawHow='$how', tawShape='$shape', tawRadius=$radius where tawPk=$tawPk";
    //echo "$query <br>";
    $result = mysql_query($query) or die('Update TaskWaypoint failed: ' . mysql_error());
    $out = '';
    $retv = 0;
    exec(BINDIR . "task_up.pl $tasPk", $out, $retv);
    if (array_key_exists('debug', $_REQUEST))
    {
        foreach ($out as $row)
        {
            echo $row . "<br>";
        }
    }
}

$tasktypes = array (
    'olc' => 'olc',
    'RACE' => 'race',
    'speedrun' => 'speedrun',
    'speedrun-interval' => 'speedrun-interval',
    'free' => 'free',
    'free-bearing' => 'free-bearing',
    'airgain' => 'airgain',
    'aat' => 'aat'
);

echo "<form action=\"task.php?tasPk=$tasPk\" name=\"taskadmin\" method=\"post\">";
echo "<p><table>";
echo "<tr><td>Name:</td><td><input type=\"text\" name=\"taskname\" value=\"$tasName\" size=10></td>";
echo "<td>Date:</td><td><input type=\"text\" name=\"date\" value=\"$tasDate\" size=10></td></tr>";
echo "<tr><td>Region:</td><td>";
$regarr = array();
$sql = "SELECT * FROM tblRegion R";
$result = mysql_query($sql,$link);
while ($row = mysql_fetch_array($result))
{
    $regDesc = $row['regDescription'];
    $regarr["$regDesc"] = $row['regPk'];
}
output_select('region', $regPk, $regarr); 
echo "</td>";
echo "<td>Task Type:</td><td>";
output_select('tasktype', $tasTaskType, $tasktypes);
echo "</td></tr>";
echo "<tr><td>Task Start:</td><td><input type=\"text\" name=\"taskstart\" value=\"$tasTaskStart\" size=10></td>";
echo "<td>Task Finish:</td><td><input type=\"text\" name=\"taskfinish\" value=\"$tasTaskFinish\" size=10></td>";
echo "</tr>";
echo "<tr><td>Start Open:</td><td><input type=\"text\" name=\"starttime\" value=\"$tasStartTime\" size=10></td>";
echo "<td>Start Close:</td><td><input type=\"text\" name=\"startclose\" value=\"$tasStartCloseTime\" size=10></td>";
echo "<td>Gate Interval(s):</td><td><input type=\"text\" name=\"interval\" value=\"$tasSSInterval\" size=3></td>";
echo "</tr>";
echo "<tr><td>Depart Bonus:</td><td>";
output_select('departure', $tasDeparture, array( 'on', 'off', 'leadout' ));
echo "</td>";
echo "<td>Arrival Bonus:</td><td>";
output_select('arrival', $tasArrival, array( 'on', 'off' ));
echo "</td></tr></table>";
echo "<button type=\"submit\" name=\"updatetask\" value=\"$tasPk\">Update Task</button>";
echo "<hr>";
// Ok - output the waypoints nicely
$count = 1;
$goal = 0;
$sql = "select T.*, RW.* from tblTaskWaypoint T, tblRegionWaypoint RW where T.tasPk=$tasPk and RW.rwpPk=T.rwpPk order by T.tawNumber";
$result = mysql_query($sql,$link) or die('Task Waypoint Selection failed: ' . mysql_error());
while ($row = mysql_fetch_array($result))
{
    $tawPk = $row['tawPk'];
    $number = $row['tawNumber'];
    $name = $row['rwpName'];
    $rwpPk = $row['rwpPk'];
    $wtype = $row['tawType'];
    $how = $row['tawHow'];
    $shape = $row['tawShape'];
    $radius = $row['tawRadius'];

    //echo "<button type=\"submit\" name=\"update\" value=\"$tawPk\">up</button>";
    echo "<button type=\"submit\" name=\"update\" value=\"$tawPk\">up</button>";
    waypoint($link,$tasPk,$tawPk,$number,$rwpPk,$wtype,$how,$shape,$radius);
    echo "<button type=\"submit\" name=\"delete\" value=\"$tawPk\">del</button>";

    echo "<br>\n";
    if ($wtype == 'goal')
    {
        $goal = 1;
    }

    $count++;
}
$sql = "select tasDistance from tblTask where tasPk=$tasPk";
$result = mysql_query($sql,$link) or die('Can\'t determine task distance: ' . mysql_error());
$dist = round(floatval(mysql_result($result, 0, 0))/1000,2);
echo "<p><b>Total distance: $dist kms</b><br>";

if ($goal == 0 && $count > 0 && ($tasTaskType == 'race' || $tasTaskType == 'speedrun' || $tasTaskType == 'speedrun-interval'))
{
    echo "<i>Warning: racing tasks require a start and a goal, it will not score correctly.</i><br>\n";
}

echo "<br>";
echo fis('add', 'Add Waypoint', '');
waypoint($link,$tasPk,'','','','waypoint','entry','circle','400');
echo "</form>";
echo "<br><hr>";
echo "<form action=\"task_result.php?comPk=$comPk&tasPk=$tasPk\" name=\"taskscore\" method=\"post\">";
echo fis('score', 'Score Task', '');
echo "</form>";
echo "<form action=\"team_task_result.php?comPk=$comPk&tasPk=$tasPk\" name=\"taskscore\" method=\"post\">";
echo fis('score', 'Team Score', '');
echo "</form>";

echo "<hr>";
echo "<form action=\"task.php?tasPk=$tasPk\" name=\"taskadmin\" method=\"post\">";
// List all associated airspace
$airarr = array();
$query = "select TA.*, A.* from tblTaskAirspace TA, tblAirspace A where TA.tasPk=$tasPk and A.airPk=TA.airPk";
$result = mysql_query($query) or die('TaskAirspace select failed: ' . mysql_error());
while ($row = mysql_fetch_array($result))
{
    $taPk = $row['taPk'];
    echo "Class: " . $row['airClass'] . " (from: " . $row['airBase'] . "m to: " . $row['airTops'] . "m) -- " . $row['airName'];
    echo "<button type=\"submit\" name=\"airdel\" value=\"$taPk\">del</button><br>";
}

// in future limit to "nearby" airspace ..
$airarr = array();
$query = "select * from tblAirspace order by airName";
$result = mysql_query($query) or die('Task select failed: ' . mysql_error());
while ($row = mysql_fetch_array($result))
{
    $airarr[$row['airName']] = $row['airPk'];
}
//output_select("air$airPk", $how, array('entry', 'exit')); 
$sel = fselect('airnew', '', $airarr);
echo $sel;
echo fis('addair', 'Add Airspace', '');
echo "<br><br>";
echo fis('airspace', 'Airspace Check', '');
echo "</form>";

echo "<hr>Bulk tracklog uploads, should be a zip file containing multiple tracks (in top directory) named: FAINum_LastName_etc.igc<br>";
echo "<form enctype=\"multipart/form-data\" action=\"bulk_submit.php?tasPk=$tasPk&comPk=$comPk\" method=\"post\">";
?>
<input type="hidden" name="MAX_FILE_SIZE" value="1000000000">
<input name="userfile" type="file">
<input type="submit" name="foo" value="Send Tracklog"></form>
</div>
</body>
</html>

