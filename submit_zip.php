<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
<?php
require 'authorisation.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

if (array_key_exists('foo', $_REQUEST))
{
    echo "<title>Track Accepted</title>\n";
    $id = accept_track();
    redirect("tracklog_map.php?trackid=$id");
    exit(0);
}
?>
</head>
<body>
<div id="container">
<?php
$comPk = intval($_REQUEST['comPk']);
menubar($comPk);
?>
<div id="rightbox">
<h3>GPS Download Programs</h3>
<ul>
<li><a href="http://www.gethome.no/stein.sorensen/body_gpsdump.htm">GPSDump</a>
<li><a href="http://www.gpsinformation.org/ronh/">G7ToWin</a>
<li><a href="http://flighttrack.sourceforge.net/">FlightTrack (MacOS X)</a>
<li><a href="http://www.gpsbabel.org/">GPS Babel</a>
</ul>
</div>
<p><h2>Tracklog Submission</h2><p>
Download your GPS track from your GPS using one of the free 
programs shown on the right.  Then you're ready to upload the 
.IGC file created to the Skyhigh Cup website using the form here!
<?php
function upload_track($file,$pilPk)
{
    # Let the Perl program do it!
    $out = '';
    $retv = 0;
    exec(BINDIR . "igcreader.pl $file $pilPk", $out, $retv);

    return $retv;
}

function task_score($traPk)
{
    # Let the Perl program do it!
    $out = '';
    $retv = 0;
    exec(BINDIR . "track_verify.pl $traPk", $out, $retv);

    return $retv;
}

function accept_track()
{
    $file = addslashes($_REQUEST['userfile']);
    $hgfa = addslashes($_REQUEST['hgfanum']);
    $name = addslashes($_REQUEST['lastname']);
    $comPk = addslashes($_REQUEST['comPk']);

    $link = db_connect();

    $query = "select pilPk, pilHGFA from tblPilot where pilLastName='$name'";
//    $result = mysql_query($query) or die('Query failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
//    $row=mysql_fetch_array($result);
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    $pilPk = $row['pilPk'];

    if ($hgfa != $row['pilHGFA'])
    {
        echo "<b>Only authorised pilots may submit tracks.</b><br>\n";
        echo "Contact your administrator if you're having an access problem.<br>\n";
        echo "</div></body></html>\n";
        exit(0);
    }

    // Copy the upload so I can use it later ..
    $copyname = tempnam(FILEDIR, $name . $hgfa . "_");
    copy($_FILES['userfile']['tmp_name'], $copyname);
    chmod($copyname, 0644);

    // Process the file
    if (upload_track($_FILES['userfile']['tmp_name'], $pilPk))
    {
        echo "<b>Failed to upload your track correctly.</b><br>\n";
        echo "Contact your administrator if this was a valid track.<br>\n";
        echo "</div></body></html>\n";
        exit(0);
    }

    $query = "select max(traPk) from tblTrack";
//    $result = mysql_query($query) or die('Query failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
//    $maxPk=mysql_result($result,0);
    $maxPk = mysqli_result($result,0);

    $tasPk = 'null';
    $query = "select T.tasPk from tblTask T, tblTrack TL where T.comPk=$comPk and TL.traPk=$maxPk and T.tasDate=TL.traDate";
//    $result = mysql_query($query) or die('Query failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
//    if (mysql_num_rows($result) > 0)
    if (mysqli_num_rows($result) > 0)
    {
//        $tasPk=mysql_result($result,0);
        $tasPk = mysqli_result($result,0);
    }

    $query = "insert into tblComTaskTrack (comPk,tasPk,traPk) values ($comPk,$tasPk,$maxPk)";
//    $result = mysql_query($query) or die('ComTaskTrack failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' ComTaskTrack failed: ' . mysqli_connect_error());

    $glider = addslashes($_REQUEST['glider']);
    $dhv = addslashes($_REQUEST['dhv']);
    $query = "update tblTrack set traGlider='$glider', traDHV='$dhv' where traPk=$maxPk";
//    $result = mysql_query($query) or die('Update tblTrack failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Update tblTrack failed: ' . mysqli_connect_error());

    if ($tasPk != 'null')
    {
        task_score($maxPk);
    }

    return $maxPk;
}

function outform()
{
    $form='
    <form enctype="multipart/form-data" action="submit_track.php" method="post">
    <input type="hidden" name="MAX_FILE_SIZE" value="1000000000">
    <table>
    <tr><td>Competition</td><td><select name="comPk">
    <option value="2" selected>Skyhigh Cup 2006</option>
    <option value="1">Highcloud OLC 2006</option>
    <option value="3">Mystic Cup Test</option>
    </select>
    </td></tr>
    <tr><td>Send IGC file</td><td><input name="userfile" type="file"></td></tr>
    <tr><td>HGFA Number</td><td><input name="hgfanum" type="text"></td></tr>
    <tr><td>Last Name</td><td><input name="lastname" type="text"></td></tr>
    <tr><td>Glider</td><td><input name="glider" type="text">
    DHV&nbsp;<select name="dhv">
    <option value="competition" selected>open</option>
    <option value="1">1</option>
    <option value="1/2">1/2</option>
    <option value="2">2</option>
    <option value="2/3">2/3</option>
    </td></tr>
    <tr><td></td><td align=center><input type="submit" name="foo" value="Send Tracklog"></td></tr></table></form>';

    echo $form;
}


outform();
?>
</td></tr>
</div>
</body>
</html>

