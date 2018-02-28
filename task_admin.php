<?php
require_once 'authorisation.php';
require_once 'format.php';
require 'template.php';

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
    echo "Size <input type=\"text\" name=\"radius$tawPk\" size=5 value=\"$radius\">";
}

function update_task($link,$tasPk, $old)
{
    $out = '';
    $retv = 0;

    // Get the old values
    $oldstart = isset($old['tasStartTime']) ? $old['tasStartTime'] : '';
    $oldclose = isset($old['tasStartCloseTime']) ? $old['tasStartCloseTime'] : '';
    $oldfinish = isset($old['tasFinishTime']) ? $old['tasFinishTime'] : '';
    $oldstop = isset($old['tasStoppedTime']) ? $old['tasStoppedTime'] : '';
    $oldtype = isset($old['tasTaskType']) ? $old['tasTaskType'] : '';

    $sql = "select T.*, TW.* from tblTask T left outer join tblTaskWaypoint TW on T.tasPk=TW.tasPk and TW.tawType='goal' where T.tasPk=$tasPk";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task not associated correctly with a competition: ' . mysqli_connect_error());
    $row = mysqli_fetch_assoc($result);

    # we should re-verify all tracks if start/finish changed!
    $newstart = $row['tasStartTime'];
    $newclose = $row['tasStartCloseTime'];
    $newfinish = $row['tasFinishTime'];
    $newstop = $row['tasStoppedTime'];
    $newtype = $row['tasTaskType'];
    $goal = $row['tawType'];

    # FIX: how about Free-bearing?
    if ($oldtype == 'olc' && ($newtype == 'free' || $newtype == 'free-pin'))
    {
        $out = '';
        $retv = 0;
        exec(BINDIR . "task_up.pl $tasPk 0", $out, $retv);
    }
    elseif (($oldtype == 'free' || $newtype == 'free-pin') && $newtype == 'olc')
    {
        $out = '';
        $retv = 0;
        exec(BINDIR . "task_up.pl $tasPk 3", $out, $retv);
    }
    elseif ($goal == 'goal' && ($newstart != $oldstart or $newfinish != $oldfinish or $oldtype != $newtype or $oldclose != $newclose or $oldstop != $newstop))
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
    $result = mysqli_query($link, $query);
    $tracks = [];
    while($row = mysqli_fetch_assoc($result))
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
            exec(BINDIR . "track_verify_sr.pl $tpk $tasPk", $out, $retv);
        }
    }
}

function sane_date($date)
{
    $year = substr($date, 0, 4);
    if ($year < 2000 || $year > 2100)
    {
        return false;
    }
    return true;
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
$tasPk = reqival('tasPk');
$file = __FILE__;

$query = "select comPk from tblTask where tasPk=$tasPk";
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task not associated with a competition: ' . mysqli_connect_error());
$comPk = mysqli_result($result,0,0);


if (reqexists('airspace'))
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

if (reqexists('addair'))
{
    check_admin('admin',$usePk,$comPk);
    $airPk = reqival('airnew');
    $query = "insert into tblTaskAirspace (tasPk, airPk) values ($tasPk, $airPk)";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Failed to connect airspace to task: ' . mysqli_connect_error());
}

if (reqexists('airdel'))
{
    $taPk = reqival('airdel');
    if ($taPk > 0)
    {
        $query = "delete from tblTaskAirspace where taPk=$taPk";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Failed to delete airspace sasociation: ' . mysqli_connect_error());
    }
}

if (reqexists('trackcopy'))
{
    $copyfrom = reqival('copyfrom');
    if ($copyfrom > 0)
    {
        $query = "select comEntryRestrict from tblCompetition where comPk=$comPk";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Failed to query tbl registration: ' . mysqli_connect_error());
        $reged = mysqli_result($result,0,0);
        echo "Copying from: $copyfrom<br>";
        if ($reged == "registered")
        {
            $query = "insert into tblComTaskTrack (comPk, tasPk, traPk) select $comPk, $tasPk, CT.traPk from tblComTaskTrack CT, tblTrack T, tblRegistration R where CT.tasPk=$copyfrom and T.traPk=CT.traPk and T.pilPk=R.pilPk and R.comPk=$comPk";
        }
        else
        {
            $query = "insert into tblComTaskTrack (comPk, tasPk, traPk) select $comPk, $tasPk, CT.traPk from tblComTaskTrack CT where CT.tasPk=$copyfrom";
        }
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Failed to copy task tracks: ' . mysqli_connect_error());
        # task_up
        exec(BINDIR . "task_up.pl $tasPk", $out, $retv);
    }
}

if (reqexists('copytask'))
{
    check_admin('admin',$usePk,$comPk);
    $copytaskpk = reqival('copytaskpk');

    $query = "update tblTask T1, tblTask T2 set T1.tasName=T2.tasName, T1.tasTaskStart=T2.tasTaskStart, T1.tasStartTime=T2.tasStartTime, T1.tasStartCloseTime=T2.tasStartCloseTime, T1.tasFinishTime=T2.tasFinishTime, T1.tasTaskType=T2.tasTaskType, T1.regPk=T2.regPk, T1.tasSSInterval=T2.tasSSInterval, T1.tasDeparture=T2.tasDeparture, T1.tasArrival=T2.tasArrival, T1.tasHeightBonus=T2.tasHeightBonus, T1.tasComment=T2.tasComment where T1.tasPk=$tasPk and T2.tasPk=$copytaskpk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Failed to copy task times: ' . mysqli_connect_error());

    $query = "insert into tblTaskWaypoint (tasPk, rwpPk, tawNumber, tawType, tawHow, tawShape, tawTime, tawRadius) select $tasPk, rwpPk, tawNumber, tawType, tawHow, tawShape, tawTime, tawRadius from tblTaskWaypoint where tasPk=$copytaskpk";
    //echo $query . "<br>";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Failed to copy task waypoints: ' . mysqli_connect_error());
    exec(BINDIR . "task_up.pl $tasPk", $out, $retv);
}

# Update the task itself 
if (reqexists('updatetask'))
{
    check_admin('admin',$usePk,$comPk);

    $query = "select tasStartTime, tasStartCloseTime, tasFinishTime, tasTaskType from tblTask where tasPk=$tasPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task not associated with a Competition: ' . mysqli_connect_error());
    $old = mysqli_fetch_array($result, MYSQLI_BOTH);

    $Name = reqsval('taskname');
    $Date = reqsval('date');
    if (!sane_date($Date))
    {
        die("Unable to update task with illegal date: $Date");
    }

    // Task Start/Finish
    $TaskStart = reqsval('taskstart');
    if (strlen($TaskStart) < 10)
    {
        $TaskStart = $Date . ' ' . $TaskStart;
    }
    $FinishTime = reqsval('taskfinish');
    if (strlen($FinishTime) < 10)
    {
        $FinishTime = $Date . ' ' . $FinishTime;
    }

    // FIX: Launch Close
    // Start gate open/close
    $StartTime = reqsval('starttime');
    if (strlen($StartTime) < 10)
    {
        $StartTime = $Date . ' ' . $StartTime;
    }
    $StartClose = reqsval('startclose');
    if (strlen($StartClose) < 10)
    {
        $StartClose = $Date . ' ' . $StartClose;
    }

    $TaskType = reqsval('tasktype');
    $Interval = reqival('interval');
    $regPk = addslashes($_REQUEST['region']);
    $departure = addslashes($_REQUEST['departure']);
    $arrival = addslashes($_REQUEST['arrival']);
    $height = addslashes($_REQUEST['height']);
    $comment = reqsval('taskcomment');

    $query = "update tblTask set tasName='$Name', tasDate='$Date', tasTaskStart='$TaskStart', tasStartTime='$StartTime', tasStartCloseTime='$StartClose', tasFinishTime='$FinishTime', tasTaskType='$TaskType', regPk=$regPk, tasSSInterval=$Interval, tasDeparture='$departure', tasArrival='$arrival', tasHeightBonus='$height', tasComment='$comment' where tasPk=$tasPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task add failed: ' . mysqli_connect_error());

    $TaskStopped = reqsval('taskstopped');
    if (strlen($TaskStopped) < 10 && strlen($TaskStopped) > 2)
    {
        $TaskStopped = $Date . ' ' . $TaskStopped;
    }

    if (strlen($TaskStopped) > 2)
    {
        $query = "update tblTask set tasStoppedTime='$TaskStopped' where tasPk=$tasPk";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task add failed: ' . mysqli_connect_error());
    }

    update_task($link, $tasPk, $old);
    #update_tracks($link,$tasPk);
}

if (reqexists('fullrescore'))
{
    $out = '';
    $retv = 0;
    exec(BINDIR . "task_up.pl $tasPk", $out, $retv);
}

$query = "select C.comPk, C.comName, C.comEntryRestrict, T.* from tblCompetition C, tblTask T where T.tasPk=$tasPk and T.comPk=C.comPk";
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task select failed: ' . mysqli_connect_error());
$row = mysqli_fetch_assoc($result);
if ($row)
{
    $comName = $row['comName'];
    $comPk = $row['comPk'];
    $comEntryRestrict = $row['comEntryRestrict'];
    $tasName = $row['tasName'];
    $tasDate = $row['tasDate'];
    $tasTaskType = $row['tasTaskType'];
    $tasComment = $row['tasComment'];

    $tasTaskStart = nice_date($tasDate, $row['tasTaskStart']);
    $tasTaskFinish = nice_date($tasDate, $row['tasFinishTime']);
    if ($row['tasStoppedTime'])
    {
        $tasStopped = nice_date($tasDate, $row['tasStoppedTime']);
    }
    else
    {
        $tasStopped = '';
    }

    $tasStartTime = substr($row['tasStartTime'], 11);
    $tasStartCloseTime = nice_date($tasDate,$row['tasStartCloseTime']);

    $tasSSInterval = $row['tasSSInterval'];
    $tasDeparture = $row['tasDeparture'];
    $tasArrival = $row['tasArrival'];
    $tasHeightBonus = $row['tasHeightBonus'];
    $regPk = $row['regPk'];
}

//initializing template header
tpadmin($link,$file,$row);

echo "<h3><a href=\"task_result.php?comPk=$comPk&tasPk=$tasPk\">Results - $tasName ($tasDate)</a></h3>\n";


// Manage waypoints for task ..
if (reqexists('add'))
{
    check_admin('admin',$usePk,$comPk);

    $waynum = addslashes($_REQUEST['number']);
    $waytype = reqsval('waytype');
    $how = reqsval('how');
    $shape = reqsval('shape');
    $waytime = reqsval('waytime');
    $radius = addslashes($_REQUEST['radius']);
    $rwppk = addslashes($_REQUEST['waypoint']);
    if ($waynum == '')
    {
        $sql = "SELECT max(tawNumber) as maxNum FROM tblTaskWaypoint where tasPk=$tasPk";
        $result = mysqli_query($link, $sql);
    	$row = mysqli_fetch_array($result, MYSQLI_BOTH);
        $waynum = 1 + $row['maxNum'];
    }
    $query = "insert into tblTaskWaypoint (tasPk, rwpPk, tawNumber, tawType, tawHow, tawShape, tawTime, tawRadius) values ($tasPk, $rwppk, $waynum, '$waytype', '$how', '$shape', '$waytime', $radius)";
    //echo "$query <br>";

    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Add Task waypoint failed: ' . mysqli_connect_error());
    // update tasDistance ...
    $old = [];
    update_task($link, $tasPk, $old);
}

if (reqexists('delete'))
{
    check_admin('admin',$usePk,$comPk);

    $tawPk = reqival('delete');
    $query = "delete from tblTaskWaypoint where tawPk=$tawPk";
    $out = '';
    $retv = 0;
    exec(BINDIR . "task_up.pl $tasPk", $out, $retv);
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Delete Task waypoint failed: ' . mysqli_connect_error());
    $old = [];
    update_task($link, $tasPk, $old);
}

if (reqexists('update'))
{
    check_admin('admin',$usePk,$comPk);

    $tawPk = reqival('update');
    $waypt = addslashes($_REQUEST["waypoint$tawPk"]);
    $waynum = addslashes($_REQUEST["number$tawPk"]);
    $waytype = addslashes($_REQUEST["waytype$tawPk"]);
    $how = addslashes($_REQUEST["how$tawPk"]);
    $shape = addslashes($_REQUEST["shape$tawPk"]);
    $radius = addslashes($_REQUEST["radius$tawPk"]);

    $query = "update tblTaskWaypoint set tawNumber=$waynum, rwpPk=$waypt, tawType='$waytype', tawHow='$how', tawShape='$shape', tawRadius=$radius where tawPk=$tawPk";
    //echo "$query <br>";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Update Task waypoint failed: ' . mysqli_connect_error());
    $out = '';
    $retv = 0;
    exec(BINDIR . "task_up.pl $tasPk", $out, $retv);
    if (reqexists('debug'))
    {
        foreach ($out as $row)
        {
            echo $row . "<br>";
        }
    }
}

$tasktypes = array (
    'RACE' => 'race',
    'olc' => 'olc',
    'speedrun' => 'speedrun',
    'speedrun-interval' => 'speedrun-interval',
    'free' => 'free',
    'free-bearing' => 'free-bearing',
    'free-pin' => 'free-pin',
    'airgain' => 'airgain',
    'aat' => 'aat'
);

echo "<form action=\"task_admin.php?tasPk=$tasPk\" name=\"taskadmin\" method=\"post\">";
echo "<p><table>";
echo "<tr><td>Name:</td><td><input type=\"text\" name=\"taskname\" value=\"$tasName\" size=9></td>";
echo "<td>Date:</td><td><input type=\"text\" name=\"date\" value=\"$tasDate\" size=10></td><td></td><td></td></tr>";
echo "<tr><td>Region:</td><td>";
$regarr = [];
$sql = "SELECT * FROM tblRegion R";
$result = mysqli_query($link, $sql);
while ($row = mysqli_fetch_assoc($result))
{
    $regDesc = $row['regDescription'];
    $regarr["$regDesc"] = $row['regPk'];
}
output_select('region', $regPk, $regarr); 
echo "</td>";
echo "<td>Task Type:</td><td>";
output_select('tasktype', $tasTaskType, $tasktypes);
echo "</td><td></td><td></td></tr>";
echo "<tr><td>Task Start:</td><td><input type=\"text\" name=\"taskstart\" value=\"$tasTaskStart\" size=9></td>";
echo "<td>Task Finish:</td><td><input type=\"text\" name=\"taskfinish\" value=\"$tasTaskFinish\" size=9></td>";
echo "<td>Task Stopped:</td><td><input type=\"text\" name=\"taskstopped\" value=\"$tasStopped\" size=8></td>";
echo "</tr>";
echo "<tr><td>Start Open:</td><td><input type=\"text\" name=\"starttime\" value=\"$tasStartTime\" size=9></td>";
echo "<td>Start Close:</td><td><input type=\"text\" name=\"startclose\" value=\"$tasStartCloseTime\" size=9></td>";
echo "<td>Gate Interval(s):</td><td><input type=\"text\" name=\"interval\" value=\"$tasSSInterval\" size=4></td>";
echo "</tr>";
echo "<tr><td>Depart Bonus:</td><td>";
output_select('departure', $tasDeparture, array( 'on', 'off', 'leadout', 'kmbonus' ));
echo "</td>";
echo "<td>Arrival Bonus:</td><td>";
output_select('arrival', $tasArrival, array( 'on', 'off' ));
echo "</td>";
echo "<td>Height Bonus:</td><td>";
output_select('height', $tasHeightBonus, array( 'on', 'off' ));
echo "</td>";
echo "</tr></table>";
echo "Comment:<br>";
echo farea("taskcomment", $tasComment, 2, 80);
echo "<br><button type=\"submit\" name=\"updatetask\" value=\"$tasPk\">Update Task</button>";
echo "<hr>";

// Ok - output the waypoints nicely
$count = 1;
$goal = 0;
$sql = "select T.*, RW.* from tblTaskWaypoint T, tblRegionWaypoint RW where T.tasPk=$tasPk and RW.rwpPk=T.rwpPk order by T.tawNumber";
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task waypoint selection failed: ' . mysqli_connect_error());
while ($row = mysqli_fetch_assoc($result))
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

$sql = "select tasDistance, tasShortRouteDistance from tblTask where tasPk=$tasPk";
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task distance not determined: ' . mysqli_connect_error());
$dist = round(floatval(mysqli_result($result, 0, 0))/1000,2);
$shortdist = round(floatval(mysqli_result($result, 0, 1))/1000,2);
echo "<p><b>Total distance: $dist ($shortdist) kms</b><br>";

if ($goal == 0 && $count > 0 && ($tasTaskType == 'race' || $tasTaskType == 'speedrun' || $tasTaskType == 'speedrun-interval'))
{
    echo "<i>Warning: racing tasks require a start and a goal, it will not score correctly.</i><br>\n";
}


echo "<br>";
echo fis('add', 'Add Waypoint', '');
waypoint($link,$tasPk,'','','','waypoint','entry','circle','400');

if ($count == 1)
{
    $copyarr = [];
    // Copy from previous tasks same comp, others on same day ..
    $sql = "select C.comName, T.* from tblCompetition C, tblTask T where C.comPk=T.comPk and (T.comPk=$comPk or T.tasDate='$tasDate') and T.tasPk <> $tasPk"; 
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task Copy selection failed: ' . mysqli_connect_error());
	while ($row = mysqli_fetch_assoc($result))
    {
        $copyarr[$row['comName'].$row['tasName']]= $row['tasPk'];
    }
    echo "<br>Or copy task from: ";
    echo fselect("copytaskpk",'', $copyarr);
    echo fis('copytask', 'Copy', '');
    echo "<br>";
}
echo "</form>";
echo "<br><hr>";
echo "<form action=\"task_result.php?comPk=$comPk&tasPk=$tasPk\" name=\"taskscore\" method=\"post\">";
echo fis('score', 'Score Task', '');
echo "</form>";
echo "<form action=\"task_admin.php?comPk=$comPk&tasPk=$tasPk\" name=\"fullrescore\" method=\"post\">";
echo fis('fullrescore', 'Full Re-Score', '');
echo "</form>";
echo "<form action=\"team_task_result.php?comPk=$comPk&tasPk=$tasPk\" name=\"teamtaskscore\" method=\"post\">";
echo fis('score', 'Team Score', '');
echo "</form>";

echo "<hr>";
echo "<form action=\"task_admin.php?tasPk=$tasPk\" name=\"taskadmin\" method=\"post\">";

// List all associated airspace
$airarr = [];
$query = "select TA.*, A.* from tblTaskAirspace TA, tblAirspace A where TA.tasPk=$tasPk and A.airPk=TA.airPk";
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task Airspace selection failed: ' . mysqli_connect_error());
while ($row = mysqli_fetch_assoc($result))
{
    $taPk = $row['taPk'];
    echo "Class: " . $row['airClass'] . " (from: " . $row['airBase'] . "m to: " . $row['airTops'] . "m) -- " . $row['airName'];
    echo fbut('submit', 'airdel', $taPk, 'del') . '<br>';
}

// in future limit to "nearby" airspace ..
$airarr = [];
$query = "select regCentre from tblRegion where regPk=$regPk";
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Region Centre selection failed: ' . mysqli_connect_error());
if (mysqli_num_rows($result) > 0)
{
    $cenPk = 0+mysqli_result($result, 0, 0);
    $query = "select * from tblAirspace R 
        where R.airPk in (
            select airPk from tblAirspaceWaypoint W, tblRegionWaypoint R where
            R.rwpPk=$cenPk and
            W.awpLatDecimal between (R.rwpLatDecimal-1.5) and (R.rwpLatDecimal+1.5) and
            W.awpLongDecimal between (R.rwpLongDecimal-1.5) and (R.rwpLongDecimal+1.5)
            group by (airPk))
        order by R.airName";
}
else
{
    $query = "select * from tblAirspace R order by R.airName";
}
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Airspace selection failed: ' . mysqli_connect_error());
while ($row = mysqli_fetch_assoc($result))
{
    $airarr[$row['airName']] = $row['airPk'];
}
$sel = fselect('airnew', '', $airarr);
echo $sel;
echo fis('addair', 'Add Airspace', '');
echo "<br><br>";
echo fis('airspace', 'Airspace Check', '');

//if ($comEntryRestrict == 'registered')
{
    $tasarr = [];
    #$sql = "select C.comName, T.* from tblTask T, tblCompetition C where T.tasPk<>$tasPk and T.tasDate='$tasDate' and T.regPk=$regPk and C.comPk=T.comPk";
    $sql = "select C.comName, T.* from tblTask T, tblCompetition C where T.tasPk<>$tasPk and T.tasDate='$tasDate' and C.comPk=T.comPk";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task copy selection failed: ' . mysqli_connect_error());
    while ($row = mysqli_fetch_assoc($result))
    {
        $tasarr[$row['comName']] = $row['tasPk'];
    }
    if (sizeof($tasarr) > 0)
    {
        echo "<hr>";
        echo "Copy registered tracks from: ";
        $sel = fselect('copyfrom', '', $tasarr);
        echo $sel;
        echo fis('trackcopy', 'Copy', '');
    }
}

echo "</form>";

echo "<hr>Bulk tracklog uploads, should be a zip file containing multiple tracks (in top directory) named: FAINum_LastName_etc.igc<br>";
echo "<form enctype=\"multipart/form-data\" action=\"bulk_submit.php?tasPk=$tasPk&comPk=$comPk\" method=\"post\">";

echo "<input type=\"hidden\" name=\"MAX_FILE_SIZE\" value=\"1000000000\">";
echo "<input name=\"userfile\" type=\"file\">";
echo "<input type=\"submit\" name=\"foo\" value=\"Send Tracklog\"></form>";

tpfooter($file);

?>
