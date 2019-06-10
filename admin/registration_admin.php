<?php
require 'admin_startup.php';
require LIBDIR.'dbextra.php';

$comPk = reqival('comPk');
$teaPk = reqival('teaPk');

$link = db_connect();
$file = __FILE__;

//initializing template header
tpadmin($link,$file);

$query = "select comName, comEntryRestrict from tblCompetition where comPk=$comPk";
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Comp query failed: ' . mysqli_connect_error());
$comName = mysqli_result($result,0,0);
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
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Handicap query failed: ' . mysqli_connect_error());

    if (mysqli_num_rows($result) == 0)
    {
        $query = "insert into tblHandicap (comPk, pilPk, hanHandicap) value ($comPk,$pilPk,1)";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot handicap insert failed: ' . mysqli_connect_error());
    }
}

if (array_key_exists('delpilot', $_REQUEST))
{
    $pilPk = intval($_REQUEST['delpilot']);
    $query = "delete from tblRegistration where comPk=$comPk and pilPk=$pilPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot delete failed: ' . mysqli_connect_error());
    $query = "delete from tblHandicap where comPk=$comPk and pilPk=$pilPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Delete handicap failed: ' . mysqli_connect_error());
}

if (array_key_exists('uppilot', $_REQUEST))
{
    $id = reqival('uppilot');
    $fai = reqsval("fai$id");
    $handi = reqfval("han$id");
    $query = "update PilotView set pilFAI='$fai' where pilPk=$id";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot ID update failed: ' . mysqli_connect_error());

    $regarr = [];
    $regarr['pilPk'] = $id;
    $regarr['comPk'] = $comPk;
    $regarr['hanHandicap'] = $handi;
    $clause = "comPk=$comPk and pilPk=$id";
    insertup($link, 'tblHandicap', 'hanPk', $clause, $regarr);
}

echo "<form action=\"registration_admin.php?comPk=$comPk&cat=$cat$tsel\" name=\"regadmin\" method=\"post\">";

$query = "  SELECT
                P.*
            FROM
                tblRegistration R
            JOIN PilotView P USING(pilPk)
            INNER JOIN tblHandicap H USING(comPk, pilPk)
            WHERE
                R.comPk = $comPk
            ORDER BY
                P.pilLastName";

$regpilots = [];
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Team pilots query failed: ' . mysqli_connect_error());
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $regpilots[] = $row;
}

if (sizeof($regpilots) > 0)
{
    $outreg = [];
    $outreg[] = array("", "FAI Nr.", "Name", "Surname", "XContest User", "");
    foreach ($regpilots as $row)
    {
        $pilPk = intval($row['pilPk']);
        #if ($row['hanHandicap'] == '')
        #{
        #    $row['hanHandicap'] = 1;
        #}
        $outreg[] = array("<button type=\"submit\" name=\"uppilot\" value=\"$pilPk\">up</button>", fin("fai$pilPk", $row['pilFAI'], 5), $row['pilFirstName'], $row['pilLastName'], isset($row['pilXContestUser']) ? $row['pilXContestUser'] : "<strong style='color: red'>NOT SET</strong>", fbut('submit', 'delpilot', $pilPk, 'del'));
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
    echo "<td><a href=\"registration_admin.php?comPk=$comPk&cat=$let$tsel\">$let</a>&nbsp;</td>";
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
    $sql = "SELECT 
				P.* 
			FROM 
				PilotView P 
			WHERE 
				P.pilLastName like '$cat%' 
				AND NOT EXISTS (
					SELECT 
						R.regPk 
					FROM 
						tblRegistration R 
					WHERE 
						R.comPk = $comPk 
						AND R.pilPk = P.pilPk
				) 
			ORDER BY 
				P.pilLastName";
				$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Pilot select failed: ' . mysqli_connect_error());

    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $id = $row['pilPk'];
        $ext = 'DB- ';
        if ( $id > 9999 )
        {
            $ext = "<span style='text-weight:bold;color:red;'>EXT </span>";
        }
        $lname = $row['pilLastName'];
        $fname = $row['pilFirstName'];
        $fai = $row['pilFAI'];
        $sex = $row['pilSex'];
        echo "<li><button type=\"submit\" name=\"addpilot\" value=\"$id\">add</button>";
        //echo "<li><button type=\"submit\" name=\"addpilot\" value=\"$id\" onclick=\"add_pilot($id);\">add</button>";
        echo "$ext $fai $fname $lname ($sex).<br>\n";
        $count++;
    }
    echo "</ol>";
}
echo "</form>";

echo "<br><br>";
echo "<p>";
echo "<a href='competition_admin.php?comPk=$comPk'>Back to Competition</a>";
echo "</p>";

echo '</div>';
echo '</div>';
echo '</div>';

tpfooter($file);

?>
