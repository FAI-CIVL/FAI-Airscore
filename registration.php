<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
<link HREF="col2.css" REL="stylesheet" TYPE="text/css">
<script src="microajax.minified.js" type="text/javascript"></script>
<script type="text/javascript">
//<![CDATA[
var map;
function add_pilot(pilPk)
{
    alert("add_pilot="+pilPk);
}
//]]>
</script>
</head>
<body>
<div id="container">
<div id="vhead"><h1>airScore admin</h1></div>
<?php
require 'authorisation.php';
require 'format.php';
require 'dbextra.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

$comPk = reqival('comPk');
$teaPk = reqival('teaPk');
adminbar($comPk);

$link = db_connect();
$query = "select comName, comEntryRestrict from tblCompetition where comPk=$comPk";
//$result = mysql_query($query) or die('Comp query failed: ' . mysql_error());
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Comp query failed: ' . mysqli_connect_error());
//$comName = mysql_result($result,0,0);
$comName = mysqli_result($result,0,0);
//$comRestricted = mysql_result($result,0,1);
$comRestricted = mysqli_result($result,0,1);

echo '<div id ="container2">';
echo '<div id ="container1">';
echo '<div id ="col1">';

if ($comRestricted == 'open')
{
    echo "Open competition entry<br>\n";
    return;
}

echo "<p><h2>Registration - $comName</h2></p>";
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
    $addarr = [];
    $addarr['pilPk'] = $pilPk;
    $addarr['comPk'] = $comPk;
    $clause = "comPk=$comPk and pilPk=$pilPk";
    insertup($link, 'tblRegistration', 'regPk', $clause, $addarr);

    $query = "select H.* from tblHandicap H where H.comPk=$comPk and H.pilPk=$pilPk";
//    $result = mysql_query($query) or die('Handicap query failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Handicap query failed: ' . mysqli_connect_error());

//    if (mysql_num_rows($result) == 0)
    if (mysqli_num_rows($result) == 0)
    {
        $query = "insert into tblHandicap (comPk, pilPk, hanHandicap) value ($comPk,$pilPk,1)";
//        $result = mysql_query($query) or die('Pilot handicap insert failed: ' . mysql_error());
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot handicap insert failed: ' . mysqli_connect_error());
    }
}

if (array_key_exists('delpilot', $_REQUEST))
{
    $pilPk = intval($_REQUEST['delpilot']);
    $query = "delete from tblRegistration where comPk=$comPk and pilPk=$pilPk";
//    $result = mysql_query($query) or die('Pilot delete failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot delete failed: ' . mysqli_connect_error());
    $query = "delete from tblHandicap where comPk=$comPk and pilPk=$pilPk";
//    $result = mysql_query($query) or die('Delete handicap failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Delete handicap failed: ' . mysqli_connect_error());
}

if (array_key_exists('uppilot', $_REQUEST))
{
    $id = reqival('uppilot');
    $fai = reqsval("fai$id");
    $handi = reqfval("han$id");
    $query = "update tblPilot set pilHGFA='$fai' where pilPk=$id";
//    $result = mysql_query($query) or die('Pilot ID update failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot ID update failed: ' . mysqli_connect_error());

    $regarr = [];
    $regarr['pilPk'] = $id;
    $regarr['comPk'] = $comPk;
    $regarr['hanHandicap'] = $handi;
    $clause = "comPk=$comPk and pilPk=$id";
    insertup($link, 'tblHandicap', 'hanPk', $clause, $regarr);
}

echo "<form action=\"registration.php?comPk=$comPk&cat=$cat$tsel\" name=\"regadmin\" method=\"post\">";

$query = "select P.*,H.hanHandicap from tblRegistration R left join tblPilot P on P.pilPk=R.pilPk left outer join tblHandicap H on H.pilPk=P.pilPk and H.comPk=$comPk where R.comPk=$comPk order by P.pilLastName";

$regpilots = [];
//$result = mysql_query($query) or die('Team pilots query failed: ' . mysql_error());
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Team pilots query failed: ' . mysqli_connect_error());
//while ($row = mysql_fetch_array($result))
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $regpilots[] = $row;
}

if (sizeof($regpilots) > 0)
{
    $outreg = [];
    foreach ($regpilots as $row)
    {
        $pilPk = intval($row['pilPk']);
        #if ($row['hanHandicap'] == '')
        #{
        #    $row['hanHandicap'] = 1;
        #}
        $outreg[] = array("<button type=\"submit\" name=\"uppilot\" value=\"$pilPk\">up</button>", fin("fai$pilPk", $row['pilHGFA'], 5), $row['pilFirstName'], $row['pilLastName'], fin("han$pilPk", $row['hanHandicap'], 1), fbut('submit', 'delpilot', $pilPk, 'del'));
        //"<input type=\"text\" name=\"tepModifier$tepPk\" value=\"$tepMod\" size=3>", fbut('submit', 'uppilot', $tepPk, 'up')
    }
    echo "<i>" . sizeof($regpilots) . " pilots registered</i>";
    echo ftable($outreg,'id="piltable"','','');
}
else
{
    echo "<i>No pilots registered yet.</i>";
}

echo "</div>";

echo '<div id="col2">';
echo "<h2>Pilots by Name: $cat</h2><p>";
$letters = array( 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
        'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z');
echo "<table><tr>";
$count = 0;

foreach ($letters as $let)
{
    $count++;
    echo "<td><a href=\"registration.php?comPk=$comPk&cat=$let$tsel\">$let</a>&nbsp;</td>";
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
//    $result = mysql_query($sql,$link) or die('Pilot select failed: ' . mysql_error());
    $result = mysqli_query($link, $sql,$link) or die('Error ' . mysqli_errno($link) . ' Pilot select failed: ' . mysqli_connect_error());

//    while($row = mysql_fetch_array($result))
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $id = $row['pilPk'];
        $lname = $row['pilLastName'];
        $fname = $row['pilFirstName'];
        $hgfa = $row['pilHGFA'];
        $sex = $row['pilSex'];
        echo "<li><button type=\"submit\" name=\"addpilot\" value=\"$id\">add</button>";
        //echo "<li><button type=\"submit\" name=\"addpilot\" value=\"$id\" onclick=\"add_pilot($id);\">add</button>";
        echo "$hgfa $fname $lname ($sex).<br>\n";
        $count++;
    }
    echo "</ol>";
}
echo "</form>";
echo '</div>';
echo '</div>';
echo '</div>';


?>
</div>
</body>
</html>

