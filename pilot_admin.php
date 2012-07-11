<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<div id="vhead"><h1>airScore admin</h1></div>
<?php
require_once 'authorisation.php';
require_once 'format.php';
require_once 'dbextra.php';

$comPk = reqival('comPk');
adminbar($comPk);
?>
<p><h2>Pilot Administration</h2></p>
<?php

$usePk = auth('system');
$link = db_connect();

$cat = reqsval('cat');
if ($cat == '')
{
    $cat = 'A';
}
$ozimp = reqsval('ozimp');

if (array_key_exists('addcomp', $_REQUEST))
{
    $comp = intval($_REQUEST['compid']);
    $xmltxt = file_get_contents("http://ozparaglidingcomps.com/scoringExport.php?password=$ozimp&comp_id=$comp");
    $xml = new SimpleXMLElement($xmltxt);
    foreach ($xml->pilot as $pilot)
    {
        $pilarr = array();
        $namarr = explode(" ", $pilot->name, 2);
        $pil['pilLastName'] = $namarr[1];
        $pil['pilFirstName'] = $namarr[0];
        $pil['pilHGFA'] = $pilot->fai_id;
        $pil['pilCIVL'] = $pilot->civl_id;
        $pil['pilBirthdate'] = $pilot->birthday;
        $pil['pilSex'] = $pilot->gender;
        $pil['pilNationCode'] = $pilot->nation;
        // $pilot->glider_make

        if ($pilot->fai_id != '')
        {
            $clause = "pilHGFA=" . quote($pilot->fai_id) . " and pilLastName=" . quote($namarr[1]);
            $pilPk = insertup($link, 'tblPilot', 'pilPk', $clause, $pil);

            if ($comPk > 0)
            {
                $regarr = array();
                $reg['pilPk'] = $pilPk;
                $reg['comPk'] = $comPk;
                $clause = "comPk=$comPk and pilPk=$pilPk";
                insertup($link, 'tblRegistration', 'regPk', $clause, $regarr);
            }
        }
        else if ($pilot->name != '')
        {
            if (0 + $pilot->civl_id > 0)
            {
                $pil['pilHGFA'] = 1000000 + $pilot->civl_id;
            }
            $clause = " pilLastName=" . quote($namarr[1]) . " and pilFirstName=" . quote($namarr[0]);
            $pilPk = insertup($link, 'tblPilot', 'pilPk', $clause, $pil);

            if ($comPk > 0)
            {
                $regarr = array();
                $reg['pilPk'] = $pilPk;
                $reg['comPk'] = $comPk;
                $clause = "comPk=$comPk and pilPk=$pilPk";
                insertup($link, 'tblRegistration', 'regPk', $clause, $regarr);
            }
        }
        else
        {
            echo "Unable to add (no id): " . $pilot->name . " id=" . $pilot->fai_id . "<br>";
        }
    }
}

if (array_key_exists('addpilot', $_REQUEST))
{
    $fai = intval($_REQUEST['fai']);
    $lname = addslashes($_REQUEST['lname']);
    $fname = addslashes($_REQUEST['fname']);
    $sex = addslashes($_REQUEST['sex']);
    $query = "insert into tblPilot (pilHGFA, pilLastName, pilFirstName, pilSex, pilNationCode) value ($fai,'$lname','$fname','$sex','AUS')";
    $result = mysql_query($query) or die('Pilot insert failed: ' . mysql_error());
}

if (array_key_exists('bulkadd', $_REQUEST))
{
    $out = '';
    $retv = 0;
    $copyname = tempnam(FILEDIR, $name . "_");
    copy($_FILES['bulkpilots']['tmp_name'], $copyname);
    //echo "bulk_pilot_import.pl $copyname<br>";
    chmod($copyname, 0644);

    exec(BINDIR . "bulk_pilot_import.pl $copyname", $out, $retv);
    foreach ($out as $txt)
    {  
        echo "$txt<br>\n";
    }
}

if (array_key_exists('update', $_REQUEST))
{
    $id = intval($_REQUEST['update']);
    $fai = intval($_REQUEST["fai$id"]);
    $lname = addslashes($_REQUEST["lname$id"]);
    $fname = addslashes($_REQUEST["fname$id"]);
    $sex = addslashes($_REQUEST["sex$id"]);
    $nat = addslashes($_REQUEST["nation$id"]);
    $query = "update tblPilot set pilHGFA=$fai, pilLastName='$lname', pilFirstName='$fname', pilSex='$sex', pilNationCode='$nat' where pilPk=$id";
    $result = mysql_query($query) or die('Pilot update failed: ' . mysql_error());
}

if (array_key_exists('delete', $_REQUEST))
{
    check_admin('admin',$usePk,-1);
    $id = intval($_REQUEST['delete']);
    $query = "delete from tblPilot where pilPk=$id";
    $result = mysql_query($query) or die('Config update failed: ' . mysql_error());
}

if ($ozimp)
{
    echo "<form enctype=\"multipart/form-data\" action=\"pilot_admin.php?ozimp=$ozimp\" name=\"trackadmin\" method=\"post\">";
}
else
{
    echo "<form enctype=\"multipart/form-data\" action=\"pilot_admin.php?cat=$cat\" name=\"trackadmin\" method=\"post\">";
}

echo "<input type=\"hidden\" name=\"MAX_FILE_SIZE\" value=\"1000000000\">";
echo "HGFA/FAI: " . fin('fai', '', 5);
echo "LastName: " . fin('lname', '', 10); 
echo "FirstName: " . fin('fname', '', 10); 
echo "Sex: " . fselect('sex', 'M', array('M' => 'M', 'F' => 'F'));
echo fis('addpilot', "Add Pilot", 5); 
echo "<br>";
echo "CSV (Last,First,FAI#,Sex,CIVL#): <input type=\"file\" name=\"bulkpilots\">";
echo fis('bulkadd', 'Bulk Submit', 5);

if ($ozimp)
{
    echo "<p>";
    $comparr = array();
    $xmltxt = file_get_contents("http://ozparaglidingcomps.com/compListXml.php");
    $xml = new SimpleXMLElement($xmltxt);
    foreach ($xml->comp as $comp)
    {
        $comparr["" . $comp->comp_name] = $comp->comp_id;
    }
    echo fselect('compid', '', $comparr);
    echo fis('addcomp', 'Import Comp', '');
}

echo "<hr>";

echo "<h2>Pilots by Name: $cat</h2><p>";
$letters = array( 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
        'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
        'Y', 'Z');
echo "<table><tr>";
$count = 0;
foreach ($letters as $let)
{
    $count++;
    echo "<td><a href=\"pilot_admin.php?cat=$let\">$let</a>&nbsp;</td>";
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
        $nat = $row['pilNationCode'];
        echo "<li><button type=\"submit\" name=\"delete\" value=\"$id\">del</button>";
        echo "<button type=\"submit\" name=\"update\" value=\"$id\">up</button>";
        //echo " $hgfa $name ($sex).<br>\n";
        echo "<input type=\"text\" name=\"fai$id\" value=\"$hgfa\" size=7>";
        echo "<input type=\"text\" name=\"lname$id\" value=\"$lname\" size=10>";
        echo "<input type=\"text\" name=\"fname$id\" value=\"$fname\" size=10>";
        echo "<input type=\"text\" name=\"sex$id\" value=\"$sex\" size=3>";
        echo "<input type=\"text\" name=\"nation$id\" value=\"$nat\" size=3> <br>";
        # echo a delete button ...
    
        $count++;
    }
    echo "</ol>";
}


echo "</form>";
?>
</div>
</body>
</html>

