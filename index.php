<?php

require 'authorisation.php';
require 'template.php';
require 'format.php';

function gettodayseason()
{
	$today = date('md');
	$season = date('Y');
	if ( $today > 1031 )
	{
		$season++;
	}
	return $season;
}

function getseasoninfo($link, $season)
{
	$seasonstart = date(($season-1).'-11-01');
	//echo 'inizio stagione: '.$seasonstart;
	$seasonend = date(($season).'-10-31');
	//echo 'fine stagione: '.$seasonend;
	$today = date('Y-m-d');

	$sql = "SELECT	COUNT(comPk) AS comNum, 
					(SELECT COUNT(comPk) FROM tblCompetition WHERE (comDatefrom > '$seasonstart' AND comDateTo < '$today') ) AS pastCom, 
					(SELECT COUNT(comPk) FROM tblCompetition WHERE (comDatefrom > '$today' AND comDateTo < '$seasonend') ) AS nextCom, 
					(SELECT COUNT(comPk) FROM tblCompetition WHERE (comDatefrom > '$seasonstart' AND ('$today' BETWEEN comDatefrom AND comDateTo) AND comDateTo < '$seasonend') ) AS openCom 
					FROM tblCompetition 
					WHERE (comDateFrom BETWEEN '$seasonstart' AND '$seasonend')";
	//$sql = "select * from tblCompetition where comDateTo > date_sub(now(), interval 1 day) order by comDateTo";
	//echo 'sql = '.$sql;
	$result = mysqli_query($link, $sql);
	$row = mysqli_fetch_array($result, MYSQLI_BOTH);

	return $row;	
}


function getcomplist($link, $season, $list=0)
{
	$seasonstart = date(($season-1).'-11-01');
	//echo 'inizio stagione: '.$seasonstart;
	$seasonend = date(($season).'-10-31');
	//echo 'fine stagione: '.$seasonend;
	$today = date('Y-m-d');
	$complist = [];
	$complist[] = array("Competition", "Period" );
	
	$sql = "select * from tblCompetition where (comDateFrom between '$seasonstart' and '$seasonend') order by comDateFrom Desc";
	//$sql = "select * from tblCompetition where comDateTo > date_sub(now(), interval 1 day) order by comDateTo";
	//echo 'sql = '.$sql;
	$result = mysqli_query($link, $sql);
	while ( $row = mysqli_fetch_array($result, MYSQLI_BOTH) )
	{
		// FIX: if not finished & no tracks then submit_track page ..
		// FIX: if finished no tracks don't list!
		$cpk = $row['comPk'];
		$datefrom = date_format( date_create($row['comDateFrom']), 'd-m-Y ' );
		$dateto = date_format( date_create($row['comDateTo']), 'd-m-Y ' );
		//$comps[] = "<span class=\"list\"><a href=\"comp_result.php?comPk=$cpk\">" . $row['comName'] . "</span></a>";
		$complist[] = array("<a href=\"comp_result.php?comPk=$cpk\">" . $row['comName'] . "</a>", $datefrom." - ".$dateto );
	}
	return $complist;
	
}

//
//       Main Code Begins HERE       //
//

$link = db_connect();
$list = isset($_REQUEST['list']) ? $_REQUEST['list'] : null;
$season = isset($_REQUEST['season']) ? $_REQUEST['season'] : gettodayseason();

$file = __FILE__;

$page = 'LP AirScore';
$title = 'AirScore - Online Scoring Tool';

$row = getseasoninfo($link,$season);

//initializing template header
tpinit($link,$file,$row);

// if ( $season = gettodayseason() )
// {
// 	$period = [];
// 	$period[] = array(fb("<a href=\"index.php?season=$season&list=past\">Closed</a>"), fb("<a href=\"index.php?season=$season&list=now\">Running</a>"), fb("<a href=\"index.php?season=$season&list=next\">Next</a>") );
// 	echo ftable($period,'', '', '');
// }

echo ftable( getcomplist($link, $season, $list),'', '', '');

tpfooter($file);

?>
