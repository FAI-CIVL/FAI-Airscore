<?php
require_once 'authorisation.php';
require_once 'format.php';
require_once 'hc.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

header('Cache-Control: no-cache, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');

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
//$result = mysql_query($query) or die('Query failed: ' . mysql_error());
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
$title = 'highcloud.net';
$comContact = '';
$comEntryRestrict = 'open';
//if ($row=mysql_fetch_array($result))
if ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $title = $row['comName'];
    $comType = $row['comType'];
    $comClass = $row['comClass'];
    $comContact = $row['comContact'];
    $comUnixTo = $row['comUnixTo'];
    $comEntryRestrict = $row['comEntryRestrict'];
}

$freepin = 0;
$query = "select * from tblTask where comPk=$comPk and tasTaskType='free-pin'";
// $result = mysql_query($query);
$result = mysqli_query($link, $query);
//if (mysql_num_rows($result) > 0)
if (mysqli_num_rows($result) > 0)
{
   $freepin = 1; 
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
<p>Download your GPS track from your GPS using one of the free 
programs shown on the right.  Then you're ready to upload the 
.IGC file created to this website using the form here!</p>
<br><br>
<?php
//function upload_track($file,$pilPk,$contact)
function upload_track($hgfa, $file, $comid, $tasPk, $contact)
{
    # Let the Perl program do it!
    $out = '';
    $retv = 0;
    $traPk = 0;
    #exec(BINDIR . "igcreader.pl $file $pilPk", $out, $retv);
    exec(BINDIR . "add_track.pl $hgfa $file $comid $tasPk", $out, $retv);

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

function accept_track($until, $contact, $restrict)
{
    //$file = addslashes($_REQUEST['userfile']);
    $hgfa = addslashes($_REQUEST['hgfanum']);
    $name = addslashes(strtolower(trim($_REQUEST['lastname'])));
    $route = reqival('route');
    $comid = reqival('comid');

    $link = db_connect();
    $query = "select pilPk, pilHGFA from tblPilot where pilLastName='$name'";
//    $result = mysql_query($query) or die('Query failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());

    $member = 0;
//    while ($row=mysql_fetch_array($result))
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        if ($hgfa == $row['pilHGFA'])
        {
            $pilPk = $row['pilPk'];
            $member = 1;
        }
    }

#    if ($restrict == 'registered')
#    {
#        $query = "select * from tblRegistration where comPk=$comid and pilPk=$pilPk";
#        $result = mysql_query($query) or die('Registration query failed: ' . mysql_error());
#        if (mysql_num_rows($result) == 0)
##        {
#            $member = 0;
#        }
#    }
##

#changed 7 day track submission limit to 700 days for historical task testing

    $gmtimenow = time() - (int)substr(date('O'),0,3)*60*60;
    if ($gmtimenow > ($until + 700*24*3600))
    {
        echo "<b>The submission period for tracks has closed ($until) ($gmtimenow).</b><br>\n";
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
    mkdir($copyname, 0755, true);
    copy($_FILES['userfile']['tmp_name'], $copyname . basename($_FILES['userfile']['tmp_name']));
    chmod($copyname . basename($_FILES['userfile']['tmp_name']), 0644);

    // Process the file
    //$maxPk = upload_track($_FILES['userfile']['tmp_name'], $pilPk, $comContact);
    $maxPk = upload_track($hgfa, $_FILES['userfile']['tmp_name'], $comid, $route, $contact);

    $tasPk = 'null';
    $tasType = '';
    $comType = '';
    $turnpoints = '';

    $out = '';
    $retv = 0;

    $glider = reqsval('glider');
    $dhv = reqsval('dhv');
    $safety = reqsval('pilotsafety');
    $quality = reqival('pilotquality');
    $query = "update tblTrack set traGlider='$glider', traDHV='$dhv', traSafety='$safety', traConditions='$quality' where traPk=$maxPk";
//    $result = mysql_query($query) or die('Update tblTrack failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Update tblTrack failed: ' . mysqli_connect_error());

    return $maxPk;
}

echo "<form enctype=\"multipart/form-data\" action=\"submit_track.php?comPk=$comPk\" method=\"post\">";
echo '
<input type="hidden" name="MAX_FILE_SIZE" value="1000000000">
';

$igcarr = [];
if ($offerall)
{
    $comps = [];
    $comps['-- select an option --'] = '';
    
    # query commented to be able to make TESTS
    #$query = "select * from tblCompetition where curdate() < date_add(comDateTo, interval 3 day) and comName not like '%test%' order by comName";
    $query = "select * from tblCompetition order by comName";
    
//    $result = mysql_query($query) or die('Query failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
//    while($row = mysql_fetch_array($result))
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $comName = $row['comName'];
        $compid = $row['comPk'];
        $comps[$comName] = $compid;
    }

    $igcarr[] = ['Competition', fselect('comid', 0, $comps)];
}
else
{
    echo("<input type=\"hidden\" name=\"comid\" value=\"$comPk\">");
}

if ($comType == 'Route')
{
    $query = "select * from tblTask where comPk=$comPk";
//    $result = mysql_query($query) or die('Route query failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Route query failed: ' . mysqli_connect_error());
    $routes = [];
//    while ($row = mysql_fetch_array($result, MYSQL_ASSOC))
    while ($row = mysqli_fetch_assoc($result))
    {
        $routes[$row['tasName']] = $row['tasPk'];
    }

    //echo '</td><td>';
    $igcarr[] = array('Route', fselect('route', 0, $routes));
}

if ($freepin)
{
    $igcarr[] = array('Send IGC file', "<input name=\"userfile\" type=\"file\">", '<center>or</center>', "<a href=\"submit_pin.php?comPk=$comPk\"><b>PIN drop</b></a>");
}
else
{
    $igcarr[] = array('Send IGC file', "<input name=\"userfile\" type=\"file\">");
}
$igcarr[] = [ 'HGFA Number', "<input name=\"hgfanum\" type=\"text\">" ];
$igcarr[] = [ 'Last Name', "<input name=\"lastname\" type=\"text\">" ];

if ($comClass == 'PG')
{
    $classarr = fselect('dhv', '2/3', [ 'novice' => '1', 'fun' => '1/2', 'sports' => '2', 'serial' => '2/3', 'competition' => 'competition' ]);
}
elseif ($comClass == 'HG')
{
    $classarr = fselect('dhv', 'open', [ 'floater' => 'floater', 'kingpost' => 'kingpost', 'open' => 'open', 'rigid' => 'rigid' ]);
}
else 
{
    $classarr = fselect('dhv', '2', [ 'pg-novice' => '1', 'pg-fun' => '1/2', 'pg-sport' => '2', 'pg-serial' => '2/3', 'pg-comp' => 'competition', 'hg-floater' => 'floater', 'hg-kingpost' => 'kingpost', 'hg-open' => 'open', 'hg-rigid' => 'rigid' ]);
}
$igcarr[] = [ 'Glider', '<input name="glider" type="text">', $classarr ];

if ($comType == 'RACE' || $comType == 'RACE-handicap' || $comType == 'Team-RACE')
{
    $igcarr[] = [ 'Conditions', fselect( 'pilotsafety', 'safe', [ 'safe' => 'safe', 'not safe for me' => 'maybe', 'not safe for all' => 'unsafe' ]), fselect('pilotquality', 5, [ 'completely unfair' => 1, 'random racing' => 2, 'passable racing' => 3, 'good racing' => 4 , 'great racing' => 5 ]) ];
}

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
        "<a href=\"http://www.xcsoar.org/\">XCSoar</a>",
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
// mysql_close($link);
mysqli_close($link);
echo "</body></html>\n";
?>

