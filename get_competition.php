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
$query = "select comName from tblCompetition where comPk=$comPk";
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task add failed: ' . mysqli_connect_error());
$comName = mysqli_result($result,0);

$forPk = 0;
$ctype = '';
$sql = "SELECT T.* FROM tblCompetition T where T.comPk=$comPk";
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
$sql = "select U.*, A.* FROM tblCompAuth A, tblUser U where U.usePk=A.usePk and A.comPk=$comPk";
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
    $sql = "SELECT F.* FROM tblFormula F where F.comPk=$comPk";
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
$sql = "SELECT T.*, traPk as Tadded FROM tblTask T left outer join tblComTaskTrack CTT on CTT.tasPk=T.tasPk where T.comPk=$comPk group by T.tasPk order by T.tasDate";
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

$sql = "SELECT T.* FROM tblCompetition C, tblTask T where T.comPk=C.comPk and C.comPk=$comPk order by T.tasPk limit 1";
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

