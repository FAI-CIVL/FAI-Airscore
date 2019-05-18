<?php
require 'admin_startup.php';
require LIBDIR.'track_ops.php';

function get_registered_pilots($link, $comPk, $tasPk)
{
    # query to get all registered pilots for Comp, and data of available tracks for the Task
    $query = "  SELECT
                    P.`pilFirstName`,
                    P.`pilLastName`,
                    P.`pilPk`,
                    TT.`traPk`,
                    TT.`tarResultType`,
                    TT.`Goal`,
                    TT.`Dist`,
                    TT.`TimeSS`,
                    TT.`TimeES`
                FROM
                    `tblRegistration` R
                JOIN tblPilot P USING(`pilPk`)
                LEFT OUTER JOIN(
                    SELECT `pilPk`,
                        `traPk`,
                        `tarResultType`,
                        `tarGoal` AS Goal,
                        (`tarDistance` / 1000) AS Dist,
                        `tarES` AS TimeES,
                        `tarSS` AS TimeSS
                    FROM
                        `tblResultView`
                    WHERE
                        `tasPk` = $tasPk
                ) AS TT USING(`pilPk`)
                WHERE
                    R.`comPk` = $comPk
                ORDER BY
                    P.`pilLastName` ASC,
                    P.`pilFirstName` ASC";

    $result = mysqli_query($link, $query);

    return $result;
}

// Main Code Begins HERE //

$comPk = reqival('comPk');
$tasPk = reqival('tasPk');
$file = __FILE__;
$usePk = auth('system');
$link = db_connect();
$message = '';
$content = '';

# We check if there is a uploaded track
if ( reqexists('addtrack') )
{
    $fh = fopen("/tmp/submit24", "w");
    foreach ($_REQUEST as $k=>$v)
    {
        fwrite($fh, "key=$k, value=$v\n");
    }
    foreach ($_FILES as $k=>$v)
    {
        fwrite($fh, "key=$k:\n");
        foreach ($v as $key=>$val)
        {
            fwrite($fh, "    key=$key, value=$val\n");
        }
    }
    fclose($fh);
    $pilPk = reqival('pilPk');
    $traPk = accept_track($link, $pilPk, $comPk, $tasPk);
    # check if we have a track or an error
    if ( is_int($traPk) && $traPk > 0 )
    {
        $message .= "Track accepted. <br /> \n";
    }
    else
    {
        $message .= "Error processing track <br /> \n";
    }
}
elseif (array_key_exists('delete', $_REQUEST))
{
    $pilPk = reqival('pilPk');
    $traPk = reqival('traPk');

    # Check if I am admin for the Comp
    if (!check_admin('admin', $usePk, $comPk))
    {
        $message .= "You cannot delete tracks for that competition (ID = $comPk) <br /> \n";
    }
    else
    {
        $query = "delete from tblTaskResult where traPk=$traPk";
        mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' TaskResult delete failed: ' . mysqli_connect_error());

        $query = "delete from tblTrack where traPk=$traPk";
        mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Track delete failed: ' . mysqli_connect_error());

        $query = "delete from tblTrackLog where traPk=$traPk";
        mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Tracklog delete failed: ' . mysqli_connect_error());

        $query = "delete from tblWaypoint where traPk=$traPk";
        mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Waypoint delete failed: ' . mysqli_connect_error());

        $query = "delete from tblBucket where traPk=$traPk";
        mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Bucket delete failed: ' . mysqli_connect_error());

        $query = "delete from tblComTaskTrack where traPk=$traPk";
        mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' ComTaskTrack delete failed: ' . mysqli_connect_error());

        $message .= "Track succesfully deleted (ID = $traPk) <br /> \n";
    }
}
elseif ( array_key_exists('setdnf', $_REQUEST) )
{
    $pilPk = reqival('pilPk');
    set_status($link, $pilPk, $comPk, $tasPk, 'dnf');
}
elseif ( array_key_exists('setabs', $_REQUEST) )
{
    $pilPk = reqival('pilPk');
    set_status($link, $pilPk, $comPk, $tasPk, 'abs');
}
elseif ( array_key_exists('mindist', $_REQUEST) )
{
    $pilPk = reqival('pilPk');
    set_status($link, $pilPk, $comPk, $tasPk, 'mindist');
}
elseif (addslashes($_REQUEST['foo']) == 'Send Tracklog')
{
    $tempnm = $_FILES['userfile']['tmp_name'];
    $out = '';
    $retv = 0;
    $command = "python3 " . BINDIR . "bulk_igc_reader.py $tasPk $tempnm > " . BINDIR . 'log/bulk_out.txt 2>&1 & echo $!; ';
    $pid = exec($command, $out, $retv);
    $ptime = microtime(true);
    sleep(15);
    redirect("safe_process_admin.php?tasPk=$tasPk&comPk=$comPk&pid=$pid&time=$ptime&bulk=1");
}
elseif ( reqexists('getxcontest') )
{
    $out = '';
    $retv = 0;
    # Check Task has been setup correctly
    if ( task_set($link, $tasPk) )
    {
        $command = "python3 " . BINDIR . "get_igc_from_xcontest.py $comPk $tasPk test > " . BINDIR . 'log/xcontest.txt 2>&1 & echo $!; ';
        $pid = exec($command, $out, $retv);
        $ptime = microtime(true);
        sleep(5);
        redirect("safe_process_admin.php?tasPk=$tasPk&comPk=$comPk&pid=$pid&time=$ptime&xcontest=1");
    }
    else
    {
        $message .= "Task ID = $tasPk is not properly set, please correct waypoints and retry. \n";
    }
}
elseif ( array_key_exists('bulk', $_REQUEST) )
{
    $message .= "Tracks Bulk Submission finished. \n";

    # Define which lines of output file we are interested in
    $alreadyscored = "already scored";
    $notfound = "in database";
    $found = "Found:";
    $scored = "Stored track";

    $matches = array();

    # Reads the output file
    $handle = @fopen(BINDIR . "log/bulk_out.txt", "r");
    if ( $handle )
    {
        while ( !feof($handle) )
        {
            $buffer = fgets($handle);

            # Log success
            if ( (strpos($buffer, $found) !== FALSE) || (strpos($buffer, $scored) !== FALSE) )
            {
                $matches[] = $buffer;
            }
            # Log failure
            elseif ( (strpos($buffer, $notfound) !== FALSE) || (strpos($buffer, $alreadyscored) !== FALSE) )
            {
                $matches[] = "<span style='color:red'> $buffer </span>";
            }
        }
        fclose($handle);
    }

    # Show results
    $content .= "<p class=\'bulk_script\'>\n";
    foreach ($matches as $txt)
    {
        $content .= "$txt <br />\n";
    }
    $content .= "</p>\n";
}
elseif ( array_key_exists('xcontest', $_REQUEST) )
{
    $message .= "Tracks retrieval from XContest finished. \n";

    # Define which lines of output file we are interested in
    $notfound = "No relevant";
    $found = "found pilot:";
    $scored = "submitted track";

    $matches = array();

    # Reads the output file
    $handle = @fopen(BINDIR . "log/xcontest.txt", "r");
    if ( $handle )
    {
        while ( !feof($handle) )
        {
            $buffer = fgets($handle);

            # Log success
            if ( (strpos($buffer, $found) !== FALSE) || (strpos($buffer, $scored) !== FALSE) )
            {
                $matches[] = $buffer;
            }
            # Log failure
            elseif ( (strpos($buffer, $notfound) !== FALSE) )
            {
                $matches[] = "<span style='color:red'> $buffer </span>";
            }
        }
        fclose($handle);
    }

    # Show results
    $content .= "<p class=\'bulk_script\'>\n";
    foreach ($matches as $txt)
    {
        $content .= "$txt <br />\n";
    }
    $content .= "</p>\n";

}



# Get registered pilots for the task
$result = get_registered_pilots($link, $comPk, $tasPk);

# Check if we have registered pilots
if ( mysqli_num_rows($result) == 0 )
{
    $message .= "There are no registered pilots for this Comp <br /> \n";
}
else
{
    # Create Tables
    $dtable = [];
    $btable = [];
    $xtable = [];

    $dtable[] = array("There are " . mysqli_num_rows($result) . " pilots registered.", '', '', '', '', '');
    $dtable[] = array("<strong>NAME</strong>", "<strong>STATUS</strong>", "<strong>RESULT</strong>", '');
    while ( $row = mysqli_fetch_assoc($result) )
    {
        $pilPk = $row['pilPk'];
        $name = $row['pilFirstName'] . " " . $row['pilLastName'] . " " . $pilPk;
        $traPk = isset($row['traPk']) ? $row['traPk'] : 0;

        #check if pilot already has a valid track or status
        if ( $traPk == 0 )
        {
            $dtable[] = array($name, "<form enctype=\"multipart/form-data\" action=\"tasktrack_admin.php?comPk=$comPk&tasPk=$tasPk&pilPk=$pilPk\" method=\"post\" name=\"task-$tasPk\" id=\"task-$tasPk\"> NYP", "<input type=\"file\" name=\"userfile\">", " " . fis('addtrack', 'Add Track', 10), " " . fis('setdnf', 'Set DNF', 10), " " . fis('mindist', 'Set Min Dist', 10) . " " . fis('setabs', 'Set ABS', 10) ."</form>");
        }
        else
        {
            $dist = round($row['Dist'], 2);
            $goal = $row['Goal'] > 0 ? 'Yes' : 'No';
            $resulttype = $row['tarResultType'];
            $time = '';
            if ( $goal == 'Yes' )
            {
                $t = $row['TimeES'] - $row{'TimeSS'};
                $hh = floor($t / 3600);
                $mm = floor(($t % 3600) / 60);
                $ss = $t % 60;
                $time = sprintf("%02d:%02d:%02d", $hh,$mm,$ss);
                $status = "Collected";
                $info = "GOAL: $time";
            }
            elseif ( $resulttype == 'abs' )
            {
                $status = "Set";
                $info = "ABS";
            }
            elseif ( $resulttype == 'dnf' )
            {
                $status = "Set";
                $info = "DNF";
            }
            else
            {
                $status = "Collected";
                $info = "OUT: $dist Km";
            }
            $dtable[] = array($name, $status, $info, "<a href='/tracklog_map.php?trackid=$traPk&tasPk=$tasPk&comPk=$comPk&ok=1'>link</a>", "<form enctype=\"multipart/form-data\" action=\"tasktrack_admin.php?comPk=$comPk&tasPk=$tasPk&pilPk=$pilPk&traPk=$traPk\" method=\"post\" name=\"task-$tasPk\" id=\"task-$tasPk\">" . fis('delete', 'DELETE', 10) ."</form>", '');
        }

    }

    # Create Bulk IGC ZIP Submit
    $btable[] = array(" <form enctype=\"multipart/form-data\" action=\"tasktrack_admin.php?tasPk=$tasPk&comPk=$comPk\" method=\"post\">
                            <input type=\"hidden\" name=\"MAX_FILE_SIZE\" value=\"1000000000\">",
                            "<input name=\"userfile\" type=\"file\">",  "<input type=\"submit\" name=\"foo\" value=\"Send Tracklog\"></form>");

    # Create XContest Tracks Submit
    $xtable[] = array(" <form action=\"tasktrack_admin.php?tasPk=$tasPk&comPk=$comPk\" name=\"xcontest\" method=\"post\"> \n".
                            fbut('submit', 'getxcontest', $tasPk, 'Get Tracks fron XContest').
                            "\n</form>\n");
}


//initializing template header
$query = "SELECT C.*, T.* FROM `tblCompetition` C JOIN `tblTask` T USING(`comPk`) where `tasPk`=$tasPk";
$result = mysqli_query($link, $query);
$row = mysqli_fetch_assoc($result);
$taskname = $row['tasName'];

tpadmin($link, $file, $row);

echo "<h3> $taskname </h3>" . PHP_EOL;
echo "<h4> Tracks Management </h4>" . PHP_EOL;
if ( $message !== '')
{
    echo "<h4> <span style='color:red'>$message</span> </h4>" . PHP_EOL;
    echo "<br />" . PHP_EOL;
    echo "<hr />" . PHP_EOL;
}
if ( $content !== '')
{
    echo "$content" . PHP_EOL;
    echo "<br />" . PHP_EOL;
    echo "<hr />" . PHP_EOL;
}


echo "<br />" . PHP_EOL;
echo "<hr />" . PHP_EOL;
echo ftable($dtable,'class=regdtable', '', '');
echo "<br />" . PHP_EOL;
echo "<hr />" . PHP_EOL;

echo "<h4>BULK TRACKLOGS UPLOAD</h4>";
echo "<p class='explanation'>Should be a zip file containing multiple tracks (in top directory) named: <br>
        FAINum.igc ;<br />
        LASZO_OKROS.20180428-090816.13084.164.igc ;<br />
        LiveTrack ALAIN WOEFFRAY.115210.20180427-114009.20353.101.igc</p>";
echo ftable($btable,'class=regdtable', '', '');
echo "<br />" . PHP_EOL;
echo "<hr />" . PHP_EOL;

echo "<h4>GET TRACKS FROM XCONTEST</h4>";
echo "<p class='explanation'>Try to get missing Tracks from XContest, for pilots who gave their XContest Username</p><br />";
echo ftable($xtable,'class=regdtable', '', '');
echo "<br />" . PHP_EOL;
echo "<hr />" . PHP_EOL;
echo "<a href='task_admin.php?tasPk=$tasPk&comPk=$comPk'>Back to Task Administration</a><br />";

tpfooter($file);

?>
