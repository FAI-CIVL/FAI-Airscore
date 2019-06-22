<?php
require 'admin_startup.php';
require_once LIBDIR.'dbextra.php';

$comPk = reqival('comPk');
$usePk = auth('system');
$link = db_connect();
$file = __FILE__;

//initializing template header
tpadmin($link,$file);

echo "<h3>Pilot Administration</h3>\n";
$message = '';
$content = '';

$cat = reqsval('cat');
if ($cat == '')
{
    $cat = 'A';
}
$ozimp = reqsval('ozimp');

if (reqexists('addcomp'))
{
    $comp = reqival('compid');
    $paid = reqsval('paidonly');
    $handicap = reqsval('handicap');
    echo "addcomp $comp $paid $handicap<br>";
    $xmltxt = file_get_contents("http://ozparaglidingcomps.com/scoringExport.php?password=$ozimp&comp_id=$comp");
    $xml = new SimpleXMLElement($xmltxt);
    foreach ($xml->pilot as $pilot)
    {
        $pilarr = [];
        $namarr = explode(" ", $pilot->name, 2);
        if (sizeof($namarr) < 2)
        {
            echo "Skipping " . $pilot->name . "<br>";
            continue;
        }
        $pil['pilLastName'] = mysqli_real_escape_string($link, $namarr[1]);
        $pil['pilFirstName'] = mysqli_real_escape_string($link, $namarr[0]);
        $pil['pilFAI'] = $pilot->fai_id;
        $pil['pilCIVL'] = $pilot->civl_id;
        $pil['pilBirthdate'] = $pilot->birthday;
        $pil['pilSex'] = $pilot->gender;
        $pil['pilNationCode'] = $pilot->nation;
        //$pil['regHours'] = $pilot->xc_hours;
        // $pilot->glider_make

        #echo "hours=" . $pilot->xc_hours . "\n";
        $hours = intval($pilot->xc_hours);
        if ($hours < 50)
        {
            $handi = 3;
        }
        elseif ($hours < 150)
        {
            $handi = 2;
        }
        else
        {
            $handi = 1;
        }

        if ($paid == "on" && $pilot->paid != "1")
        {
            // skip non-payers
            continue;
        }

        if ($pilot->fai_id != '')
        {
            $clause = "pilFAI=" . quote($pilot->fai_id) . " and pilLastName=" . quote(mysqli_real_escape_string($link, $namarr[1]));
            $pilPk = insertnullup($link, 'PilotView', 'pilPk', $clause, $pil);
            echo "insertup: $clause<br>";

            if ($comPk > 0)
            {
                $regarr = [];
                $regarr['pilPk'] = $pilPk;
                $regarr['comPk'] = $comPk;
                $regarr['regHours'] = $pilot->xc_hours;
                $clause = "comPk=$comPk and pilPk=$pilPk";
                insertup($link, 'tblRegistration', 'regPk', $clause, $regarr);
                if ($handicap == "on")
                {
                    $handarr = [];
                    $handarr['pilPk'] = $pilPk;
                    $handarr['comPk'] = $comPk;
                    $handarr['hanHandicap'] = $handi;
                    $clause = "comPk=$comPk and pilPk=$pilPk";
                    insertup($link, 'tblHandicap', 'hanPk', $clause, $handarr);
                }
            }
        }
        elseif ($pilot->name != '')
        {
            if (0 + $pilot->civl_id > 0)
            {
                $pil['pilFAI'] = 1000000 + $pilot->civl_id;
            }
            $clause = " pilLastName=" . quote(mysqli_real_escape_string($link, $namarr[1])) . " and pilFirstName=" . quote(mysqli_real_escape_string($link, $namarr[0]));
            echo "insertup: $clause<br>";
            $pilPk = insertnullup($link, 'PilotView', 'pilPk', $clause, $pil);

            if ($comPk > 0)
            {
                $regarr = [];
                $regarr['pilPk'] = $pilPk;
                $regarr['comPk'] = $comPk;
                $regarr['regHours'] = $pilot->xc_hours;
                $clause = "comPk=$comPk and pilPk=$pilPk";
                insertup($link, 'tblRegistration', 'regPk', $clause, $regarr);
                if ($handicap == "on")
                {
                    $handarr = [];
                    $handarr['pilPk'] = $pilPk;
                    $handarr['comPk'] = $comPk;
                    $handarr['hanHandicap'] = $handi;
                    $clause = "comPk=$comPk and pilPk=$pilPk";
                    insertup($link, 'tblHandicap', 'hanPk', $clause, $handarr);
                }
            }
        }
        else
        {
            echo "Unable to add (no id): " . $pilot->name . " id=" . $pilot->fai_id . "<br>";
        }
    }
}

if (reqexists('addpilot'))
{
    $fai = reqival('fai');
    $civl = reqival('civl');
    $lname = reqsval('lname');
    $fname = reqsval('fname');
    $sex = reqsval('sex');
    $nat = reqsval('nation');
    $brand = reqsval('brand');
    $glider = reqsval('glider');
    $cert = reqsval('cert');
	$xcid = reqsval('xcontest');

	#look for pilot in PilotView
    $query = "SELECT * from PilotView WHERE pilLastName LIKE CONCAT('%', '$lname' ,'%') AND pilFirstName LIKE CONCAT('%', '$fname' ,'%') ";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot select failed: ' . mysqli_connect_error());
    if ( mysqli_num_rows($result) > 0 )
    {
        echo "Pilot insert failed, already exists <br>";
    }
    else
    {
        $query = "	INSERT INTO tblExtPilot (
						pilFAI, pilCIVL, pilLastName, pilFirstName,
						pilSex, pilGliderBrand, pilGlider,
						gliGliderCert, pilNat, pilXContestUser
					)
					VALUES
						(
							$fai, $civl, '$lname', '$fname', '$sex',
							'$brand', '$glider', '$cert', $nat,
							'$xcid'
						)";
        mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot insert failed: ' . mysqli_connect_error());
    }
}

if (reqexists('bulkadd'))
{
    $out = '';
    $retv = 0;
    $name = reqsval('name');

    $copyname = tempnam(FILEDIR, $name . "_");
    copy($_FILES['bulkpilots']['tmp_name'], $copyname);
    //echo "bulk_pilot_import.pl $copyname<br>";
    chmod($copyname, 0644);

//     exec(BINDIR . "bulk_pilot_import.pl $copyname", $out, $retv);
//     foreach ($out as $txt)
//     {
//         echo "$txt<br>\n";
//     }

	# Using new Python3 script
	$command = "python3 " . BINDIR . "bulk_pilot_import.py $copyname";
	$message .= "Bulk Add Result: <br />";
	//$message .= "Command: $command <br />";
	$content .= nl2br(shell_exec($command));

}

if (reqexists('update'))
{
    $id = reqival('update');
    $fai = reqival("fai$id");
    $lname = reqsval("lname$id");
    $fname = reqsval("fname$id");
    $sex = reqsval("sex$id");
    $nat = reqsval("nation$id");
    $brand = reqsval("brand$id");
    $glider = reqsval("glider$id");
    $cert = reqsval("cert$id");
	$xcid = reqsval("xcontest$id");

	//echo " parameters: Id $id , FAI $fai , wing $brand $glider $cert , user $xcid \n";

    $query = "SELECT * FROM PilotView WHERE pilFAI=$fai AND pilPk<>$id";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot update select failed: ' . mysqli_connect_error());
    if (($fai < 1000 or mysqli_num_rows($result) > 0) and $fai != 0)
    {
        echo "Pilot update failed, HGFA/FAI number ($fai) already exists or is too low (<1000) <br>";
    }
    else
    {
        $query = "	UPDATE
						tblExtPilot
					SET
						pilFAI = $fai,
						pilLastName = '$lname',
						pilFirstName = '$fname',
						pilSex = '$sex',
						pilNat = '$nat',
						pilGliderBrand = '$brand',
						pilGlider = '$glider',
						gliGliderCert = '$cert',
						pilXContestUser = '$xcid'
					WHERE
						pilPk = $id";
		//echo $query . '\n';
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot update failed: ' . mysqli_connect_error());
    }
}

if (reqexists('delete'))
{
    check_admin('admin',$usePk,-1);
    $id = reqival('delete');
    $query = "select count(*) as numtracks from tblTrack where pilPk=$id";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot delete check failed: ' . mysqli_connect_error());
    $row = mysqli_fetch_assoc($result);
    if ((0+$row['numtracks']) > 0)
    {
        $message .= 'Unable to delete pilot as they have associated tracks <br />';
    }
    else
    {
        $query = "delete from tblExtPilot where pilPk=$id";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot delete failed: ' . mysqli_connect_error());
        $message .= "Pilot with ID $id DELETED <br />";
    }
}

if ($ozimp)
{
    echo "<form enctype=\"multipart/form-data\" action=\"pilot_admin.php?comPk=$comPk&ozimp=$ozimp\" name=\"trackadmin\" method=\"post\">";
}
else
{
    echo "<form enctype=\"multipart/form-data\" action=\"pilot_admin.php?comPk=$comPk&cat=$cat\" name=\"trackadmin\" method=\"post\">";
}

$country = get_countrylist($link, 'nation', 380);
echo "<input type=\"hidden\" name=\"MAX_FILE_SIZE\" value=\"1000000000\">";
echo "HGFA/FAI: " . fin('fai', '', 5);
echo "CIVL: " . fin('civl', '', 5);
echo "LastName: " . fin('lname', '', 10);
echo "FirstName: " . fin('fname', '', 10);
echo "Sex: " . fselect('sex', 'M', [ 'M' => 'M', 'F' => 'F' ]);
echo "$country";
echo "Xcontest ID:" . fin('xcontest', '' ,10);
echo fis('addpilot', "Add Pilot", 5);
echo "<br>";
echo "CSV (FAI#, First, Last, Nat, Sex): <input type=\"file\" name=\"bulkpilots\">";
echo fis('bulkadd', 'Bulk Submit', 5);

if ($ozimp)
{
    echo "<p>";
    $comparr = [];
    $xmltxt = file_get_contents("http://ozparaglidingcomps.com/compListXml.php");
    $xml = new SimpleXMLElement($xmltxt);
    foreach ($xml->comp as $comp)
    {
        $comparr["" . $comp->comp_name] = $comp->comp_id;
    }
    echo fselect('compid', '', $comparr);
    echo fib('checkbox', 'paidonly', '', '') . "Paid Only";
    echo fib('checkbox', 'handicap', '', '') . "Generate Handicap";
    echo fis('addcomp', 'Import Comp', '');
}

echo "<hr>";

# Messages field
if ( $message !== '')
{
	echo "<h4> <span style='color:red'>$message</span> </h4>" . PHP_EOL;
	echo "<br />" . PHP_EOL;
	echo "<hr />" . PHP_EOL;
}

# Content field
if ( $content !== '')
{
	echo "$content" . PHP_EOL;
	echo "<br />" . PHP_EOL;
	echo "<hr />" . PHP_EOL;
}

echo "<h2>Pilots by Name: $cat</h2><p>";
$letters = [  'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
        'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
        'Y', 'Z' ];
echo "<table><tr>";
$count = 0;
foreach ($letters as $let)
{
    $count++;
    echo "<td><a href=\"pilot_admin.php?cat=$let\">$let</a>&nbsp;</td>";
//     if ($count % 26 == 0)
//     {
//             echo "</tr><tr>";
//     }
}
echo "</tr></table><br />\n";
if ($cat != '')
{
    echo "<ol>";
    $count = 1;
    $sql = "SELECT P.* FROM PilotView P where P.pilLastName like '$cat%' order by P.pilLastName";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Pilot select failed: ' . mysqli_connect_error());

    while ($row = mysqli_fetch_assoc($result))
    {
        $id = $row['pilPk'];
        $lname = $row['pilLastName'];
        $fname = $row['pilFirstName'];
        $fai = $row['pilFAI'];
        $civlid = $row['pilCIVL'];
        $sex = ($row['pilSex']);
        $nat = $row['pilNat'];
        $brand = $row['pilGliderBrand'];
        $glider = $row['pilGlider'];
        $cert = $row['gliGliderCert'];
		$xcid = $row['pilXContestUser'];

		# Get Country Code
		$countrycode = get_countrycode($link, $nat);

		# Let edit or Delete onlu if pilot is in Ext Table, not in CB db
		if ( $id > 9999 )
		{
			echo "<li><button type=\"submit\" name=\"delete\" value=\"$id\">del</button>";
			echo "<button type=\"submit\" name=\"update\" value=\"$id\">up</button>";
			# Get Countries list
			$country = get_countrylist($link, "nation$id", $nat);
        }
        else
        {
			echo "<li><button type=\"submit\" name=\"delete\" value=\"$id\" disabled>del</button>";
			echo "<button type=\"submit\" name=\"update\" value=\"$id\" disabled>up</button>";
			# Get Country Code
			$countrycode = get_countrycode($link, $nat);
			$country = "<input type=\"text\" name=\"nation$id\" value=\"$countrycode\" size=11>";
        }
        //echo " $hgfa $name ($sex).<br>\n";
        echo "<input type=\"text\" name=\"fai$id\" value=\"$fai\" size=7>";
        echo "<input type=\"text\" name=\"civl$id\" value=\"$civlid\" size=5>";
        echo "<input type=\"text\" name=\"lname$id\" value=\"$lname\" size=16>";
        echo "<input type=\"text\" name=\"fname$id\" value=\"$fname\" size=16>";
        echo "<input type=\"text\" name=\"sex$id\" value=\"$sex\" size=3>";
        //echo "<input type=\"text\" name=\"nation$id\" value=\"$nat\" size=4>";
        echo "$country";
        echo "<input type=\"text\" name=\"brand$id\" value=\"$brand\" size=10>";
        echo "<input type=\"text\" name=\"glider$id\" value=\"$glider\" size=12>";
        echo "<input type=\"text\" name=\"cert$id\" value=\"$cert\" size=4>";
		echo "<input type=\"text\" name=\"xcontest$id\" value=\"$xcid\" size=12> </li>";
        # echo a delete button ...

        $count++;
    }
    echo "</ol>";
}


echo "</form>";

tpfooter($file);

?>
