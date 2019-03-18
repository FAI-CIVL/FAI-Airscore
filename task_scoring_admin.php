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

if ( reqexists('pid') )
{

	$pid = reqival('pid');
	$type = reqsval('type');
	if ( $type == 'score' )
		{
			$url = "task_result.php?tasPk=$tasPk&comPk=$comPk";
		}
	elseif ( $type == 'update' )
		{
			$url = "task_admin.php?tasPk=$tasPk&comPk=$comPk&updated";
		}

	if ( !script_isRunning($pid) ) 
	{
		redirect("$url");
	}
	
	$header .= "Full Task Rescore: Task id  ($tasPk)";
	$starttime = reqival('time');
	#$page = $_SERVER['REQUEST_URI'];
	$sec = "10";
	$time = microtime(true);
	$elapsedtime = secondsToTime($time - $starttime);
	$content .= "Task Full Scoring ... <br />";
	$content .= "Process ID $pid still working ... <br />";
	$content .= "It could take some time depending on task length and pilots number ... <br />";
	$content .= "Elapsed time: $elapsedtime seconds <br />";
	$content .= "You'll be redirected to results as it finishes its job. <br />";
}

//initializing template header
tpadmin($link,$file);

echo "<h4>$header</h4>";
echo "<hr />";
echo $content;

tpfooter($file);

?>
