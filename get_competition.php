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
$result = mysql_query($query) or die('Task add failed: ' . mysql_error());
$comName = mysql_result($result,0);

$forPk = 0;
$ctype = '';
$sql = "SELECT T.* FROM tblCompetition T where T.comPk=$comPk";
$result = mysql_query($sql,$link);
$row = mysql_fetch_array($result);
$competition = [];
if ($row)
{
    $competition = $row;
    //$cdfrom = substr($row['comDateFrom'],0,10);
    //$cdto = substr($row['comDateTo'],0,10);
}


// Administrators 
$sql = "select U.*, A.* FROM tblCompAuth A, tblUser U where U.usePk=A.usePk and A.comPk=$comPk";
$result = mysql_query($sql,$link);
$admin = [];
while ($row = mysql_fetch_array($result))
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
    $result = mysql_query($sql,$link);
    $row = mysql_fetch_array($result);
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
$result = mysql_query($sql,$link);

$comp_tasks = [];
while($row = mysql_fetch_array($result))
{
    $comp_tasks[] = $row;
}

$sql = "SELECT * FROM tblRegion R";
$result = mysql_query($sql,$link);
$regions = [];
while ($row = mysql_fetch_array($result))
{
    $regPk = $row['regPk'];
    $regDesc = $row['regDescription'];
    $regions[$regDesc] = $regPk;
}

$sql = "SELECT T.* FROM tblCompetition C, tblTask T where T.comPk=C.comPk and C.comPk=$comPk order by T.tasPk limit 1";
$result = mysql_query($sql,$link);
$defregion = '';
if (mysql_num_rows($result) > 0)
{
    $row = mysql_fetch_array($result);
    $defregion = $row['regPk'];
}


$depdef = 'on';

$data = [ 'competition' => $competition, 'formula' => $formula, 'tasks' => $comp_tasks ];
print json_encode($data);
}
?>

