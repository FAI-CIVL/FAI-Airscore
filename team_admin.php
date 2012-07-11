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

$comPk = intval($_REQUEST['comPk']);
$teaPk = intval($_REQUEST['teaPk']);
adminbar($comPk);

$link = db_connect();
$query = "select comName, comTeamScoring from tblCompetition where comPk=$comPk";
$result = mysql_query($query) or die('Task add failed: ' . mysql_error());
$comName = mysql_result($result,0,0);
$comTeamScoring = mysql_result($result,0,1);

echo "<p><h2>Teams - $comName ($comTeamScoring)</h2></p>";

$usePk = auth('system');
$cat = addslashes($_REQUEST['cat']);
if ($cat == '')
{
    $cat = 'A';
}
$link = db_connect();


if (!check_admin('admin',$usePk,$comPk))
{
    return 0;
}

if (array_key_exists('addpilot', $_REQUEST))
{
    $pilPk = intval($_REQUEST['addpilot']);
    $query = "insert into tblTeamPilot (teaPk, pilPk, tepModifier) value ($teaPk,$pilPk,1.0)";
    $result = mysql_query($query) or die('Pilot insert failed: ' . mysql_error());
}

if (array_key_exists('delpilot', $_REQUEST))
{
    $pilPk = intval($_REQUEST['pilPk']);
    $tepPk = intval($_REQUEST['tepPk']);
    $query = "delete from tblTeamPilot where teaPk=$teaPk and tepPk=$tepPk";
    $result = mysql_query($query) or die('Pilot delete failed: ' . mysql_error());
}

if (array_key_exists('uppilot', $_REQUEST))
{
    $tepPk = intval($_REQUEST['uppilot']);
    $mod = floatval($_REQUEST["tepModifier$tepPk"]);
    #echo "tepPk=$tepPk mod=$mod<br>";
    if ($comTeamScoring == 'handicap')
    {
        if ($tepPk < 0)
        {
            $tepPk = -$tepPk;
            $query = "insert into tblHandicap (comPk, pilPk, hanHandicap) values ($comPk, $tepPk, $mod)";
        }
        else
        {
            $query = "update tblHandicap set hanHandicap=$mod where hanPk=$tepPk";
        }
    }
    else
    {
        $query = "update tblTeamPilot set tepModifier=$mod where tepPk=$tepPk";
    }
    $result = mysql_query($query) or die('Pilot update failed: ' . mysql_error());
}

if (array_key_exists('addteam', $_REQUEST))
{
    $pilPk = intval($_REQUEST['pilPk']);
    $tname = addslashes($_REQUEST['teamname']);
    $query = "insert into tblTeam (comPk, teaName) value ($comPk,'$tname')";
    $result = mysql_query($query) or die('Team create failed: ' . mysql_error());
    $teaPk = mysql_insert_id();
}

if (array_key_exists('upteam', $_REQUEST))
{
    // update team name
}


if (array_key_exists('delteam', $_REQUEST))
{
    $query = "delete from tblTeam where teaPk=$teaPk";
    $result = mysql_query($query) or die('Delete team failed: ' . mysql_error());
    $query = "delete from tblTeamPilot where teaPk=$teaPk";
    $result = mysql_query($query) or die('Delete team pilot failed: ' . mysql_error());
    $teaPk = 0;
}

$query = "select teaName from tblTeam where teaPk=$teaPk";
$result = mysql_query($query) or die('Team name query failed: ' . mysql_error());
if (mysql_num_rows($result) > 0)
{
    $teamname = mysql_result($result,0,0);
}
else
{
    $teaPk = 0;
}

$tsel='';
if ($teaPk > 0)
{
    $tsel = "&teaPk=$teaPk";
}
echo "<form action=\"team_admin.php?comPk=$comPk&cat=$cat$tsel\" name=\"teamadmin\" method=\"post\">";

echo "TeamName: <input type=\"text\" name=\"teamname\" size=10>";
echo "<input type=\"submit\" name=\"addteam\" value=\"Create Team\">";

$query = "select T.* from tblTeam T where comPk=$comPk";
$result = mysql_query($query) or die('Team query failed: ' . mysql_error());
$teamarr = Array();
while ($row = mysql_fetch_array($result))
{
    $teamarr[$row['teaName']] = $row['teaPk'];
}

if (sizeof($teamarr) > 0)
{
    echo "<p>";
    ksort($teamarr);
    $ttcnt = 0;
    $teamtab = Array();
    $teamrow = Array();
    foreach ($teamarr as $name => $id)
    {
        $teamrow[] = "<a href=\"team_admin.php?comPk=$comPk&cat=$cat&teaPk=$id\">$name</a>&nbsp;";
        $ttcnt++;
        if ($ttcnt % 10 == 0)
        {
            $teamtab[] = $teamrow;
            $teamrow = Array();
        }
    }

    if ($ttcnt % 10 != 0)
    {
        $teamtab[] = $teamrow;
    }

    echo ftable($teamtab, '', '', '');
}

echo "<hr>";

if ($teaPk > 0)
{
    if ($comTeamScoring == 'handicap')
    {
        $query = "select T.*, P.*, H.hanPk as tepPk, H.hanHandicap as tepModifier from tblTeam T,tblTeamPilot TP,tblPilot P left outer join tblHandicap H on H.pilPk = P.pilPk and H.comPk=$comPk where TP.teaPk=T.teaPk and P.pilPk=TP.pilPk and T.teaPk=$teaPk";
    }
    else
    {
        $query = "select T.*, TP.*, P.* from tblTeam T,tblTeamPilot TP,tblPilot P where TP.teaPk=T.teaPk and P.pilPk=TP.pilPk and T.teaPk=$teaPk";
    }
    $result = mysql_query($query) or die('Team pilots query failed: ' . mysql_error());
    $row = mysql_fetch_array($result);
    $selteaPk = $row['teaPk'];
    if ($row)
    {
        $teampilots = Array();
        do 
        {
            $teampilots[] = $row;
            $row = mysql_fetch_array($result);
        } while ($row);
    }

    echo "<h2>Current Team: $teamname</h2><p>";
    if (sizeof($teampilots) > 0)
    {
        $outteam = Array();
        foreach ($teampilots as $row)
        {
            $tepMod = floatval($row['tepModifier']);
            $tepPk = intval($row['tepPk']);
            if ($tepMod == 0)
            {
                // Huh?
                $tepPk = -(intval($row['pilPk']));
            }
            $outteam[] = Array($row['pilFirstName'], $row['pilLastName'], 
                "<input type=\"text\" name=\"tepModifier$tepPk\" value=\"$tepMod\" size=3>",
                "<button type=\"submit\" name=\"uppilot\" value=\"$tepPk\">up</button>");
        }
        echo ftable($outteam,'','','');
    }
    else
    {
        echo "<i>No pilots in team yet.</i>";
    }
    echo "<button type=\"submit\" name=\"delteam\" value=\"$teaPk\">Delete Team</button>";
    echo "<hr>";
}




echo "<h2>Pilots by Name: $cat</h2><p>";
$letters = array( 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
        'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
        'Y', 'Z');
echo "<table><tr>";
$count = 0;
foreach ($letters as $let)
{
    $count++;
    echo "<td><a href=\"team_admin.php?comPk=$comPk&cat=$let$tsel\">$let</a>&nbsp;</td>";
    if ($count % 26 == 0)
    {
            echo "</tr><tr>";
    }
}
echo "</tr></table>";
if ($cat != '')
{
    echo "<ol>";
    $count = 1;
    $sql = "SELECT P.* FROM tblPilot P where P.pilLastName like '$cat%' order by P.pilLastName";
    $result = mysql_query($sql,$link) or die('Pilot select failed: ' . mysql_error());

    while($row = mysql_fetch_array($result))
    {
        $id = $row['pilPk'];
        $lname = $row['pilLastName'];
        $fname = $row['pilFirstName'];
        $hgfa = $row['pilHGFA'];
        $sex = $row['pilSex'];
        echo "<li><button type=\"submit\" name=\"addpilot\" value=\"$id\">add</button>";
        echo "$hgfa $fname $lname ($sex).<br>\n";
        $count++;
    }
    echo "</ol>";
}

echo "</form>";

?>
</div>
</body>
</html>

