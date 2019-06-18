<?php
require 'admin_startup.php';

function waypoint($link,$tasPk, $tawPk, $num, $waypt, $type, $how, $shape, $radius)
{

    echo "<input type=\"text\" name=\"number$tawPk\" value=\"$num\" size=1>";
    echo "Way ";
    waypoint_select($link, $tasPk, "waypoint$tawPk", $waypt);
    echo "Type ";
    output_select("waytype$tawPk", $type, array('waypoint', 'launch', 'speed', 'endspeed', 'goal'));
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

    # Get the old values
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
    if ($oldtype == 'olc' && ($newtype == 'free distance' || $newtype == 'distance with bearing'))
    {
        $out = '';
        $retv = 0;
        exec(BINDIR . "task_up.pl $tasPk 0", $out, $retv);
    }
    elseif (($oldtype == 'free distance' || $newtype == 'distance with bearing') && $newtype == 'olc')
    {
        $out = '';
        $retv = 0;
        exec(BINDIR . "task_up.pl $tasPk 3", $out, $retv);
    }
    elseif ($goal == 'goal' && ($newstart != $oldstart or $newfinish != $oldfinish or $oldtype != $newtype or $oldclose != $newclose or $oldstop != $newstop))
    {
        $out = '';
        $retv = 0;
        exec("python3 " . BINDIR . "update_task.py $tasPk", $out, $retv);
    }
    return "Task succesfully updated. \n";

}

// function full_rescore($tasPk, $comPk, $type, $param=null)
// {
//     $out = '';
//     $retv = 0;
//  $command = BINDIR . "task_up.pl $tasPk $param" . ' > /dev/null 2>&1 & echo $!; ';
//
//     $pid = exec($command, $out, $retv);
//     $ptime = microtime(true);
//     redirect("task_scoring_admin.php?tasPk=$tasPk&comPk=$comPk&pid=$pid&time=$ptime&type=$type");
// }

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

// Main Code Begins HERE //

$usePk = auth('system');
$link = db_connect();
$tasPk = reqival('tasPk');
$file = __FILE__;

$query = "select C.comPk, C.comExt from tblCompetition C JOIN tblTask USING(comPk) where tasPk=$tasPk";
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task not associated with a competition: ' . mysqli_connect_error());
$comPk = mysqli_result($result,0,0);
$ext = mysqli_result($result,0,1);
$message = '';
$content = '';

if ( $ext )
{
    $message = '* External Competition *';
    $content = 'Event was imported. Editing options are disabled.';
}

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

if (reqexists('updated'))
{
    $message = "Task updated succesfully";
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
    $message .= 'Task succesfully copied. \n';
    $content .= "Information pulled from task ID $copytaskpk. \n";
}

# Update the task itself
if (reqexists('updatetask'))
{
    check_admin('admin',$usePk,$comPk);

    $query = "select tasStartTime, tasStartCloseTime, tasFinishTime, tasTaskType from tblTask where tasPk=$tasPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task not associated with a Competition: ' . mysqli_connect_error());
    $old = mysqli_fetch_array($result, MYSQLI_BOTH);

    if ( !$ext )
    {
        $Name = reqsval('taskname');
        $Date = reqsval('date');
        if (!sane_date($Date))
        {
            die("Unable to update task with illegal date: $Date");
        }

        # Task Start/Finish
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

        # FIX: Launch Close
        # Start gate open/close
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
        $checklaunch = addslashes($_REQUEST['checklaunch']);
        $height = addslashes($_REQUEST['height']);
        $comment = reqsval('taskcomment');
        # check margin percentage
        if ( reqfval('margin') <= 100 )
        {
            $margin = abs( reqfval('margin') );
        }
        else
        {
            $margin = 0.5;
        }

        $query = "  UPDATE
                        `tblTask`
                    SET
                        `tasName` = '$Name',
                        `tasDate` = '$Date',
                        `tasTaskStart` = '$TaskStart',
                        `tasStartTime` = '$StartTime',
                        `tasStartCloseTime` = '$StartClose',
                        `tasFinishTime` = '$FinishTime',
                        `tasTaskType` = '$TaskType',
                        `regPk` = $regPk,
                        `tasSSInterval` = $Interval,
                        `tasDeparture` = '$departure',
                        `tasArrival` = '$arrival',
                        `tasHeightBonus` = '$height',
                        `tasCheckLaunch` = '$checklaunch',
                        `tasComment` = '$comment',
                        `tasMarginOverride` = $margin
                    WHERE
                        `tasPk` = $tasPk ";

        mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task update failed: ' . mysqli_connect_error());

        $TaskStopped = reqsval('taskstopped');
        if (strlen($TaskStopped) < 10 && strlen($TaskStopped) > 2)
        {
            $TaskStopped = $Date . ' ' . $TaskStopped;
        }

        if (strlen($TaskStopped) > 2)
        {
            $query = "update tblTask set tasStoppedTime='$TaskStopped' where tasPk=$tasPk";
            $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Stopped Task update query failed: ' . mysqli_connect_error());
        }

        update_task($link, $tasPk, $old);
        $message .= "Task successfully updated \n";
    }
    else
    {
        $comment = reqsval('taskcomment');
        $query = "UPDATE tblTask SET tasComment='$comment' WHERE tasPk=$tasPk";

        mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' External Task update failed: ' . mysqli_connect_error());
        $message .= "External Task successfully updated \n";
    }



}

if (reqexists('fullrescore'))
{
    $command = BINDIR . "task_up.pl $tasPk" . ' > /dev/null 2>&1 & echo $!; ';
    safe_process($link, $command, $tasPk, $comPk, 'score');
}

if (reqexists('taskscore'))
{
    $out = '';
    $retv = 0;
    $command = "python3 " . BINDIR . "score_task.py $tasPk > " . BINDIR . 'log/scoretask.txt 2>&1 & echo $!; ';
    $pid = exec($command, $out, $retv);
    $ptime = microtime(true);
    # redirect to avoid Timeout if script takes too long
    sleep(25);
    // if ( script_isRunning($pid) )
    // {
    //     redirect("safe_process_admin.php?tasPk=$tasPk&comPk=$comPk&pid=$pid&time=$ptime&task=1");
    // }
    $content .= "Task has been scored. <br />\n";
}

# Manage waypoints for task ..
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

    mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Add Task waypoint failed: ' . mysqli_connect_error());
    // update tasDistance ...
    $old = [];
    $message .= update_task($link, $tasPk, $old);
    $content .= "Waypoint added. \n";
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
    $message .= update_task($link, $tasPk, $old);
    $content .= "Waypoint deleted. \n";
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
    mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Update Task waypoint failed: ' . mysqli_connect_error());
//  full_rescore($tasPk, $comPk, 'update');
    $old = [];
    $message .= update_task($link, $tasPk, $old);
    $content .= "Waypoint updated. \n";
}

# Upload a task file generated from xc-track
elseif ( reqexists('XCTask') )
{
    copy($_FILES['taskfile']['tmp_name'], FILEDIR . basename($_FILES['taskfile']['name']));
    chmod(FILEDIR . basename($_FILES['taskfile']['name']), 0644);

    $tempnm = FILEDIR . basename($_FILES['taskfile']['name']);

    $out = '';
    $retv = 0;
    $command = "python3 " . BINDIR . "import_xctrack_task.py $tasPk $tempnm > " . BINDIR . 'log/xctask.txt 2>&1 & echo $!; ';
    echo $command;
    $pid = exec($command, $out, $retv);
    sleep(25);
    if ($retv)
    {
        $message .= "Failed to upload your Task File.<br>\n";

    }
    else
    {
        $message .= "Task File correctly processed.<br>\n";
        # Show results
        $content .= "<p class=\'bulk_script\'>\n";
        foreach ($out as $txt)
        {
            $content .= "$txt <br />\n";
        }
        $content .= "</p>\n";
        $out = '';
        $retv = 0;
        $command = "python3 " . BINDIR . "score_task.py $tasPk > " . BINDIR . 'log/scoretask.txt 2>&1 & echo $!; ';
        $pid = exec($command, $out, $retv);
        $ptime = microtime(true);
        # redirect to avoid Timeout if script takes too long
        sleep(15);
        if ( script_isRunning($pid) )
        {
            redirect("safe_process_admin.php?tasPk=$tasPk&comPk=$comPk&pid=$pid&time=$ptime&task=1");
        }
        $content .= "A task has been set from XC-Track informations. <br />\n";
    }
}

$query = "  SELECT
                *
            FROM
                TaskView
            WHERE
                tasPk = $tasPk
            LIMIT 1";
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
    $ext = $row['comExt'];

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
    $tasCheckLaunch = $row['tasCheckLaunch'];
    $tasHeightBonus = $row['tasHeightBonus'];
    $tasMargin = $row['tasMargin'];
    $regPk = $row['regPk'];
}

$tasktypes = array (
    'RACE' => 'race',
    'elapsed time' => 'elapsed time',
    'free distance' => 'free distance',
    'distance with bearing' => 'distance with bearing',
);

$regarr = [];
$sql = "SELECT * FROM tblRegion R";
$result = mysqli_query($link, $sql);
while ($reg = mysqli_fetch_assoc($result))
{
    $regDesc = $reg['regDescription'];
    $regarr["$regDesc"] = $reg['regPk'];
}

# Create Tables
$ttable = [];
$atable = [];
$ftable = [];
$ctable = [];
$wtable = [];

# Create Task Info table

# Case External Competition
if ( $ext )
{
    $ttable[] = array("Name: ", $tasName, "Date: ", $tasDate, '', '');
    $ttable[] = array('', '', "Task Type: ", $tasTaskType, '', '');
    $ttable[] = array("Window opens: ", $tasTaskStart, "Task deadline: ", $tasTaskFinish, "Task Stopped: ", $tasStopped);
    $ttable[] = array("START opens: ", $tasStartTime, "START closed: ", $tasStartCloseTime, "Gate Interval(s): ", $tasSSInterval);
}
else
{
    $ttable[] = array("Name: ", fin('taskname', $tasName, 'width16'), "Date: ", fin('date', $tasDate, 'width10'), '', '');
    $ttable[] = array("Region: ", fselect('region', $regPk, $regarr), "Task Type: ", fselect('tasktype', $tasTaskType, $tasktypes), '', '');
    $ttable[] = array("Window opens: ", fin('taskstart', $tasTaskStart, 'width8'), "Task deadline: ", fin('taskfinish', $tasTaskFinish, 'width8'), "Task Stopped: ", fin('taskstopped', $tasStopped, 'width8'));
    $ttable[] = array("START opens: ", fin('starttime', $tasStartTime, 'width8'), "START closed: ", fin('startclose', $tasStartCloseTime, 'width8'), "Gate Interval(s): ", fin('interval', $tasSSInterval, 'width4'));
}

## Options only for non external events

if ( !$ext )
{
    # Create Advanced Options table

    $atable[] = array("Depart Bonus: ", fselect('departure', $tasDeparture, array( 'on', 'off', 'leadout', 'kmbonus' )), " default: leadout ", "Arrival Bonus: ", fselect('arrival', $tasArrival, array( 'on', 'off' )), " default: HG on / PG off ");
    $atable[] = array("Height Bonus: ", fselect('height', $tasHeightBonus, array( 'on', 'off' )), " default: off ", "Launch Check: ", fselect('checklaunch', $tasCheckLaunch, array( 'on', 'off' )), " default: off ", '', '', '');
    $atable[] = array('Radius Margin Override %: ', fin('margin', $tasMargin, 4), 'Default: Scoring Formula Margin', '', '', '', '', '', '', '', '', '');

    # Create the task file upload table
    $ftable[] = array(" <input type=\"hidden\" name=\"MAX_FILE_SIZE\" value=\"1000000000\">",
                            "<input name=\"taskfile\" type=\"file\">",  "<input type=\"submit\" name=\"XCTask\" value=\"Send XC-Track File\">");
}

# Create the Task Waypoint list table
$wtable[] = array('', '', "Name: ", "Type: ", "How: ", "Shape: ", "Size (m): ", '');

$count = 1;
$goal = 0;
$sql = "SELECT
            T.*,
            RW.*
        FROM
            tblTaskWaypoint T
            JOIN tblRegionWaypoint RW USING (rwpPk)
        WHERE
            T.tasPk = $tasPk
        ORDER BY
            T.tawNumber";
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task waypoint selection failed: ' . mysqli_connect_error());
while ($wpt = mysqli_fetch_assoc($result))
{
    $tawPk = $wpt['tawPk'];
    $number = $wpt['tawNumber'];
    $name = $wpt['rwpName'];
    $rwpPk = $wpt['rwpPk'];
    $wtype = $wpt['tawType'];
    $how = $wpt['tawHow'];
    $shape = $wpt['tawShape'];
    $radius = $wpt['tawRadius'];

    if ( $ext )
    {
        $wtable[] = array(  '',
                            $number,
                            $name,
                            $wtype,
                            $how,
                            $shape,
                            $radius,
                            ''
                        );
    }
    else
    {
        $wtable[] = array(  fbut('submit','delete',$tawPk,'Delete'),
                            fin("number$tawPk", $number, 'width4'),
                            fwaypoint($link, $tasPk, "waypoint$tawPk", $rwpPk),
                            fselect("waytype$tawPk", $wtype, array('waypoint', 'launch', 'speed', 'endspeed', 'goal')),
                            fselect("how$tawPk", $how, array('entry', 'exit')),
                            fselect("shape$tawPk", $shape, array('circle', 'semicircle', 'line')),
                            fin("radius$tawPk", $radius, 'width6'),
                            fbut('submit','update',$tawPk,'Update')
                        );
    }

    if ($wtype == 'goal')
    {
        $goal = 1;
    }

    $count++;
}

$wtable[] = array("<hr />");

if ( !$ext )
{
    $wtable[] = array(  '',
                        fin("number", '', 'width4'),
                        fwaypoint($link, $tasPk, "waypoint", ''),
                        fselect("waytype", "waypoint", array('waypoint', 'launch', 'speed', 'endspeed', 'goal')),
                        fselect("how", "entry", array('entry', 'exit')),
                        fselect("shape", "circle", array('circle', 'semicircle', 'line')),
                        fin("radius", "400", 'width6'),
                        fis('add', 'Add Waypoint', '')
                    );
}
# Create the task copy from previous ones table
if ($count == 1)
{
    $copyarr = [];
    # Copy from previous tasks same comp, others on same day ..
    $sql = "SELECT
                C.comName,
                T.*
            FROM
                tblCompetition C
                JOIN tblTask T USING (comPk)
            WHERE
                (
                    T.comPk = $comPk
                    OR T.tasDate = '$tasDate'
                )
                AND T.tasPk <> $tasPk";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task Copy selection failed: ' . mysqli_connect_error());
    while ($task = mysqli_fetch_assoc($result))
    {
        $copyarr[$task['comName'] . ' | ' . $task['tasName']] = $task['tasPk'];
    }

    $ctable[] = array("Copy Waypoints from Task: ", fselect("copytaskpk",'', $copyarr), fis('copytask', 'Copy', ''));
}

# Get Task Distances
$sql = "select tasDistance, tasShortRouteDistance from tblTask where tasPk=$tasPk";
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task distance not determined: ' . mysqli_connect_error());
$dist = round(floatval(mysqli_result($result, 0, 0))/1000,2);
$shortdist = round(floatval(mysqli_result($result, 0, 1))/1000,2);

//initializing template header
tpadmin($link,$file,$row);

echo "<h3>$tasName ($tasDate)</h3>\n";
echo "<h4><a href=\"/task_result.php?comPk=$comPk&tasPk=$tasPk\">Results</a></h4>\n";
echo "<hr />\n";

# Messages field
//$message .= 'prova funzionamento';
if ( $message !== '')
{
    //echo "<h4> <span style='color:red'>Prova</span> </h4>" . PHP_EOL;
    echo "<h4> <span style='color:red'>$message</span> </h4>" . PHP_EOL;
    echo "<br />" . PHP_EOL;
    echo "<hr />" . PHP_EOL;
}

# Content field
if ( $content !== '')
{
    echo "$content" . PHP_EOL;
    echo "<br />" . PHP_EOL;
    echo "<hr />" . PHP_EOL;
}

# Display task info
echo "<h4>Task Info:</h4>\n";
echo "<form enctype=\"multipart/form-data\" name=\"taskadmin\" action=\"task_admin.php?tasPk=$tasPk&comPk=$comPk\" method=\"post\">\n";
echo ftable($ttable,"class='format tinfotable'", '', '');
echo "<hr />\n";

if ( !$ext )
{
    # Display Advanced setup
    echo "<p class='warning'>advanced</p>\n";
    echo "<p class='explanation'>This parameters are usually correct by default.<br>\n";
    echo ftable($atable,"class='format tadvtable'", '', '');
}
echo "<hr />\n";

echo "Comment:<br>";
echo farea("taskcomment", $tasComment, 2, 80);
echo "<br><button type=\"submit\" name=\"updatetask\" value=\"$tasPk\">Update Task</button>";
echo "<hr>";

# Display WPT Definistion
echo "<h4>Task Definition:</h4>\n";
if ( !$ext )
{
    # Upload xc-track task file
    echo "<p class='explanation'>You can upload the XCTSK file generated by XC-Track:<br>\n";
    echo "<p class='warning'>This will overwrite task definition without warning.<br>\n";
    echo ftable($ftable,"class='format taskfiletable'", '', '');
    echo "<hr>";
}
#copy task from previous
if ( !empty($ctable) && !$ext)
{
    echo "<p class='explanation'>You can copy definition from a previous task:<br>\n";
    echo ftable($ctable,"class='format taskfiletable'", '', '');
    echo "<hr />";
}
echo "<p class='explanation'>Insert / Modify / Delete Waypoints:<br>\n";
echo ftable($wtable,"class='format wpttable'", '', '');
echo "<br /></form>";

if ($goal == 0 && $count > 0 && ($tasTaskType == 'race' || $tasTaskType == 'elapsed time'))
{
    echo "<p class='warning'>Warning: racing tasks require a launch and a goal, it will not score correctly otherwise.</p><br>\n";
}
elseif ( $goal == 1 )
{
    # Display Task Distance, Track Management and Scoring if task is set
    echo "<hr>";
    echo "<p class='taskDistance'><span>Optimised Distance: $shortdist Km </span> <span>|  </span> <span> Distance through Centres: $dist Km </span><br>";
    echo "<br /><hr /> \n";

    if ( !$ext )
    {
        # Display Track manager
        echo "<form action=\"tasktrack_admin.php?comPk=$comPk&tasPk=$tasPk\" name=\"tasktrack\" method=\"post\"> \n";
        echo "<h4>Track Manager:</h4>\n";
        echo "<p class='explanation'>Permits to add or delete tracks, set pilots DNF or ABS, upload zip file or get tracks from XContest server.<br>\n";
        echo fis('trackmanager', 'Manage Tracks', '');
        echo "</form> \n";
        echo "<br><hr> \n";

        # Display Scoring Section
        echo "<h4>Scoring:</h4>\n";
        echo "<form action=\"task_admin.php?comPk=$comPk&tasPk=$tasPk\" name=\"taskscore\" method=\"post\"> \n";
        echo "<p class='explanation'>Score Task will add tracks not yet scored.<br>\n";
        echo fis('taskscore', 'Score Task', '');
        echo "</form> \n";
        echo "<form action=\"task_admin.php?comPk=$comPk&tasPk=$tasPk\" name=\"fullrescore\" method=\"post\"> \n";
        echo "<p class='explanation'>Full Re-Score will recalculate task distance, and will verify all tracks. Could take a while.<br>\n";
        echo fis('fullrescore', 'Full Re-Score', '');
        echo "</form> \n";
        echo "<form action=\"../team_task_result.php?comPk=$comPk&tasPk=$tasPk\" name=\"teamtaskscore\" method=\"post\"> \n";
        echo fis('score', 'Team Score', '');
        echo "</form> \n";
    }
}
echo "<hr>";

# Email Notification
echo '<h4> Email Notification to Pilots</h4>';
echo "<p class='explanation'>Will send a remainder to all pilots yet without a valid track for the task.<br>\n";
echo "<form action=\"email_admin.php?comPk=$comPk&tasPk=$tasPk\" name=\"sendmail\" method=\"post\"> \n";
echo fis('sendmail', 'Send Email to missing Pilots', '');
echo fis('sendmail', 'Send TEST Email to your address only', '');
echo "</form>";
echo "<hr />";

# Airspace Section
if ( !$ext )
{
    echo "<form action=\"task_admin.php?tasPk=$tasPk\" name=\"taskadmin\" method=\"post\">";

    # List all associated airspace
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
        $query = "  SELECT
                        A.*
                    FROM
                        tblAirspace A
                    WHERE
                        A.airPk IN (
                            SELECT
                                W.airPk
                            FROM
                                tblAirspaceWaypoint W
                                JOIN tblRegionWaypoint R ON (
                                    W.awpLatDecimal BETWEEN (R.rwpLatDecimal - 1.5)
                                    AND (R.rwpLatDecimal + 1.5)
                                )
                                AND (
                                    W.awpLongDecimal BETWEEN (R.rwpLongDecimal - 1.5)
                                    AND (R.rwpLongDecimal + 1.5)
                                )
                            WHERE
                                R.rwpPk = $cenPk
                            GROUP BY
                                W.airPk
                        )
                    ORDER BY
                        A.airName";
    }
    else
    {
        $query = "select * from tblAirspace A order by A.airName";
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

    if ($comEntryRestrict == 'registered')
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
}

echo "<br><br>";
echo "<p>";
echo "<a href='competition_admin.php?comPk=$comPk'>Back to Competition</a>";
echo "</p>";

tpfooter($file);

?>
