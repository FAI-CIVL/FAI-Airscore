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

$comPk = intval($_REQUEST['comPk']);
$teaPk = intval($_REQUEST['teaPk']);
adminbar($comPk);

$link = db_connect();
$query = "select comName, comEntryRestrict from tblCompetition where comPk=$comPk";
$result = mysql_query($query) or die('Comp query failed: ' . mysql_error());
$comName = mysql_result($result,0,0);
$comRestricted = mysql_result($result,0,1);

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
    $query = "insert into tblRegistration (comPk, pilPk) value ($comPk,$pilPk)";
    $result = mysql_query($query) or die('Pilot insert failed: ' . mysql_error());
}

if (array_key_exists('delpilot', $_REQUEST))
{
    $pilPk = intval($_REQUEST['delpilot']);
    $query = "delete from tblRegistration where comPk=$comPk and pilPk=$pilPk";
    $result = mysql_query($query) or die('Pilot delete failed: ' . mysql_error());
}

echo "<form action=\"registration.php?comPk=$comPk&cat=$cat$tsel\" name=\"regadmin\" method=\"post\">";

$query = "select P.* from tblRegistration R, tblPilot P where P.pilPk=R.pilPk and R.comPk=$comPk order by P.pilFirstName";

$regpilots = array();
$result = mysql_query($query) or die('Team pilots query failed: ' . mysql_error());
while ($row = mysql_fetch_array($result))
{
    $regpilots[] = $row;
}

if (sizeof($regpilots) > 0)
{
    $outreg = array();
    foreach ($regpilots as $row)
    {
        $pilPk = intval($row['pilPk']);
        $outreg[] = array(
            "<button type=\"submit\" name=\"delpilot\" value=\"$pilPk\">del</button>", $row['pilFirstName'], $row['pilLastName']);
        //"<input type=\"text\" name=\"tepModifier$tepPk\" value=\"$tepMod\" size=3>", fbut('submit', 'uppilot', $tepPk, 'up')
    }
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
    $result = mysql_query($sql,$link) or die('Pilot select failed: ' . mysql_error());

    while($row = mysql_fetch_array($result))
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

