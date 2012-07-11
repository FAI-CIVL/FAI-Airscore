<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<div id="vhead"><h1>airScore admin</h1></div>
<?php
require 'authorisation.php';
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

echo "<form action=\"comp_admin.php\" name=\"compadmin\" method=\"post\">";
echo "<ol>";
$count = 1;
$sql = "SELECT C.* FROM tblCompetition C order by C.comDateFrom desc";
$result = mysql_query($sql,$link);

while($row = mysql_fetch_array($result))
{
    $id = $row['comPk'];
    $name = $row['comName'];
    $datefrom = substr($row['comDateFrom'], 0, 10);
    $dateto = substr($row['comDateTo'], 0, 10);
    $location = $row['comLocation'];
    $director = $row['comMeetDirName'];
    echo "<li><a href=\"competition.php?comPk=$id\">$name ($datefrom - $dateto) in $location directed by $director.</a>\n";

    $count++;
}
echo "</ol><hr>";

echo "<table>";
echo "<tr><td>Name:</td><td><input type=\"text\" name=\"comname\" size=20></td>";
echo "<td>Type:</td><td>";
output_select('comptype', 'RACE', array('OLC', 'RACE', 'Free', 'Route' ));
echo "</td></tr>";
echo "<tr><td>Date From:</td><td><input type=\"text\" name=\"datefrom\" size=10>";
echo "</td><td>Date To:</td><td><input type=\"text\" name=\"dateto\" size=10></td></tr>";
echo "<tr><td>Director:</td><td><input type=\"text\" name=\"director\" size=10>";
echo "</td><td>Location:</td><td><input type=\"text\" name=\"location\" size=10></td></tr>";
echo "<tr><td>Abbrevation:</td><td><input type=\"text\" name=\"code\" size=10></td>";
echo "<td>Time Offset:</td><td><input type=\"text\" name=\"timeoffset\" size=7></td></tr>";
echo "</table>\n";
echo "<input type=\"submit\" name=\"add\" value=\"Create Competition\">";

echo "</form>";
?>
</div>
</body>
</html>

