<?php

function accept_track($link, $pilPk, $comPk, $tasPk)
{
    $traPk = 0;
    $filename = basename($_FILES['userfile']['name']);
    $tempnm = $_FILES['userfile']['tmp_name'];

    // $command = "python3 " . BINDIR . "track_reader.py $tasPk '$tempnm' '$filename' $pilPk > " . BINDIR . 'log/track_read.txt 2>&1 & echo $!; ';
    $command = "python3 " . BINDIR . "track_reader.py $tasPk '$tempnm' '$filename' $pilPk ";
    $pid = exec($command, $out, $retv);

    foreach ($out as $row) {
        if (substr_compare("traPk=6", $row, 0, 6) == 0) {
            $traPk = 0 + substr($row, 6);
            break;
        }
    }

    return $traPk;
}

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
    $tarPk = 0;
    $command = "python3 " . BINDIR . "set_pilot_status.py $tasPk $pilPk '$resulttype' ";
    echo ($command);
    $pid = exec($command, $out, $retv);

    foreach ($out as $row)
    {
        // echo $row . PHP_EOL;
        if (substr_compare("tarPk=6", $row, 0, 6) == 0)
        {
            $tarPk = 0 + substr($row, 6);
            //echo $row . PHP_EOL;
            break;
        }
    }

    return $tarPk;
}

?>
