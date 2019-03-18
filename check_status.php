<?php

require_once 'authorisation.php';
require_once 'format.php';
require_once 'dbextra.php';
require 'template.php';

function find_track($link, $tasPk, $pilPk)
{
	$traPk = 0;
	$sql = "SELECT 
			TR.traPk 
		FROM 
			tblTrack T 
			JOIN tblTaskResult TR on T.traPk = TR.traPk 
		WHERE 
			tasPk = $tasPk 
			AND pilPk = $pilPk 
		LIMIT 
			1";
	$result = mysqli_query($link, $sql);
	if (mysqli_num_rows($result) > 0)
	{
		$traPk = mysqli_fetch_object($result)->traPk;
		//var_dump($traPk);
	}
	return $traPk;
}

function get_open_tasks($link, $comp, $pilPk)
{
	$comPk = $comp['comPk'];
	$restrict = $comp['comEntryRestrict'];
	$ftable = [];
	# Check if comp needs registration
	$permission = 1;
	if ($restrict == 'registered')
	{
		# Check if pilot is registered
		$sql = "SELECT * FROM tblRegistration WHERE comPk=$compK and pilPk=$pilPk LIMIT 1";
		$result = mysqli_query($link, $sql);
		if (mysqli_num_rows($result) == 0)
		{
			$permission = 0;
		}
	}
	if ( $permission = 0 )
	{
		$ftable[] = array("You are not registered in this Competition",'','','');
	}
	else
	{
		# Get list of open tasks
		$sql = "SELECT 
					T.* 
				FROM 
					tblTask T 
				WHERE 
					tasDate BETWEEN CURDATE() - INTERVAL 2 DAY 
					AND CURDATE() 
					AND comPk = $comPk 
				ORDER BY 
					tasDate ASC";
		$result = mysqli_query($link, $sql);

		# Check if we have any open task
		if (mysqli_num_rows($result) > 0)
		{
			$opentasks = mysqli_num_rows($result);
			$ftable[] = array("We found $opentasks open tasks:",'','','');
			while ( $row = mysqli_fetch_array($result, MYSQLI_BOTH) )
			{
				$tasPk = $row['tasPk'];
				$tasName = $row['tasName'];
				$date = date_format( date_create($row['tasDate']), 'd-m-Y ' );
				//$ftable[] = array("$tasName | $date :",'','','');
				# Check if pilot has already a valid track for the task
				$traPk = find_track($link, $tasPk, $pilPk);
				if ( $traPk > 0)
				{
					$ftable[] = array("$tasName | $date :","<a href='check_status.php?traPk=$traPk'>Track already sent</a>",'','');
				}
				else
				{
					$ftable[] = array("$tasName | $date :", "<form enctype=\"multipart/form-data\" action=\"submit_track.php?comPk=$comPk&tasPk=$tasPk&pilPk=$pilPk\" method=\"post\" name=\"task-$tasPk\" id=\"task-$tasPk\">", "<input type=\"file\" name=\"userfile\">", " " . fis('addtrack', 'Add Track', 10) . "</form>");
				}
			}
		}
	}
	//echo ftable($ftable,'class=submit-track', '', '');
	return $ftable;
}

function get_comp_details($link, $comPk, $pilPk)
{
	$sql = "SELECT 
				C.comName, 
				DATE_FORMAT(C.comDateFrom, '%Y/%m/%d') AS dateFrom, 
				DATE_FORMAT(C.comDateTo, '%Y/%m/%d') AS dateTo, 
				R.regPk 
			FROM 
				tblCompetition C 
				LEFT OUTER JOIN tblRegistration R on R.comPk = C.comPk 
				AND R.pilPk = $pilPk 
			WHERE 
				C.comPk = $comPk 
			LIMIT 
				1";
	$result = mysqli_query($link, $sql);
	//echo $sql . "\n";
	//print_r ($result);
	$row = mysqli_fetch_assoc($result);
	//print_r ($row);
	$comname = $row['comName'];
	$datefrom = $row['dateFrom'];
	$dateto = $row['dateTo'];
	//echo $comname . ' - ' . mysqli_fetch_object($result)->regPk . '\n';
	//echo $datefrom . ' - ' . $dateto . '\n';
	$registered = isset($row['regPk']) ? 1 : 0;
	$ctable[] = array("<strong>$comname<strong>", "$datefrom", ' - ', "$dateto");
	if ( $registered )
	{
		$ctable[] = array("You are registered in this event", '', '', '');
	}
	else
	{
		$ctable[] = array("<a href='registered_pilots.php?comPk=$comPk'><strong>REGISTER</strong></a>", '', '', '');
	}

	$ctable[] = array("<hr />",'','','');
	
	return $ctable;
}

function get_track_result($link, $traPk)
{
    # Get track provisional results
    $ftable = [];
    $sql = "SELECT 
				TR.tarGoal AS Goal, 
				(TR.tarDistance / 1000) AS Dist, 
				TR.tarES AS TimeES, 
				TR.tarSS AS TimeSS, 
				TR.tasPk, 
				T.comPk, 
                T.tasName, 
                T.tasDate, 
                C.comName 
			FROM 
				tblTaskResult TR 
				JOIN tblTask T on TR.tasPk = T.tasPk 
                JOIN tblCompetition C ON C.comPk = T.comPk 
			WHERE 
				traPk = $traPk";
	$result = mysqli_query($link, $sql);
	$row = mysqli_fetch_array($result, MYSQLI_BOTH);
	$tasPk = $row['tasPk'];
	$comPk = $row['comPk'];
	$name = $row['comName'] . ' ' . $row['tasName'];
	$date = $row['tasDate'];
	$dist = round($row['Dist'], 2);
	$goal = $row['Goal'] > 0 ? 'Yes' : 'No';
	$time = '';
	if ( $goal == 'Yes' )
	{
		$t = $row['TimeES'] - $row{'TimeSS'};
		$hh = floor($t / 3600);
        $mm = floor(($t % 3600) / 60);
        $ss = $t % 60;
        $time = sprintf("%02d:%02d:%02d", $hh,$mm,$ss);
	}
	$ftable[] = array($name, '', $date,'');
	$ftable[] = array("Distance: ", $dist,'','');
	$ftable[] = array("Goal: ", $goal,'','');
	$ftable[] = array("Time: ", $time,'','');
	$ftable[] = array("Track: ", "<a href='tracklog_map.php?trackid=$traPk&tasPk=$tasPk&comPk=$comPk&ok=1'>link</a>",'','');
	return $ftable;
}

// Main Code Begins HERE //

$comPk = intval($_REQUEST['comPk']);
$traPk = reqival('traPk');
$class = reqsval('class');

$file = __FILE__;
$link = db_connect();
$title = 'AirScore'; # default
$message = '';
$table = [];

# Get pilot ID or redirect to login
$pilPk = get_juser();

# We look for track results query
if ( $traPk !== 0 )
{
	# Write task result
    $out = get_track_result($link, $traPk);
	foreach ( $out as $line)
	{
		$table[] = $line;
	}
	$table[] = array("<a href='check_status.php'>BACK</a>",'','','');
}
# Otherwise we look for open tasks and next comps
else
{
	# Get list of open comps (usually just one but... )
	$sql = "SELECT 
				DISTINCT C.comPk,
				C.* 
			FROM 
				tblTask T 
				JOIN tblCompetition C ON T.comPk = C.comPk 
			WHERE 
				tasDate BETWEEN CURDATE() - INTERVAL 2 DAY 
				AND CURDATE() 
			ORDER BY 
				tasDate DESC";
	$result = mysqli_query($link, $sql);

	# Check if we have any open comp
	if ( mysqli_num_rows($result) > 0 )
	{
		while ( $row = mysqli_fetch_array($result, MYSQLI_BOTH) )
		{
			$comname = $row['comName'];
			$table[] = array("<strong>$comname<strong>",'','','');
		
			$out = get_open_tasks($link, $row, $pilPk);
		
			foreach ( $out as $line)
			{
				$table[] = $line;
			}
			$table[] = array("<hr />",'','','');
		}
	}
	else
	{
		$message .= "We do not have any open task at the moment.<br />\n";
	}
	
	# Check if there are defined future comps
	$sql = "SELECT 
				DISTINCT C.comPk 
			FROM 
				tblCompetition C  
			WHERE 
				C.comDateFrom BETWEEN CURDATE() 
				AND CURDATE() + INTERVAL 30 DAY
			ORDER BY 
				C.comDateFrom ASC";
	$result = mysqli_query($link, $sql);
	if ( mysqli_num_rows($result) > 0 )
	{
		$num = mysqli_num_rows($result);
		$table[] = array("<hr />",'','','');
		$table[] = array("Next Events:", $num,'','');
		while ( $row = mysqli_fetch_array($result, MYSQLI_BOTH) )
		{			
			$comPk = $row['comPk'];
			$out = get_comp_details($link, $comPk, $pilPk);		
			foreach ( $out as $line)
			{
				$table[] = $line;
			}
			$table[] = array("<hr />",'','','');
		}
	}
	else
	{
		$message .= "We do not have any defined event in the next 2 months.<br />\n";
	}
	
}

# initializing template header
tpinit($link,$file,$row);

if ( isset($message) and $message !== '' )
{
	echo "<h4 style='color:red'>$message</h4>";
}

echo "<p>\n";
echo ftable($table,'class=submit-track', '', '');
echo "</p>\n";


tpfooter($file);

?>