<?php

require 'authorisation.php';
require 'template.php';
require 'format.php';

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
	//echo 'sql = '.$sql;
	$result = mysqli_query($link, $sql);
	$row = mysqli_fetch_assoc($result);

	return $row;	
}


function getladderlist($link, $season)
{
	$seasonstart = date(($season-1).'-11-01');
	$seasonend = date(($season).'-10-31');
	$today = date('Y-m-d');
	$ladderlist = [];
	$ladderlist[] = array("League", "Class", "Nation" );
	
	$sql = "SELECT 
				L.ladPk AS id, 
				L.*, 
				LS.* 
			FROM 
				tblLadder L 
				JOIN tblLadderSeason LS ON L.ladPk = LS.ladPk AND LS.seasonYear = $season 
			ORDER BY 
				ladComClass ASC, 
				ladName";
	$result = mysqli_query($link, $sql);
	while ( $row = mysqli_fetch_array($result, MYSQLI_BOTH) )
	{
		// FIX: if not finished & no tracks then submit_track page ..
		// FIX: if finished no tracks don't list!
		$ladpk = $row['ladPk'];
		$name = $row['ladName'];
		$nat = get_countrycode($link, $row['ladNationCode']);
		$class = $row['ladComClass'];
		$today = new DateTime('now');
		
		# Get class image
		$image = strtolower($class) . '.png';

		$ladderlist[] = array("<a href=\"ladder_result.php?ladPk=$ladpk&season=$season\">$name</a>", "<img src='./images/$image' alt='$class' class='compclass'>", "$nat" );

	}
	return $ladderlist;
	
}

//
//       Main Code Begins HERE       //
//

$link = db_connect();
$list = isset($_REQUEST['list']) ? $_REQUEST['list'] : null;
$season = isset($_REQUEST['season']) ? $_REQUEST['season'] : getseason(date('Ymd'));

$file = __FILE__;

$page = 'LP AirScore';
$title = 'AirScore - League Classifications for $season';

# Season selector
$stable = [];
$stable[] = array("Season: ", fselect('season', $season, season_array($link), " onchange=\"document.getElementById('main').submit();\"") );

$row = getseasoninfo($link,$season);

//initializing template header
tpinit($link,$file,$row);

echo "<form enctype='multipart/form-data' action=\"league.php\" name='main' id='main' method='post'>\n";
echo ftable($stable,"class='selector'", '', '');
echo "</form>\n";
echo "<hr />\n";
echo ftable( getladderlist($link, $season),"class='format ladderlist'", '', '');

tpfooter($file);

?>
