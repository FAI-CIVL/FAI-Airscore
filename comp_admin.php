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
adminbar(0);
?>
<p><h2>Competition Administration</h2></p>
<?php

$usePk=auth('system');
$link = db_connect();

if (array_key_exists('add', $_REQUEST))
{
    $comname = addslashes($_REQUEST['comname']);
    $datefrom = addslashes($_REQUEST['datefrom']);
    $dateto = addslashes($_REQUEST['dateto']);
    $location = addslashes($_REQUEST['location']);
    $director = addslashes($_REQUEST['director']);
    //$sanction = addslashes($_REQUEST['sanction']);
    $comptype = addslashes($_REQUEST['comptype']);
    $comcode = addslashes($_REQUEST['code']);
    $timeoffset = floatval($_REQUEST['timeoffset']);

    if ($comname == '')
    {
        echo "<b>Can't create a competition with no name</b>";    
    }
    else
    {
        $forPk = 0;
        $query = "insert into tblCompetition (comName, comLocation, comDateFrom, comDateTo, comMeetDirName, forPk, comType, comCode, comTimeOffset) values ('$comname','$location', '$datefrom', '$dateto', '$director', $forPk, '$comptype', '$comcode', $timeoffset)";
    
        $result = mysql_query($query) or die('Competition addition failed: ' . mysql_error());
    
        $comPk = mysql_insert_id();
    
        #$query = "select max(comPk) from tblCompetition";
        #$result = mysql_query($query) or die('Cant get max comPk: ' . mysql_error());
        #$comPk = mysql_result($result,0,0);
    
        $query = "insert into tblCompAuth values ($usePk, $comPk, 'admin')";
        $result = mysql_query($query) or die('CompAuth addition failed: ' . mysql_error());
    }
}

if (array_key_exists('update', $_REQUEST))
{
    $comPk = intval($_REQUEST['comPk']);
    $comname = addslashes($_REQUEST['comname']);
    $datefrom = addslashes($_REQUEST['datefrom']);
    $dateto = addslashes($_REQUEST['dateto']);
    $location = addslashes($_REQUEST['location']);
    $director = addslashes($_REQUEST['director']);
    $formula = addslashes($_REQUEST['formula']);
    $sanction = addslashes($_REQUEST['sanction']);
    $comptype = addslashes($_REQUEST['comptype']);
    $comcode = addslashes($_REQUEST['code']);
    $timeoffset = floatval($_REQUEST['timeoffset']);

    check_admin('admin',$usePk,$comPk);

    $query = "update tblCompetition set comName='$comname', comLocation='$comLocation', comDateFrom='$datefrom', comDateTo='$dateto', comDirector='$director', forPk='$formula', comSanction='$sanction', comType='$comptype', comCode='$comcode',  comTimeOffset=$timeoffset where comPk=$comPk";
    $result = mysql_query($query) or die('Competition update failed: ' . mysql_error());
}

$comparr = array();
$comparr[] = array ('', fb('Date Range'), fb('Name'), fb('Location'), fb('Director') );

echo "<form action=\"comp_admin.php\" name=\"compadmin\" method=\"post\">";
$count = 1;

if (is_admin('admin', $usePk, -1))
{
    $sql = "SELECT C.* FROM tblCompetition C order by C.comDateTo desc";
}
else
{
    $sql = "SELECT C.* FROM tblCompAuth A, tblCompetition C where A.comPk=C.comPk and A.usePk=$usePk order by C.comDateTo desc";
}
$result = mysql_query($sql,$link);
while($row = mysql_fetch_array($result, MYSQL_ASSOC))
{
    $id = $row['comPk'];
    $name = $row['comName'];
    $datefrom = substr($row['comDateFrom'], 0, 10);
    $dateto = substr($row['comDateTo'], 0, 10);
    $location = $row['comLocation'];
    $director = $row['comMeetDirName'];
    $comparr[] = array("$count.", "$datefrom - $dateto", "<a href=\"competition.php?comPk=$id\">" . $name . "</a>", $location, $director);
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

