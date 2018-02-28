<?php
require_once 'authorisation.php';
require_once 'format.php';

// Just get all the submitted variables and store for reference
$fh = fopen("/tmp/live24", "w");
foreach ($_REQUEST as $k=>$v)
{
    fwrite($fh, "key=$k, value$v\n");
}
fclose($fh);


// The standard variables
$op = reqsval('op');

$link = db_connect();

$username = reqsval('username');
$password = reqsval('password');
$session = reqsval('sessionID');

$sql = "select pilPk from tblPilot where pilLastName='$username' and pilHGFA='$password'";
$result = mysqli_query($link, $sql);

#if ($op eq 'login')
#{
    // my $a = floor(random(System.currentTimeMillis()));
    //int rnd=a.nextInt();
    // we make an int with leftmost bit=1 ,
    // the next 7 bits random 
    // (so that the same userID can have multiple active sessions)
    // and the next 3 bytes the userID
    //rnd=( rnd &  0x7F000000 ) | ( userID & 0x00ffffff) | 0x80000000;                    
#}


if ($op == 'submit')
{
    $user = reqsval('liveUsername');
    $id = reqsval('liveUserID');
    $glidertype = reqival('gliderType');
    $glider = reqival('gliderName');
    $platform = reqsval('platform');
    $gpsmodel = reqsval('gps');
    $progname = reqsval('programName');
    $progversion = reqsval('programVersion');
    $comments = reqival('comments');
    $userurl = reqsval('url');
    $server = reqival('leonardoServer');

    // Assume full re-upload
    $format = $_REQUEST['format'];
    $compressed = reqival('compressed');
    $timestamp = reqival('firstTM');

    if ($compressed)
    {
        // reinflate data ..
        $format = http_inflate($format);
    }

    // Now write the differential format
    $dte = date("Y-m-d_Hms");
    $yr = date("Y");
    $copyname = FILEDIR . $yr . "/" . $name . "_" . $hgfa . "_" . $dte;

    $fh = fopen($copyname, "w");
    fwrite($fh, "LIVE24\n");
    fwrite($fh, "time=$timestamp\n");
    fwrite($fh, $format);
    fclose($fh);

    $out = '';
    $retv = 0;
    if (!$comments)
    {
        $comments = 1;
    }
    exec(BINDIR . "add_track.pl $pilPk $copyname $comments", $out, $retv);
    foreach ($out as $row)
    {  
        if (substr_compare("traPk=6", $row, 0, 6) == 0)
        {  
            $traPk = 0 + substr($row, 6);
            break;
        }
    }

    // Ok - update glider and any other info we have
    print "added track ($traPk): $out\n";
}
else
{
    print "Unknown operation: $op<br>\n";
}

?>

