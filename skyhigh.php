<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<?php 
require 'authorisation.php';
menubar(5); 
?>
<p><h2>What is it?</h2></p>
<div id="rightbox">
<?php
$link = db_connect();
echo "<h3>Top 10</h3>";
echo "<ol>";
$count = 1;
$sql = "SELECT T.*, P.* FROM tblTrack T, tblPilot P, tblComTaskTrack CTT where T.pilPk=P.pilPk and CTT.traPk=T.traPk and CTT.comPk=5 order by T.traLength desc limit 10";
$result = mysql_query($sql,$link);
while($row = mysql_fetch_array($result))
{
    $id = $row['traPk'];
    $dist = round($row['traLength']/1000,2);
    $name = $row['pilFirstName'];
    echo "<a href=\"tracklog_map.php?trackid=$id&comPk=5\"><li> $dist kms ($name).</a><br>\n";

    $count++;
}
echo "</ol>";
echo "<p><h3>Recent 10</h3>";
echo "<ol>";
$count = 1;
$sql = "SELECT T.*, P.* FROM tblTrack T, tblPilot P, tblComTaskTrack CTT where T.pilPk=P.pilPk and CTT.traPk=T.traPk and CTT.comPk=5 order by T.traDate desc limit 10";
$result = mysql_query($sql,$link);
while($row = mysql_fetch_array($result))
{
    $id = $row['traPk'];
    $dist = round($row['traLength']/1000,2);
    $name = $row['pilFirstName'];
    echo "<a href=\"tracklog_map.php?trackid=$id&comPk=5\"><li> $dist kms ($name).</a><br>\n";

    $count++;
}
echo "</ol>";
?>
</div>

The Skyhigh Cup is a free cross-country competition for members of 
The Skyhigh Paragliding Club. It is intended to be a friendly 
competition that encourages members to improve their cross country 
flying at unfamiliar sites in the company of others. By collecting 
all the competitors' tracklogs 
in one place (here) club members also get the benefit of viewing where others 
have flown. This enables them to see where they might try to fly next 
time there are similar conditions and what areas work best for 
getting up and away. Stuff you need to know:
<ul>
<li><b>Who</b> - Any club pilot who is intermediate or above.<br>

<li><b>Where</b> - anywhere in Victoria except NEVHGC sites around Bright
   (including Mystic, Tawonga, Buffalo, Emu and the Pines). Here are some
   <a href="http://highcloud.net/xc/download_waypoints.php?download=6">waypoints</a> 
   for central Victoria (Compegps format).<br>

<li><b>When</b> - Any weekend between the 1st of Oct to the 31st of May.<br>
</ul>
Prizes will be awarded at the end of the season, The Skyhigh Cup itself
being awarded to the pilot with the highest overall score.
<p>
<h2>Registration</h2>
<p>
If you are intending to compete you must inform other
pilots by posting to Topica on the Friday before the weekend.  If
you're unable to post to Topica you must contact someone 
who can post your flying intentions to Topica.  Other pilots must be
given the opportunity to fly in the same conditions as you!
<p>
<h2>Safety</h2>
<p>
<i>Pilots may not fly alone</i>. Any flights without a witness(es) will
be considered to be invalid.
<p>
<i>Pilots must have a working UHF radio</i>. 
Any tracklog submitted by a pilot flying without a working radio 
will be considered to be invalid.
<p>
<i>Safe flying conditions:</i> if more than 50% of pilots present at a site 
assess the conditions as un-flyable then tracklogs from that day/site will be considered to be invalid.
<p>
We encourage pilots at a site to fill out a <a href="">running sheet</a>
on the day with mobile phone numbers and appoint duty pilots per the
HGFA handbook. 
<p>
<h2>Scoring</h2>
<p>
Submitted tracklogs will be scored using an OLC style scoring system.
Each tracklog with be optimised to include a start, 3 waypoints and an 
end point.  Tracks where the landing point is near the starting point may
gain bonus points based upon the area they enclose providing the
track forms a simple polygon. Your track will be viewable on the web,
and you will be able to view other participants tracks. Your total score
for the competition will be the total of your best four scores during
the season.
<p>
<i>Team flying</i> - to encourage team flying should will be bonus points 
awarded if pilots complete some of their flight with other pilots (TBD). 
<p>
Downloads must be within two weeks of the flight or at a club meeting if
you don't have your own cable. At the moment only .IGC files are 
accepted for scoring.

You can submit a track <a href="http://highcloud.net/xc/submit_track.php">here.</a>
<p>
<h2>Map Notes</h2>
<p>
The red-line tracklogs are only an approximation of the actual track, points
are removed in an effort to improve the speed of the map. The scoring
optimisation is an algorithm that is intended to be fast but doesn't
necessarily guarantee the most optimal track, but it should be pretty
close. Any glaring errors should be reported to Geoff Wong.
</div>
</body>
</html>

