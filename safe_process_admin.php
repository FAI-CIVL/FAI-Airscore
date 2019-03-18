<?php

require 'authorisation.php';
require 'template.php';

$comPk = reqival('comPk');
$tasPk = reqival('tasPk');

$usePk = auth('system');
$link = db_connect();
$file = __FILE__;
$header = '';	
$message = '';
$content = '';

# Task Update
if ( reqexists('task') )
{
	$header .= "Task update and tracks verifying process: Task id  ($tasPk)";
	$url = "task_admin.php?tasPk=$tasPk&comPk=$comPk&task=1";
	$content .= "Verifying Tracks with new task setting and adding them to scoring ... <br />";
}
# Bulk Submit
elseif ( reqexists('bulk') )
{
	$header .= "Bulk Track Submission from Zip File: Task id  ($tasPk)";
	$url = "tasktrack_admin.php?tasPk=$tasPk&comPk=$comPk&bulk=1";
	$content .= "Uploading Tracks and adding them to scoring ... <br />";
}
# Xcontest Retrieve
elseif ( reqexists('xcontest') )
{
    $header .= "Bulk Track Submission from XContest: Task id  ($tasPk)";
    $url = "tasktrack_admin.php?tasPk=$tasPk&comPk=$comPk&xcontest=1";
    $content .= "Retrieving Tracks from XContest and adding them to scoring ... <br />";
}
# Complete Task Rescore
elseif ( reqexists('score') )
{
    $header .= "Complete Tracks check and Task rescore: Task id  ($tasPk)";
    $url = "task_result.php?tasPk=$tasPk&comPk=$comPk";
    $content .= "Verifying Tracks and computing results ... <br />";
}

$pid = reqival('pid');
$starttime = reqival('time');

if ( !script_isRunning($pid) ) 
{
	redirect("$url");
}

$time = microtime(true);
$elapsedtime = secondsToTime($time - $starttime);
$content .= "Process ID $pid still working ... <br />";
$content .= "It could take some time depending on task length and pilots number ... <br />";
$content .= "Elapsed time: $elapsedtime seconds <br />";
$content .= "You'll be redirected to results as it finishes its job. <br />";

//initializing template header
tpadmin($link,$file);

echo "<h4>$header</h4>";
echo "<hr />";
echo $content;

echo "<br /><hr />
		<a href='tasktrack_admin.php?tasPk=$tasPk&comPk=$comPk'>Back to Tracks Management</a><br />";
echo "<hr />";		
echo "<a href='task_admin.php?tasPk=$tasPk&comPk=$comPk'>Back to Task Administration</a><br />";

tpfooter($file);

?>
