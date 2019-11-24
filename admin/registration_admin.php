<?php
require 'admin_startup.php';
require LIBDIR.'dbextra.php';

$comPk = reqival('comPk');
$teaPk = reqival('teaPk');

$link = db_connect();
$file = __FILE__;

//initializing template header
tpadmin($link,$file);

$query = "SELECT `comName`, `comEntryRestrict` FROM `tblCompetition` WHERE `comPk` = $comPk LIMIT 1";
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
    $pilPk = reqival('addpilot');

    #get pilot info from DB
    $query = "  SELECT
                    CONCAT(`P`.`pilFirstName`, ' ', `P`.`pilLastName`) AS `name`,
                    `P`.`pilSex` AS `sex`,
                    ( SELECT `C`.`natIso3` FROM `tblCountryCode` `C` WHERE `C`.`natID` = `P`.`pilNat` ) AS `nat`,
                    `P`.`pilCIVL` AS `civl`,
                    `P`.`pilFAI` AS `fai`,
                    CONCAT(`P`.`pilGliderBrand`, ' ', `P`.`pilGlider`) AS `glider`,
                    `P`.`gliGliderCert` AS `cert`,
                    `P`.`pilSponsor` AS `sponsor`,
                    `P`.`pilXContestUser` AS `xc`
                FROM `PilotView` `P`
                WHERE `P`.`pilPk` = $pilPk
                LIMIT 1";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot data retrieval failed: ' . mysqli_connect_error());
    $row = mysqli_fetch_assoc($result);

    # create pilot data array
    $addarr = [];
    $addarr['pilPk'] = $pilPk;
    $addarr['comPk'] = $comPk;
    $addarr['regName'] = $row['name'];
    $addarr['regSex'] = $row['sex'];
    $addarr['regNat'] = $row['nat'];
    $addarr['regGlider'] = $row['glider'];
    #class needs to be calculated from Cert and comp formula
    $addarr['regCert'] = $row['cert'];
    $addarr['regSponsor'] = $row['sponsor'];
    $addarr['regCIVL'] = $row['civl'];
    $addarr['regFAI'] = $row['fai'];
    $addarr['regXC'] = $row['xc'];
    # create insert command
    $clause = "`comPk` = $comPk AND `pilPk` = $pilPk";
    $regPk = insertup($link, 'tblRegistration', 'regPk', $clause, $addarr);

    if ($regPk > 0) {
        $message .= "Pilot succesfully registered with reg. id $regPk. <br />";
    }
}

// if (array_key_exists('addpilot', $_REQUEST))
// {
//     $pilPk = intval($_REQUEST['addpilot']);
//     $addarr = [];
//     $addarr['pilPk'] = $pilPk;
//     $addarr['comPk'] = $comPk;
//     $clause = "comPk=$comPk and pilPk=$pilPk";
//     insertup($link, 'tblRegistration', 'regPk', $clause, $addarr);
// }

if (array_key_exists('delpilot', $_REQUEST))
{
    $pilPk = intval($_REQUEST['delpilot']);
    $query = "DELETE FROM `tblRegistration` WHERE `comPk` = $comPk AND `pilPk` = $pilPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot delete failed: ' . mysqli_connect_error());
    // $query = "delete from tblHandicap where comPk=$comPk and pilPk=$pilPk";
    // $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Delete handicap failed: ' . mysqli_connect_error());
}

if (array_key_exists('uppilot', $_REQUEST))
{
    $id = reqival('uppilot');
    $fai = reqsval("fai$id");
    // $handi = reqfval("han$id");
    // $query = "update PilotView set pilFAI='$fai' where pilPk=$id";
    // $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot ID update failed: ' . mysqli_connect_error());

    // $regarr = [];
    // $regarr['pilPk'] = $id;
    // $regarr['comPk'] = $comPk;
    // $regarr['hanHandicap'] = $handi;
    // $clause = "comPk=$comPk and pilPk=$id";
    // insertup($link, 'tblHandicap', 'hanPk', $clause, $regarr);
}

echo "<form action=\"registration_admin.php?comPk=$comPk&cat=$cat$tsel\" name=\"regadmin\" method=\"post\">";

#get Team scoring
$query = "  SELECT
                `comTeamScoring`
            FROM `tblForComp`
            WHERE
                `comPk` = $comPk
            LIMIT 1";
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Team Scoring query failed: ' . mysqli_connect_error());
$team = mysqli_result($result, 0, 0);

$query = "  SELECT
                *
            FROM `tblRegistration`
            WHERE
                `comPk` = $comPk
            ORDER BY
                `regName`";

$regpilots = [];
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Registered pilots query failed: ' . mysqli_connect_error());
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $regpilots[] = $row;
}

if (sizeof($regpilots) > 0)
{
    $outreg = [];
    $header = [];
    $header = array("ID", "Name", "Nat.", "CIVL n.", "FAI n.", "Glider", "Class", "Sponsor", "XContest User");
    if ($team == 1) {
        $header[] = "Team";
    }
    $header[] = array("", "");
    $outreg[] = $header;

    foreach ($regpilots as $row)
    {
        $pilPk = intval($row['pilPk']);
        #if ($row['hanHandicap'] == '')
        #{
        #    $row['hanHandicap'] = 1;
        #}
        $pilot = [];
        $pilot[] = fin("ID$pilPk", "", 4);
        $pilot[] = fin("surname$pilPk", $row['regName'], 24);
        $pilot[] = fin("nat$pilPk", $row['regNat'], 4);
        $pilot[] = fin("civl$pilPk", $row['regCIVL'], 6);
        $pilot[] = fin("fai$pilPk", $row['regFAI'], 8);
        $pilot[] = fin("glider$pilPk", $row['regGlider'], 14);
        $pilot[] = fin("class$pilPk", $row['regClass'], 6);
        $pilot[] = fin("sponsor$pilPk", $row['regSponsor'], 16);
        $pilot[] = fin("XC$pilPk", $row['regXC'], 14);
        if ($team == 1) {
            $pilot[] = fin("team$pilPk", $row['regTeam'], 8);
        }
        $pilot[] = "<button type=\"submit\" name=\"uppilot\" value=\"$pilPk\">up</button>";
        $pilot[] = fbut('submit', 'delpilot', $pilPk, 'del');

        $outreg[] = $pilot;
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
                `P`.*
            FROM
                `PilotView` `P`
            WHERE
                `P`.`pilLastName` LIKE '$cat%'
            AND NOT EXISTS (
                SELECT
                    `R`.`regPk`
                FROM
                    `tblRegistration` `R`
                WHERE
                    `R`.`comPk` = $comPk
                AND `R`.`pilPk` = `P`.`pilPk`
                )
            ORDER BY
                `P`.`pilLastName`";

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
