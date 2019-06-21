<?php


// function accept_track($link, $pilPk, $comPk, $tasPk)
// {
//     $filename = basename($_FILES['userfile']['name']);
//     //echo "file name: $filename or " . $_FILES['userfile']['name'];
//
//     # Copy the upload so I can use it later ..
//     $dte = date("Ymd_Hms");
//     $yr = date("Y");
//
//     # Get Comp short name
//     $query = "  SELECT
//                     LOWER(T.`comCode`) AS comCode,
//                     LOWER(T.`tasCode`) AS tasCode,
//                     YEAR(C.`comDateFrom`) AS comYear,
//                     DATE_FORMAT(T.`tasdate`, '%Y%m%d') AS tasDate,
//                     CONCAT_WS(
//                         '_',
//                         LOWER(P.`pilFirstName`),
//                         LOWER(P.`pilLastName`)
//                     ) AS pilName
//                 FROM
//                     `PilotView` P,
//                     `TaskView` T
//                 JOIN `tblCompetition` C USING(`comPk`)
//                 WHERE
//                     T.`tasPk` = $tasPk AND P.`pilPk` = $pilPk
//                 LIMIT 1";
//     //echo "query: <br> $query <br>";
//     $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Comp Short name failed: ' . mysqli_connect_error());
//     $row = mysqli_fetch_object($result);
//     $cname = $row->comCode;
//     $tname = $row->tasCode;
//     $pname = $row->pilName;
//     $year  = $row->comYear;
//     $tdate = $row->tasDate;
//
//     //echo "params: $cname $tname $pname $year $tdate <br><br>";
//
//     # Using /tracks/Year/CompShortName/TaskShortName_Date as repository
//     //$copyname = FILEDIR . $year . "/" . $cname . "/" . $tname . "_" . $dte;
//     $taskdir = FILEDIR . $year . "/" . $cname . "/" . $tname . "_" . $tdate;
//     if ( !file_exists($taskdir) )
//     {
//         mkdir($taskdir, 0755, true);
//     }
//     # renaming file as pilot_name_date_index.igc
//     $filename = $pname.'_'.$dte;
//     # check if pilot has already a file for this task, and use appropriate index
//     $index = count(glob($taskdir.'/'.$filename.'*') ) + 1;
//     $filename .= "_$index.igc";
//     $file = $taskdir.'/'.$filename;
//     # copying file from tmp to correct folder
//     copy($_FILES['userfile']['tmp_name'], $file);
//     chmod($file, 0644);
//     //echo "file: $file <br>";
//
//     # Process the file
//     $traPk = process_track($pilPk, $file, $comPk, $tasPk);
//
//     return $traPk;
// }

function accept_track($link, $pilPk, $comPk, $tasPk)
{
    // $fh = fopen("/tmp/submit24", "w");
    // foreach ($_REQUEST as $k=>$v)
    // {
    //     fwrite($fh, "key=$k, value=$v\n");
    // }
    // foreach ($_FILES as $k=>$v)
    // {
    //     fwrite($fh, "key=$k:\n");
    //     foreach ($v as $key=>$val)
    //     {
    //         fwrite($fh, "    key=$key, value=$val\n");
    //     }
    // }
    // fclose($fh);
    $traPk = 0;
    $filename = basename($_FILES['userfile']['name']);
    $tempnm = $_FILES['userfile']['tmp_name'];

    // $command = "python3 " . BINDIR . "track_reader.py $tasPk '$tempnm' '$filename' $pilPk > " . BINDIR . 'log/track_read.txt 2>&1 & echo $!; ';
    $command = "python3 " . BINDIR . "track_reader.py $tasPk '$tempnm' '$filename' $pilPk ";
    $pid = exec($command, $out, $retv);

    foreach ($out as $row)
    {
        // echo $row . PHP_EOL;
        if (substr_compare("traPk=6", $row, 0, 6) == 0)
        {
            $traPk = 0 + substr($row, 6);
            //echo $row . PHP_EOL;
            break;
        }
    }

    return $traPk;
}

// function upload_track($pilPk, $file, $comPk, $tasPk)
// {
//     # Let the Perl program do it!
//     $out = '';
//     $retv = 0;
//     $traPk = 0;
//     exec(BINDIR . "add_track.pl $pilPk $file $comPk $tasPk", $out, $retv);
//
//     if ($retv)
//     {
//         echo "<b>Failed to upload your track: </b>";
//         if ($out)
//         {
//             foreach ($out as $txt)
//             {
//                 echo "$txt<br>\n";
//             }
//         }
//         else
//         {
//             echo " it appears to have been submitted previously.<br>\n";
//         }
//         echo "Contact $contact if this was a valid track.<br>\n";
//         echo "</div></body></html>\n";
//         exit(0);
//     }
//
//     foreach ($out as $row)
//     {
//         if (substr_compare("traPk=6", $row, 0, 6) == 0)
//         {
//             $traPk = 0 + substr($row, 6);
//             break;
//         }
//     }
//
//
//     return $traPk;
// }


function process_track($pilPk, $file, $comPk, $tasPk)
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
    $query = "  SELECT
                    P.*,
                    FC.forMinDistance * 1000 AS minDistance,
                    T.tasStartTime,
                    T.tasDate
                FROM
                    PilotView P,
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
