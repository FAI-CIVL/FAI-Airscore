<?php

function accept_track($link, $pilPk, $comPk, $tasPk)
{
    $filename = basename($_FILES['userfile']['name']);
    //echo "file name: $filename or " . $_FILES['userfile']['name'];

    // Copy the upload so I can use it later ..
    $dte = date("Y-m-d_Hms");
    $yr = date("Y");
    $copyname = FILEDIR . $yr . "/" . $pilPk . "_" . $tasPk . "_" . $dte;
    mkdir($copyname, 0755, true);
    copy($_FILES['userfile']['tmp_name'], $copyname . basename($_FILES['userfile']['tmp_name']));
    chmod($copyname . basename($_FILES['userfile']['tmp_name']), 0644);
    $file = $copyname . basename($_FILES['userfile']['tmp_name']);

    // Process the file
    $traPk = upload_track($pilPk, $file, $comPk, $tasPk);

    return $traPk;
}

function upload_track($pilPk, $file, $comPk, $tasPk)
{
    # Let the Perl program do it!
    $out = '';
    $retv = 0;
    $traPk = 0;
    exec(BINDIR . "add_track.pl $pilPk $file $comPk $tasPk", $out, $retv);

    if ($retv)
    {
        echo "<b>Failed to upload your track: </b>";
        if ($out)
        {
            foreach ($out as $txt)
            {
                echo "$txt<br>\n";
            }
        }
        else
        {
            echo " it appears to have been submitted previously.<br>\n";
        }
        echo "Contact $contact if this was a valid track.<br>\n";
        echo "</div></body></html>\n";
        exit(0);
    }

    foreach ($out as $row)
    {
        if (substr_compare("traPk=6", $row, 0, 6) == 0)
        {
            $traPk = 0 + substr($row, 6);
            break;
        }
    }


    return $traPk;
}

function task_score($traPk)
{
    # Let the Perl program do it!
    $out = '';
    $retv = 0;
    exec(BINDIR . "track_verify_sr.pl $traPk", $out, $retv);

    return $retv;
}


function set_status($link, $pilPk, $comPk, $tasPk, $resulttype)
{
	#Get pilot details
	$query = "	SELECT 
					P.*, 
					FC.forMinDistance * 1000 AS minDistance, 
					T.tasStartTime, 
					T.tasDate 
				FROM 
					tblPilot P, 
					tblTask T 
					JOIN tblForComp FC USING (comPk) 
				WHERE 
					P.pilPk = $pilPk  
					AND T.tasPk = $tasPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Pilot profile failed: ' . mysqli_connect_error());
    $pilot = mysqli_fetch_object($result);
    $glider = $pilot->pilGliderBrand . ' ' . $pilot->pilGlider;
    $dhv = $pilot->gliGliderCert;
    $tasDate = $pilot->tasDate;
    $flown = 0.0;
    if ( $resulttype == 'mindist' )
    {
    	$flown = $pilot->minDistance;
    }
    $query = "insert into tblTrack (pilPk,traGlider,traDHV,traDate,traStart,traLength) values ($pilPk,'$glider','$dhv','$tasDate','$tasDate',$flown)";
	mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Track insert result failed: ' . mysqli_connect_error());

	$traPk = mysqli_insert_id($link);

	$query = "insert into tblTaskResult (tasPk,traPk,tarDistance,tarResultType) values ($tasPk,$traPk,$flown,'$resulttype')";
	mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Insert result failed: ' . mysqli_connect_error());
	
	$query = "INSERT INTO tblComTaskTrack (comPk, tasPk, traPk) VALUES ($comPk, $tasPk, $traPk)";
	mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Insert comtasktrack values failed: ' . mysqli_connect_error());
	
	$out = '';
	$retv = 0;
	exec(BINDIR . "task_score.pl $tasPk", $out, $retv);
}




?>
