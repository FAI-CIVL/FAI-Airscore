<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<div id="vhead"><h1>airScore admin</h1></div>
<?php
require 'authorisation.php';
require 'format.php';
require 'dbextra.php';
adminbar(0);
?>
<p><h2>Competition Administration</h2></p>
<?php

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

$usePk=auth('system');
$link = db_connect();

if (reqexists('add'))
{
    $comname = reqsval('comname');
    $datefrom = reqsval('datefrom');
    $dateto = reqsval('dateto');
    $location = reqsval('location');
    $director = reqsval('director');
    $comptype = reqsval('comptype');
    $comcode = reqsval('code');
    $timeoffset = reqfval('timeoffset');

    if ($comname == '')
    {
        echo "<b>Can't create a competition with no name</b>";    
    }
    else
    {
        $query = "insert into tblCompetition (comName, comLocation, comDateFrom, comDateTo, comMeetDirName, forPk, comType, comCode, comTimeOffset) values ('$comname','$location', '$datefrom', '$dateto', '$director', 0, '$comptype', '$comcode', $timeoffset)";
    
//        $result = mysql_query($query) or die('Competition addition failed: ' . mysql_error());
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Competition addition failed: ' . mysqli_connect_error());
//        $comPk = mysql_insert_id();
		$comPk = mysqli_insert_id($link);

        $regarr = [];
        $regarr['comPk'] = $comPk;
        $regarr['forClass'] = 'gap';
        $regarr['forVersion'] = '2007';
        $regarr['forNomDistance'] = 35.0;
        $regarr['forMinDistance'] = 5.0;
        $regarr['forNomTime'] = 90;
        $regarr['forNomGoal'] = 30.0;
        $regarr['forGoalSSPenalty'] = 1.0;
        $regarr['forLinearDist'] = 0.5;
        $regarr['forDiffDist'] = 3.0;
        $regarr['forDiffRamp'] = 'flexible';
        $regarr['forDiffCalc'] = 'lo';
        $regarr['forDistMeasure'] = 'average';
        if (reqexists('weightstart'))
        {
            $regarr['forWeightStart'] = 0.125;
            $regarr['forWeightArrival'] = 0.175;
            $regarr['forWeightSpeed'] = 0.7;
        }
        $clause = "comPk=$comPk";
        $forPk = insertup($link, 'tblFormula', 'forPk', $clause,  $regarr);

        $query = "update tblCompetition set forPk=$forPk where $clause";
//        $result = mysql_query($query) or die('Competition formula update failed: ' . mysql_error());
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Competition formula update failed: ' . mysqli_connect_error());
		    
        $query = "insert into tblCompAuth values ($usePk, $comPk, 'admin')";
//        $result = mysql_query($query) or die('CompAuth addition failed: ' . mysql_error());
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' CompAuth addition failed: ' . mysqli_connect_error());
    }
}

if (reqexists('update'))
{
    $comPk = reqival('comPk');
    $comname = reqsval('comname');
    $datefrom = reqsval('datefrom');
    $dateto = reqsval('dateto');
    $location = reqsval('location');
    $director = reqsval('director');
    $sanction = reqsval('sanction');
    $formula = reqsval('formula');
    $comptype = reqsval('comptype');
    $comcode = reqsval('code');
    $timeoffset = reqfval('timeoffset');

    check_admin('admin',$usePk,$comPk);

    $query = "update tblCompetition set comName='$comname', comLocation='$comLocation', comDateFrom='$datefrom', comDateTo='$dateto', comDirector='$director', forPk='$formula', comSanction='$sanction', comType='$comptype', comCode='$comcode',  comTimeOffset=$timeoffset where comPk=$comPk";
//    $result = mysql_query($query) or die('Competition update failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Competition update failed: ' . mysqli_connect_error());
}

$comparr = [];
$comparr[] = array ('', fb('Date Range'), fb('Name'), fb('Location'), fb('Director') );

echo "<form action=\"comp_admin.php\" name=\"compadmin\" method=\"post\">";
$count = 1;

if (is_admin('admin', $usePk, -1))
{
    $sql = "SELECT C.* FROM tblCompetition C order by C.comName like '%test%', C.comDateTo desc";
}
else
{
    $sql = "SELECT C.* FROM tblCompAuth A, tblCompetition C where (A.comPk=C.comPk and A.usePk=$usePk) or (C.comName like '%test%') group by C.comName order by C.comName like '%test%', C.comDateTo desc";
}
// $result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql);
// while($row = mysql_fetch_array($result, MYSQL_ASSOC))
while($row = mysqli_fetch_assoc($result))
{
    $id = $row['comPk'];
    $name = $row['comName'];
    $datefrom = substr($row['comDateFrom'], 0, 10);
    $dateto = substr($row['comDateTo'], 0, 10);
    $today = time();
    $fromdate = strtotime($datefrom);
    $todate = strtotime($dateto) + 24*3600;
    if ($today>=$fromdate && $today<=$todate)
    {
        $datestr = fb("$datefrom - $dateto");
    }
    else
    {
        $datestr = "$datefrom - $dateto";
    }
    $location = $row['comLocation'];
    $director = $row['comMeetDirName'];
    $comparr[] = array("$count.", $datestr, "<a href=\"competition.php?comPk=$id\">" . $name . "</a>", $location, $director);
    $count++;
}
echo ftable($comparr, "border=\"0\" cellpadding=\"2\" cellspacing=\"0\" alternate-colours=\"yes\" valign=\"top\" align=\"left\"", array('class="d"', 'class="l"'), '');

echo "<br><hr>";
echo "<h2>Add Competition</h2>";

echo ftable(array(
    array('Name', fin('comname', '', 20), 'Type:', fselect('comptype', 'RACE', array('OLC', 'RACE', 'Free', 'Route', 'Team-RACE'))),
    array('Date From:', fin('datefrom', '', 10), 'Date To:', fin('dateto', '', 10)),
    array('Director:', fin('director', '', 10), 'Location:', fin('location', '', 10)),
    array('Abbreviation:', fin('code', '', 10), 'Time Offset:', fin('timeoffset', '', 7))
    ), '', '', ''
);
echo fis('add', 'Create Competition', '');

echo "</form>";
?>
</div>
</body>
</html>

