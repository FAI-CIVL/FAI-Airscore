<?php
require 'authorisation.php';
require 'hc.php';
require 'format.php';
require 'xcdb.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

$comPk = intval($_REQUEST['comPk']);

$usePk = check_auth('system');
$link = db_connect();
$tasPk = intval($_REQUEST['tasPk']);
$isadmin = 0;
if (!array_key_exists('pr', $_REQUEST))
{
    $isadmin = is_admin('admin',$usePk,$comPk);
}

$rnd = 0;
if (array_key_exists('rnd', $_REQUEST))
{
    $rnd = intval($_REQUEST['rnd']);
}
#echo "usePk=$usePk isadmin=$isadmin<br>";

$fdhv= '';
$classstr = '';
if (reqexists('class'))
{
    $cval = reqival('class');
    $carr = [ "'1/2'", "'2'", "'2/3'", "'competition'" ];
    $cstr = ["Fun", "Sport", "Serial", "Open", "Women" ];
    $classstr = "<b>" . $cstr[reqival('class')] . "</b> - ";
    if ($cval == 4)
    {
        $fdhv = "and P.pilSex='F'";
    }
    else
    {
        $fdhv = $carr[reqival('class')];
        $fdhv = "and traDHV=$fdhv ";
    }
}

if (array_key_exists('score', $_REQUEST))
{
    $changeok = 1;
    $row = get_comtask($link,$tasPk);
    if ($row)
    {
        $dateto = $row['comDateTo'];
        $today = date('Y-m-d');
        if ($today > $dateto)
        {
            $changeok = 0;
        }
    }
    if ($changeok == 1)
    {
        $out = '';
        $retv = 0;
        exec(BINDIR . "task_score.pl $tasPk", $out, $retv);
    }
    else
    {
        echo "Unable to rescore a closed competition.\n";
    }
}

if (array_key_exists('tardel', $_REQUEST))
{
    $tarPk = intval($_REQUEST['tardel']);
    $out = '';
    $retv = 0;
    exec(BINDIR . "del_track.pl $tarPk", $out, $retv);
    if ($retv == 0)
    {
        echo "Deleted: $tarPk<br>";
    }
    else
    {
        echo "$out<br>";
    }
}

if (array_key_exists('tarup', $_REQUEST))
{
    $tarPk = reqival('tarup');
    $glider = reqsval("glider$tarPk");
    $dhv = reqsval("dhv$tarPk");
    $flown = reqsval("flown$tarPk");
    $penalty = reqival("penalty$tarPk");
    $traPk = reqival("track$tarPk");
    $resulttype = 'lo';
    if ($flown == 'abs' || $flown == 'dnf' || $flown == 'lo')
    {
        $resulttype = $flown;
        $flown = 0;
    }
    else
    {
        $flown = $flown * 1000;
        if (0 + $flown == 0) 
        {
            $resulttype = 'dnf';
        }
    }

    $query = "update tblTaskResult set tarDistance=$flown, tarPenalty=$penalty, tarResultType='$resulttype' where tarPk=$tarPk";
    // $result = mysql_query($query) or die('Task Result update failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task Result update failed: ' . mysqli_connect_error());
    $query = "update tblTrack set traGlider='$glider', traDHV='$dhv' where traPk=$traPk";
    // $result = mysql_query($query) or die('Glider update failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Glider update failed: ' . mysqli_connect_error());
    # recompute every time?
    $out = '';
    $retv = 0;
    exec(BINDIR . "task_score.pl $tasPk", $out, $retv);
}

if (array_key_exists('addflight', $_REQUEST))
{
    $fai = intval($_REQUEST['fai']);
    if ($fai > 0)
    {
        $query = "select pilPk from tblPilot where pilHGFA=$fai";
        // $result = mysql_query($query) or die('Query pilot (fai) failed: ' . mysql_error());
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query pilot (fai) failed: ' . mysqli_connect_error());
    }

//    if (mysql_num_rows($result) == 0)
    if (mysqli_num_rows($result) == 0)
    {
        $fai = addslashes($_REQUEST['fai']);
        $query = "select P.pilPk from tblComTaskTrack T, tblTrack TR, tblPilot P 
                    where T.comPk=$comPk 
                        and T.traPk=TR.traPk 
                        and TR.pilPk=P.pilPk 
                        and P.pilLastName='$fai'";
        // $result = mysql_query($query) or die('Query pilot (name) failed: ' . mysql_error());
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query pilot (name) failed: ' . mysqli_connect_error());
    }

//    if (mysql_num_rows($result) > 0)
    if (mysqli_num_rows($result) > 0)
    {
//        $pilPk = mysql_result($result,0,0);
        $pilPk = mysqli_result($result,0,0);
        $flown = floatval($_REQUEST["flown"]) * 1000;
        $penalty = intval($_REQUEST["penalty"]);
        $glider = addslashes($_REQUEST["glider"]);
        $dhv = addslashes($_REQUEST["dhv"]);
        $resulttype = addslashes($_REQUEST["resulttype"]);
        $tasPk = intval($_REQUEST["tasPk"]);
        if ($resulttype == 'dnf' || $resulttype == 'abs')
        {
            $flown = 0.0;
        }

        $query = "select tasDate from tblTask where tasPk=$tasPk";
        // $result = mysql_query($query) or die('Task date failed: ' . mysql_error());
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task date failed: ' . mysqli_connect_error());
//        $tasDate=mysql_result($result,0);
        $tasDate=mysqli_result($result,0);

        $query = "insert into tblTrack (pilPk,traGlider,traDHV,traDate,traStart,traLength) values ($pilPk,'$glider','$dhv','$tasDate','$tasDate',$flown)";
        // $result = mysql_query($query) or die('Track Insert result failed: ' . mysql_error());
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task insert result failed: ' . mysqli_connect_error());

//        $maxPk = mysql_insert_id();
        $maxPk = mysqli_insert_id($link);

        #$query = "select max(traPk) from tblTrack";
        #// $result = mysql_query($query) or die('Max track failed: ' . mysql_error());
        #$maxPk=mysql_result($result,0);

        $query = "insert into tblTaskResult (tasPk,traPk,tarDistance,tarPenalty,tarResultType) values ($tasPk,$maxPk,$flown,$penalty,'$resulttype')";
        // $result = mysql_query($query) or die('Insert result failed: ' . mysql_error());
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Insert result failed: ' . mysqli_connect_error());

        $out = '';
        $retv = 0;
        exec(BINDIR . "task_score.pl $tasPk", $out, $retv);
    }
    else
    {
        echo "Unknown pilot: $fai<br>";
    }
}

$depcol = 'Dpt';
$row = get_comtask($link,$tasPk);
if ($row)
{
    $comName = $row['comName'];
    $comClass = $row['comClass'];
    $comPk = $row['comPk'];
    $_REQUEST['comPk'] = $comPk;
    $comTOffset = $row['comTimeOffset'] * 3600;
    $tasName = $row['tasName'];
    $tasDate = $row['tasDate'];
    $tasTaskType = $row['tasTaskType'];
    $tasStartTime = substr($row['tasStartTime'],11);
    $tasFinishTime = substr($row['tasFinishTime'],11);
    $tasDistance = round($row['tasDistance']/1000,2);
    $tasShortest = round($row['tasShortRouteDistance']/1000,2);
    $tasQuality = round($row['tasQuality'],3);
    $tasComment = $row['tasComment'];
    $tasDistQuality = round($row['tasDistQuality'],2);
    $tasTimeQuality = round($row['tasTimeQuality'],2);
    $tasLaunchQuality = round($row['tasLaunchQuality'],2);
    $tasArrival = $row['tasArrival'];
    $tasHeightBonus = $row['tasHeightBonus'];
    $tasStoppedTime = substr($row['tasStoppedTime'],11);

    if ($row['tasDeparture'] == 'leadout')
    {
        $depcol = 'Ldo';
    }
    elseif ($row['tasDeparture'] == 'kmbonus')
    {
        $depcol = 'Lkm';
    }
    elseif ($row['tasDeparture'] == 'on')
    {
        $depcol = 'Dpt';
    }
    else
    {
        $depcol = 'off';
    }
}
$waypoints = get_taskwaypoints($link,$tasPk);

// incorporate $tasTaskType / $tasDate in heading?
if ($isadmin > 0)
{
    $hdname = "<a href=\"task.php?comPk=$comPk&tasPk=$tasPk\">$tasName</a> - <a href=\"competition.php?comPk=$comPk\">$comName</a>";
}
else
{
    $hdname =  "$comName - $tasName";
}
hcheader($hdname,2,"${classstr}${tasDate}");
echo "<div id=\"content\">";

# Waypoint Info
echo "<div id=\"infobar\">";
echo "<div id=\"colone\">";
$goalalt = 0;
$winfo = [];
$winfo[] = array(fb("#"), fb("ID"), fb("Type"), fb("Radius"), fb("Dist(k)"), fb("Description"));
foreach ($waypoints as $row)
{
    $winfo[] = array($row['tawNumber'], $row['rwpName'], $row['tawType'] . " (" . $row['tawHow'] . ")", $row['tawRadius'] . "m", round($row['ssrCumulativeDist']/1000,1), $row['rwpDescription']);
    if ($row['tawType'] == 'goal')
    {
        $goalalt = $row['rwpAltitude'];
    }
}
echo ftable($winfo, "id=\"alt\" border=\"0\" cellpadding=\"2\" cellspacing=\"0\" valign=\"top\" align=\"left\"", '', '');
echo "</div>";

if ($comClass == "HG")
{
    $classopts = array ( 'open' => '', 'floater' => '&class=0', 'kingpost' => '&class=1', 
        'hg-open' => '&class=2', 'rigid' => '&class=3', 'women' => '&class=4', 'masters' => '&class=5', 'teams' => '&class=6' );
}
else
{
    $classopts = array ( 'open' => '', 'fun' => '&class=0', 'sports' => '&class=1', 
        'serial' => '&class=2', 'women' => '&class=4', 'masters' => '&class=5', 'teams' => '&class=6' );
}
$cind = '';
if ($cval != '')
{
    $cind = "&class=$cval";
}
$copts = [];
foreach ($classopts as $text => $url)
{
    if ($text == 'teams')
    {
        # Hack for now
        $copts[$text] = "team_task_result.php?comPk=$comPk&tasPk=$tasPk$url";
    }
    else
    {
        $copts[$text] = "task_result.php?comPk=$comPk&tasPk=$tasPk$url";
    }
}

$classfilter = fselect('class', "task_result.php?comPk=$comPk&tasPk=$tasPk$cind", $copts, ' onchange="document.location.href=this.value"');

echo "<div id=\"coltwo\">";
$tinfo = [];
$tinfo[] = array( fb("Task Type"), $tasTaskType, "", "", fb("Class"), $classfilter );
if ($tasStoppedTime == "")
{
    $tinfo[] = array( fb("Date"), $tasDate, fb("Start"), "$tasStartTime", fb("End"), "$tasFinishTime" );
}
else
{
    $tinfo[] = array( fb("Date"), $tasDate, fb("Start"), "$tasStartTime", fb("Stopped"), "$tasStoppedTime" );
}
$tinfo[] = array( fb("Quality"), number_format($tasQuality,2), fb("WP Dist"), "$tasDistance km", fb("Task Dist"), "$tasShortest km" );
$tinfo[] = array( fb("DistQ"), number_format($tasDistQuality,2), fb("TimeQ"), number_format($tasTimeQuality,2), fb("LaunchQ"), number_format($tasLaunchQuality,2) );
echo ftable($tinfo, "id=\"alt\" border=\"0\" cellpadding=\"3\" cellspacing=\"0\" valign=\"top\" align=\"right\"", '', '');
echo "</div>";
echo "</div>";
if ($tasComment != '')
{
    echo "<div id=\"comment\" width=\"50%\" align=\"right\">";
    echo $tasComment;
    echo "</div>";
}

# Pilot Info
$pinfo = [];
# total, launched, absent, goal, es?

# Formula / Quality Info
$finfo = [];
# gap, min dist, nom dist, nom time, nom goal ?

# quality, dist, time, launch, available dist, available time, available lead, arrival
#$qinfo = [];
#$qinfo[] = array( fb("Quality"), fb("$tasQuality"));
#$qinfo[] = array( fb("Dist"), $tasDistQuality, fb("Time"), $tasTimeQuality, fb("Launch"), $tasLaunchQuality );
#echo ftable($qinfo, "border=\"2\" cellpadding=\"3\" cellspacing=\"0\" alternate-colours=\"yes\" valign=\"top\" align=\"right\"", array('class="d"', 'class="l"'), '');
#echo "<br><p>";


// FIX: Print out task quality information.

if ($isadmin)
{
    echo "<form action=\"task_result.php?comPk=$comPk&tasPk=$tasPk\" name=\"resultupdate\" method=\"post\">"; 
}
// add in country from tblCompPilot if we have entries ...
$trtab = [];

$header = array(fb("Place"), fb("Pilot"), fb("Nat"), fb("Glider"));
if ($isadmin)
{
    $header[] = fb("DHV");
}
$header[] = fb("SS");
$header[] = fb("ES");
$header[] = fb("Time");
if ($tasStoppedTime != '')
{
    $header[] = fb("S.Alt");
}
if ($tasHeightBonus == 'on')
{
    $header[] = fb("HBs");
}
$header[] = fb("Kms");
$header[] = fb("Pen");
if ($depcol != 'off')
{
    $header[] = fb($depcol);
}
if ($tasArrival == 'on')
{
    $header[] = fb("Arv");
}
$header[] = fb("Spd");
$header[] = fb("Dst");
$header[] = fb("Total");
$trtab[] = $header;
$count = 1;

$sql = "select TR.*, T.*, P.* from tblTaskResult TR, tblTrack T, tblPilot P where TR.tasPk=$tasPk $fdhv and T.traPk=TR.traPk and P.pilPk=T.pilPk order by TR.tarScore desc, P.pilFirstName";
// $result = mysql_query($sql,$link) or die('Task Result selection failed: ' . mysql_error());
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task result selection failed: ' . mysqli_connect_error());
$lastscore = 0;
$hh = 0;
$mm = 0;
$ss = 0;
// while ($row = mysql_fetch_array($result))
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $name = $row['pilFirstName'] . ' ' . $row['pilLastName'];
    $nation = $row['pilNationCode'];
    $tarPk = $row['tarPk'];
    $traPk = $row['traPk'];
    $dist = round($row['tarDistanceScore'], $rnd);
    $dep = round($row['tarDeparture'], $rnd);
    $arr = round($row['tarArrival'], $rnd);
    $speed = round($row['tarSpeedScore'], $rnd);
    $score = round($row['tarScore'], $rnd);
    $lastalt = round($row['tarLastAltitude']);
    $resulttype = $row['tarResultType'];
    $comment = $row['tarComment'];
    $start = $row['tarSS'];
    $end = $row['tarES'];
    $endf = "";
    $startf = "";
    $timeinair = "";
    if ($end)
    {
        $hh = floor(($end - $start) / 3600);
        $mm = floor((($end - $start) % 3600) / 60);
        $ss = ($end - $start) % 60;
        $timeinair = sprintf("%01d:%02d:%02d", $hh,$mm,$ss);
        $hh = floor(($comTOffset + $start) / 3600) % 24;
        $mm = floor((($comTOffset + $start) % 3600) / 60);
        $ss = ($comTOffset + $start) % 60;
        $startf = sprintf("%02d:%02d:%02d", $hh,$mm,$ss);
        $hh = floor(($comTOffset + $end) / 3600) % 24;
        $mm = floor((($comTOffset + $end) % 3600) / 60);
        $ss = ($comTOffset + $end) % 60;
        $endf = sprintf("%02d:%02d:%02d", $hh,$mm,$ss);
    }
    else
    {
        $timeinair = "";
        if ($tasTaskType == 'speedrun-interval')
        {
            $hh = floor(($comTOffset + $start) / 3600) % 24;
            $mm = floor((($comTOffset + $start) % 3600) / 60);
            $ss = ($comTOffset + $start) % 60;
            if ($hh >= 0 && $mm >= 0 && $ss >= 0)
            {
                $startf = sprintf("%02d:%02d:%02d", $hh,$mm,$ss);
            }
            else
            {
                $startf = "";
            }
        }
    }
    $time = ($end - $start) / 60;
    $tardist = round($row['tarDistance']/1000,2);
    $penalty = round($row['tarPenalty']);
    $glider = htmlspecialchars($row['traGlider']);
    $dhv = $row['traDHV'];
    if (0 + $tardist == 0)
    {
        $tardist = $resulttype;
    }

    if ($lastscore != $score)
    {
        $place = "$count";
    }
    else
    {
        $place = '';
    }
    $lastscore = $score;

    if ($count % 2 == 0)
    {
        $class = "d";
    }
    else
    {
        $class = "l";
    }

    $trrow = array(fb($place), "<a href=\"tracklog_map.php?trackid=$traPk&comPk=$comPk\">$name</a>", $nation );
    if ($isadmin)
    {
        $trrow[] = fih("track$tarPk", $traPk) . fin("glider$tarPk", $glider, 18);
        $trrow[] = fin("dhv$tarPk", $dhv, 3);
    }
    else
    {
        $trrow[] = "$glider ($dhv)";
    }
    $trrow[] = $startf;
    $trrow[] = $endf;
    $trrow[] = $timeinair;
    if ($tasStoppedTime != '')
    {
        $trrow[] = $lastalt;
    }
    if ($tasHeightBonus == 'on')
    {
        if ($lastalt > 0)
        {
            $habove = $lastalt - $goalalt;
            if ($habove > 400)
            {
                $habove = 400;
            }
            if ($habove > 50)
            {
                $trrow[] = round(20.0*pow(($habove-50.0),0.40));
            }
            else
            {
                $trrow[] = 0;
            }
        }
        else
        {
            $trrow[] = '';
        }
    }
    if ($isadmin) 
    {
        $trrow[] = fin("flown$tarPk", $tardist, 4);
        $trrow[] = fin("penalty$tarPk", $penalty, 4);
    }
    else
    {
        $trrow[] = $tardist;
        $trrow[] = $penalty;
    }

    if ($depcol != 'off')
    {
        $trrow[] = $dep;
    }
    if ($tasArrival == 'on')
    {
        $trrow[] = $arr;
    }
    $trrow[] = $speed;
    $trrow[] = $dist;
    $trrow[] = $score;
    if ($isadmin) 
    {
        $trrow[] = fbut("submit", "tardel",  $traPk, "del");
        $trrow[] = fbut("submit", "tarup",  $tarPk, "up");
        $trrow[] = $comment;
    }

    $trtab[] = $trrow;

    $count++;
}
echo ftable($trtab, "id=\"alth\" border=\"0\" width=\"100%\" cellpadding=\"2\" cellspacing=\"0\" align=\"left\"", '' , '');
if ($isadmin)
{
    // FIX: enable 'manual' pilot flight addition
    
    $piladd = [];
    $piladd[] =  array(fb("FAI"), fin("fai",'',6), fb("Type"), fselect('resulttype', 'lo', array('abs', 'dnf', 'lo', 'goal' )),
        fb("Dist"), fin("flown",'',4), fb("Glider"), fin("glider",'',6), fb("Class"), fselect('dhv', 'competition', array('1', '1/2', '2', '2/3', 'competition')), fb("Penalty"),fin("penalty",'',4), fbut("submit","addflight", "$tarPk", "Manual Addition"));
    echo ftable($piladd, "border=\"0\" cellpadding=\"2\" cellspacing=\"0\" valign=\"bottom\" align=\"left\"", '', '');

    echo "</form>";
    echo "</p>";
}

?>
</div>
</div>
</body>
</html>

