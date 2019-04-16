<?php
require 'startup.php';
require_once LIBDIR.'dbextra.php';

// Main Code Begins HERE //

$comPk = intval($_REQUEST['comPk']);
$class = reqsval('class');

$file = __FILE__;
$link = db_connect();
$title = 'AirScore'; # default
$message = '';

if (array_key_exists('addpilot', $_REQUEST))
{
	$pilPk = get_juser();
	$addarr = [];
	$addarr['pilPk'] = $pilPk;
	$addarr['comPk'] = $comPk;
	$clause = "comPk=$comPk and pilPk=$pilPk";
	insertup($link, 'tblRegistration', 'regPk', $clause, $addarr);

// 	$query = "select H.* from tblHandicap H where H.comPk=$comPk and H.pilPk=$pilPk";
// 	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Handicap query failed: ' . mysqli_connect_error());
// 
// 	if (mysqli_num_rows($result) == 0)
// 	{
// 		$query = "insert into tblHandicap (comPk, pilPk, hanHandicap) value ($comPk,$pilPk,1)";
// 		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot handicap insert failed: ' . mysqli_connect_error());
// 	}
	$message .= "You are registered in this competition";
}

if (array_key_exists('delpilot', $_REQUEST))
{
	$pilPk = get_juser();
	$addarr = [];
	$addarr['pilPk'] = $pilPk;
	$addarr['comPk'] = $comPk;
	$clause = "comPk=$comPk AND pilPk=$pilPk";
	
	$query = "DELETE FROM tblRegistration WHERE $clause";
	mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot cancelation from event failed: ' . mysqli_connect_error());
	$message .= "You canceled from this competition.";
}

$query = "	SELECT 
				T.*, 
				F.*, 
				FC.* 
			FROM 
				tblCompetition T 
				JOIN tblForComp FC ON T.comPk = FC.comPk 
				LEFT OUTER JOIN tblFormula F ON FC.forPk = F.forPk 
			WHERE 
				T.comPk = $comPk";
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Comp query failed: ' . mysqli_connect_error());
$row = mysqli_fetch_assoc($result);
if ($row)
{
    $comName = isset($row['comName']) ? $row['comName'] : '';
    $title = 'AirScore - '.isset($row['comName']) ? $row['comName'] : '';
    $comDateFrom = substr(isset($row['comDateFrom']) ? $row['comDateFrom'] : '',0,10);
    $comDateTo = substr(isset($row['comDateTo']) ? $row['comDateTo'] : '',0,10);
    $comPk = $row['comPk'];
    $comOverall = isset($row['comOverallScore']) ? $row['comOverallScore'] : '';
    $comOverallParam = isset($row['comOverallParam']) ? $row['comOverallParam'] : ''; # Discard Parameter, Ex. 75 = 75% eq normal FTV 0.25
    $comDirector = isset($row['comMeetDirName']) ? $row['comMeetDirName'] : '';
    $comLocation = isset($row['comLocation']) ? $row['comLocation'] : '';
    $comFormula = ( isset($row['forClass']) ? $row['forClass'] : '' ) . ' ' . ( isset($row['forVersion']) ? $row['forVersion'] : '' );
    //$forOLCPoints = isset($row['forOLCPoints']) ? $row['forOLCPoints'] : '';
    $comSanction = isset($row['comSanction']) ? $row['comSanction'] : '';
    $comOverall = isset($row['comOverallScore']) ? $row['comOverallScore'] : '';  # Type of scoring discards: FTV, ...
    $comTeamScoring = isset($row['comTeamScoring']) ? $row['comTeamScoring'] : '';
    $comCode = isset($row['comCode']) ? $row['comCode'] : '';
    $comClass = isset($row['comClass']) ? $row['comClass'] : '';
    $comType = isset($row['comType']) ? $row['comType'] : '';
    $forNomGoal = isset($row['forNomGoal']) ? $row['forNomGoal'] : '';
    $forMinDistance = isset($row['forMinDistance']) ? $row['forMinDistance'] : '';
    $forNomDistance = isset($row['forNomDistance']) ? $row['forNomDistance'] : '';
    $forNomTime = isset($row['forNomTime']) ? $row['forNomTime'] : '';
    //$forDiscreteClasses = isset($row['forDiscreteClasses']) ? $row['forDiscreteClasses'] : '';
    
}

#initializing template header
tpinit($link,$file,$row);

if ( isset($message) and $message !== '' )
{
	echo "<h4 style='color:red'>$message</h4>";
}

$embed = reqsval('embed');

$regpilots = [];
$query = "	SELECT 
				P.*, 
				H.hanHandicap 
			FROM 
				tblRegistration R 
				LEFT JOIN tblPilot P on P.pilPk = R.pilPk 
				LEFT OUTER JOIN tblHandicap H ON H.pilPk = P.pilPk 
				AND H.comPk = $comPk 
			WHERE 
				R.comPk = $comPk 
				AND P.pilPk > 0 
			ORDER BY 
				P.pilSex DESC, 
				P.pilLastName DESC";
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Team pilots query failed: ' . mysqli_connect_error());
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $regpilots[] = $row;
}

if (sizeof($regpilots) > 0)
{
    $outreg = [];
    $outreg[] = array("FAI nr.", "Name", "  ", "Glider");
    foreach ($regpilots as $row)
    {
        $pilPk = intval($row['pilPk']);
        #if ($row['hanHandicap'] == '')
        #{
        #    $row['hanHandicap'] = 1;
        #}
        $outreg[] = array($row['pilFAI'], $row['pilFirstName'] . " " . $row['pilLastName'], $row['pilSex'], $row['pilGliderBrand'] . " " . $row['pilGlider']);
        //"<input type=\"text\" name=\"tepModifier$tepPk\" value=\"$tepMod\" size=3>", fbut('submit', 'uppilot', $tepPk, 'up')
    }
    echo "<i>" . sizeof($regpilots) . " pilots registered</i>";
    echo ftable($outreg,'class="regpiltable"','','');
}
else
{
    echo "<i>No pilots registered yet.</i>";
}



tpfooter($file);

?>