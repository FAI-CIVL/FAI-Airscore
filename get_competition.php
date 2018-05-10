<?php
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Content-type: application/json');

require 'authorisation.php';
require 'hc.php';
require 'format.php';
require 'xcdb.php';
require 'authorisation.php';
require 'format.php';
require 'dbextra.php';

$comPk = reqival('comPk');
adminbar($comPk);

$usePk = auth('system');
$link = db_connect();
$query = "SELECT comName FROM tblCompetition WHERE comPk = $comPk";
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task add failed: ' . mysqli_connect_error());
$comName = mysqli_result($result,0);

$forPk = 0;
$ctype = '';
$sql = "SELECT 
			T.*, 
			FC.* 
		FROM 
			tblCompetition T 
			LEFT JOIN tblForComp FC USING (comPk) 
		WHERE 
			T.comPk = $comPk";
$result = mysqli_query($link, $sql);
$row = mysqli_fetch_array($result, MYSQLI_BOTH);
$competition = [];
if ($row)
{
    $competition = $row;
    //$cdfrom = substr($row['comDateFrom'],0,10);
    //$cdto = substr($row['comDateTo'],0,10);
}


// Administrators 
$sql = "SELECT 
			U.*, 
			A.* 
		FROM 
			tblCompAuth A 
			LEFT JOIN tblUser U USING (usePk) 
		WHERE 
			A.comPk = $comPk";
$result = mysqli_query($link, $sql);
$admin = [];
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $admin[] = $row['useLogin'];
}

// Formula
$version = 0;
$has_formula = array('RACE', 'Team-RACE', 'Route', 'RACE-handicap');
$formula = [];

if (in_array($ctype, $has_formula))
{
    $sql = "SELECT 
				F.*, 
				FC.*
			FROM 
				tblFormula F 
				LEFT OUTER JOIN tblForComp FC USING (forPk) 
			where 
				FC.comPk = $comPk";
    $result = mysqli_query($link, $sql);
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    if ($row)
    {
        $formula = $row;
    }
}


if (in_array($ctype, $has_formula))
{
// Tasks
$count = 1;
$sql = "SELECT 
			T.*, 
			traPk AS Tadded 
		FROM 
			tblTask T 
			LEFT OUTER JOIN tblComTaskTrack CTT USING (tasPk) 
		WHERE 
			T.comPk = $comPk 
		GROUP BY 
			T.tasPk 
		ORDER BY 
			T.tasDate";
$result = mysqli_query($link, $sql);

$comp_tasks = [];
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $comp_tasks[] = $row;
}

$sql = "SELECT * FROM tblRegion R";
$result = mysqli_query($link, $sql);
$regions = [];
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $regPk = $row['regPk'];
    $regDesc = $row['regDescription'];
    $regions[$regDesc] = $regPk;
}

$sql = "SELECT 
			T.* 
		FROM 
			tblCompetition C, 
			tblTask T 
		WHERE 
			T.comPk = C.comPk 
			AND C.comPk = $comPk 
		ORDER BY 
			T.tasPk 
		LIMIT 
			1";
$result = mysqli_query($link, $sql);
$defregion = '';
if (mysqli_num_rows($result) > 0)
{
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    $defregion = $row['regPk'];
}


$depdef = 'on';

$data = [ 'competition' => $competition, 'formula' => $formula, 'tasks' => $comp_tasks ];
print json_encode($data);
}
?>

