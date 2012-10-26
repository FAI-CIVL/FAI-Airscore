<?php
require 'authorisation.php';
require 'format.php';
require 'hc.php';

$comPk = reqival('comPk');
$embed = reqsval('embed');
$link = db_connect();
$offerall = 0;


if ($comPk < 2)
{
    $offerall = 1;
    $comPk=1;
}


$comUnixTo = time() - (int)substr(date('O'),0,3)*60*60;
$query = "select *, unix_timestamp(date_sub(comDateTo, interval ComTimeOffset hour)) as comUnixTo  from tblCompetition where comPk=$comPk";
$result = mysql_query($query) or die('Query failed: ' . mysql_error());
$title = 'highcloud.net';
$comContact = '';
$comEntryRestrict = 'open';
if ($row=mysql_fetch_array($result))
{
    $title = $row['comName'];
    $comType = $row['comType'];
    $comClass = $row['comClass'];
    $comContact = $row['comContact'];
    $comUnixTo = $row['comUnixTo'];
    $comEntryRestrict = $row['comEntryRestrict'];
}

if ($comContact == '')
{
    $comContact = 'your competition organiser';
}

if (array_key_exists('foo', $_REQUEST))
{
    $fh = fopen("/tmp/submit24", "w");
    foreach ($_REQUEST as $k=>$v)
    {
        fwrite($fh, "key=$k, value$v\n");
    }
    fclose($fh);

    echo "<title>Track Accepted</title>\n";
    $id = accept_track($comUnixTo, $comContact, $comEntryRestrict);
    redirect("tracklog_map.php?trackid=$id&comPk=$comPk&ok=1");
    exit(0);
}
if ($embed == '')
{
    hcheader($title, 1, "");
    echo "<div id=\"content\">";
    echo "<div id=\"text\">";

}
else
{
    echo "<html><head>";
    echo "<link HREF=\"$embed\" REL=\"stylesheet\" TYPE=\"text/css\">\n";
    echo "</head><body><div id=\"track_submit\">\n";
}
?>
<h1>Tracklog Submission</h1>
Download your GPS track from your GPS using one of the free 
programs shown on the right.  Then you're ready to upload the 
.IGC file created to this website using the form here!
<br><br>
<?php
function upload_track($file,$pilPk,$contact)
{
    # Let the Perl program do it!
    $out = '';
    $retv = 0;
    $traPk = 0;
    exec(BINDIR . "igcreader.pl $file $pilPk", $out, $retv);

    if ($retv)
    {
        echo "<b>Failed to upload your track, it appears to have been submitted previously.</b><br>\n";
        echo "Contact $contact if this was a valid track.<br>\n";
        foreach ($out as $txt)
        {
            echo "$txt<br>\n";
        }
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

function accept_track($until, $contact, $restrict)
{
    //$file = addslashes($_REQUEST['userfile']);
    $hgfa = addslashes($_REQUEST['hgfanum']);
    $name = addslashes(strtolower($_REQUEST['lastname']));
    $route = reqival('route');
    $comid = reqival('comid');

    $link = db_connect();
    $query = "select pilPk, pilHGFA from tblPilot where pilLastName='$name'";
    $result = mysql_query($query) or die('Query failed: ' . mysql_error());

    $member = 0;
    while ($row=mysql_fetch_array($result))
    {
        if ($hgfa == $row['pilHGFA'])
        {
            $pilPk = $row['pilPk'];
            $member = 1;
        }
    }

    if ($restrict == 'registered')
    {
        $query = "select * from tblRegistration where comPk=$comid and pilPk=$pilPk";
        $result = mysql_query($query) or die('Registration query failed: ' . mysql_error());
        if (mysql_num_rows($result) == 0)
        {
            $member = 0;
        }
    }

    $gmtimenow = time() - (int)substr(date('O'),0,3)*60*60;
    if ($gmtimenow > ($until + 7*24*3600))
    {
        echo "<b>The submission period for tracks has closed ($until).</b><br>\n";
        echo "Contact $contact if you're having an access problem.<br>\n";
        echo "</div></body></html>\n";
        exit(0);
    }
    if ($member == 0)
    {
        echo "<b>Only registered pilots may submit tracks.</b><br>\n";
        echo "Contact $contact if you're having an access problem.<br>\n";
        echo "</div></body></html>\n";
        exit(0);
    }

    // Copy the upload so I can use it later ..
    $dte = date("Y-m-d_Hms");
    $yr = date("Y");
    $copyname = FILEDIR . $yr . "/" . $name . "_" . $hgfa . "_" . $dte;
    copy($_FILES['userfile']['tmp_name'], $copyname);
    chmod($copyname, 0644);

    // Process the file
    $maxPk = upload_track($_FILES['userfile']['tmp_name'], $pilPk, $comContact);
    $tasPk = 'null';
    $tasType = '';
    $comType = '';
    $turnpoints = '';

    if ($route > 0)
    {
        $tasPk = $route;
        $query = "select T.tasPk, T.tasTaskType, C.comType from tblTask T, tblTrack TL, tblCompetition C where C.comPk=T.comPk and T.comPk=$comid and TL.traPk=$maxPk and T.tasPk=$tasPk";
        $result = mysql_query($query) or die('Query failed: ' . mysql_error());
        if (mysql_num_rows($result) > 0)
        {
            //$tasPk=mysql_result($result,0,0);
            $tasType=mysql_result($result,0,1);
            $comType=mysql_result($result,0,2);
        }
        // should check date of track is within tasStart/tasFinish time
    }
    else
    {
        $query = "select T.tasPk, T.tasTaskType, C.comType from tblTask T, tblTrack TL, tblCompetition C where C.comPk=T.comPk and T.comPk=$comid and TL.traPk=$maxPk and TL.traStart > date_sub(T.tasDate, interval C.comTimeOffset hour) and TL.traStart < date_add(T.tasDate, interval (24-C.comTimeOffset) hour)";
        $result = mysql_query($query) or die('Query failed: ' . mysql_error());
        if (mysql_num_rows($result) > 0)
        {
            $tasPk=mysql_result($result,0,0);
            $tasType=mysql_result($result,0,1);
            $comType=mysql_result($result,0,2);
        }
    }

    $query = "insert into tblComTaskTrack (comPk,tasPk,traPk) values ($comid,$tasPk,$maxPk)";
    $result = mysql_query($query) or die('ComTaskTrack failed: ' . mysql_error());

    $out = '';
    $retv = 0;

    if ($tasPk != 'null')
    {   
        $turnpoints = '3';
        if ($tasType == 'free')
        {
            $turnpoints = '0';
        }

        exec(BINDIR . "optimise_flight.pl $maxPk $tasPk $turnpoints", $out, $retv);
    }
    else
    {
        if ($comType == 'Free')
        {
            $turnpoints = '0';
            exec(BINDIR . "optimise_flight.pl $maxPk 0 $turnpoints", $out, $retv);
        }
        else
        {
            echo "optimise_flight.pl $maxPk<br>";
            exec(BINDIR . "optimise_flight.pl $maxPk", $out, $retv);
        }
    }

    if ($retv)
    {
        echo "<b>Failed to optimise your track correctly.</b><br>\n";
        echo "Contact $contact if this was a valid track.<br>\n";
        foreach ($out as $txt)
        {
            echo "$txt<br>\n";
        }
        echo "</div></body></html>\n";
        exit(0);
    }

    $glider = addslashes($_REQUEST['glider']);
    $dhv = addslashes($_REQUEST['dhv']);
    $query = "update tblTrack set traGlider='$glider', traDHV='$dhv' where traPk=$maxPk";
    $result = mysql_query($query) or die('Update tblTrack failed: ' . mysql_error());

    if ($tasPk != 'null') 
    {
        if ($tasType == 'speedrun' || $tasType == 'race' || $tasType =='speedrun-interval')
        {
            task_score($maxPk);
        }
        elseif ($tasType == 'airgain')
        {
            exec(BINDIR . "airgain_verify.pl $maxPk $comid $tasPk", $out, $retv);
        }
    }

    return $maxPk;
}

echo "<form enctype=\"multipart/form-data\" action=\"submit_track.php?comPk=$comPk\" method=\"post\">";
echo '
<input type="hidden" name="MAX_FILE_SIZE" value="1000000000">
';

$igcarr = array();
if ($offerall)
{
    $comps = array();
    $query = "select * from tblCompetition where curdate() < date_add(comDateTo, interval 3 day)";
    $result = mysql_query($query) or die('Query failed: ' . mysql_error());
    while($row = mysql_fetch_array($result))
    {
        $comName = $row['comName'];
        $compid = $row['comPk'];
        $comps[$comName] = $compid;
    }

    $igcarr[] = array('Competition', fselect('comid', $comPk, $comps));
}
else
{
    echo("<input type=\"hidden\" name=\"comid\" value=\"$comPk\">");
}

if ($comType == 'Route')
{
    $query = "select * from tblTask where comPk=$comPk";
    $result = mysql_query($query) or die('Route query failed: ' . mysql_error());
    $routes = array();
    while($row = mysql_fetch_array($result))
    {
        $routes[$row['tasName']] = $row['tasPk'];
    }

    //echo '</td><td>';
    $igcarr[] = array('Route', fselect('route', 0, $routes));
}

$igcarr[] = array('Send IGC file', "<input name=\"userfile\" type=\"file\">");
$igcarr[] = array('HGFA Number', "<input name=\"hgfanum\" type=\"text\">");
$igcarr[] = array('Last Name', "<input name=\"lastname\" type=\"text\">");

if ($comClass == 'PG')
{
    $classarr = fselect('dhv', 'competition', array('novice' => '1', 'fun' => '1/2', 'sports' => '2', 'serial' => '2/3', 'competition' => 'competition' ));
}
elseif ($comClass == 'HG')
{
    $classarr = fselect('dhv', 'open', array('floater' => 'floater', 'kingpost' => 'kingpost', 'open' => 'open', 'rigid' => 'rigid' ));
}
else 
{
    $classarr = fselect('dhv', '2', array('pg-novice' => '1', 'pg-fun' => '1/2', 'pg-sport' => '2', 'pg-serial' => '2/3', 'pg-comp' => 'competition', 'hg-floater' => 'floater', 'hg-kingpost' => 'kingpost', 'hg-open' => 'open', 'hg-rigid' => 'rigid' ));
}
$igcarr[] = array('Glider', '<input name="glider" type="text">', $classarr);

echo ftable($igcarr, '', '', '');
echo '<br><center><input type="submit" name="foo" value="Send Tracklog"></center>';

if ($embed == '') 
{   
    echo "</div>";

    echo "<div id=\"sideBar\">";
    echo "<h1>GPS Downloaders</h1>"; 
    $gpsarr = array(
        "<a href=\"http://www.gethome.no/stein.sorensen/body_gpsdump.htm\">GPSDump</a>",
        "<a href=\"http://flighttrack.sourceforge.net/\">FlightTrack (MacOS X)</a>",
        "<a href=\"http://www.gpsbabel.org/\">GPS Babel</a>",
        "<b><a href=\"http://www.freethinker.com/iphone/livetrack24/index.html\">Livetrack 24 (*iOS*)</a></b>",
        );
    echo fnl($gpsarr);
    hcopencomps($link);
    hcclosedcomps($link);
    echo "</div>";
    hcimage($link,$comPk);
    hcfooter();
    echo "</div>";

}
else
{
    echo "</div>";
}
mysql_close($link);
echo "</body></html>\n";
?>

