<?php
require 'authorisation.php';
require 'template.php';
require 'format.php';
require 'xcdb.php';

$comPk = intval($_REQUEST['comPk']);

$usePk = check_auth('system');
$link = db_connect();
$tasPk = intval($_REQUEST['tasPk']);
$isadmin = 0;
$cval = null;
$tarPk = null;

$file = __FILE__;

if (!array_key_exists('pr', $_REQUEST))
{
    $isadmin = is_admin('admin',$usePk,$comPk);
}

$rnd = 1;
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
    #$classstr = "<b>" . $cstr[reqival('class')] . "</b> - ";
    $classstr = "<b>" . (isset($cstr[reqival('class')]) ? $cstr[reqival('class')] : "") . "</b> - ";
    if ($cval == 4)
    {
        $fdhv = "and P.pilSex='F'";
    }
    else
    {
        #$fdhv = $carr[reqival('class')];
        $fdhv = isset($carr[reqival('class')]) ? $carr[reqival('class')] : "";
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

//		Old Task Check
//		Removed to debug and test
//
//         if ($today > $dateto)
//         {
//             $changeok = 0;
//         }

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
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task Result update failed: ' . mysqli_connect_error());
    $query = "update tblTrack set traGlider='$glider', traDHV='$dhv' where traPk=$traPk";
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
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query pilot (fai) failed: ' . mysqli_connect_error());
    }

    if (mysqli_num_rows($result) == 0)
    {
        $fai = addslashes($_REQUEST['fai']);
        $query = "select P.pilPk from tblComTaskTrack T, tblTrack TR, tblPilot P 
                    where T.comPk=$comPk 
                        and T.traPk=TR.traPk 
                        and TR.pilPk=P.pilPk 
                        and P.pilLastName='$fai'";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query pilot (name) failed: ' . mysqli_connect_error());
    }

    if (mysqli_num_rows($result) > 0)
    {
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
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task date failed: ' . mysqli_connect_error());
        $tasDate=mysqli_result($result,0);

        $query = "insert into tblTrack (pilPk,traGlider,traDHV,traDate,traStart,traLength) values ($pilPk,'$glider','$dhv','$tasDate','$tasDate',$flown)";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task insert result failed: ' . mysqli_connect_error());

        $maxPk = mysqli_insert_id($link);

        $query = "insert into tblTaskResult (tasPk,traPk,tarDistance,tarPenalty,tarResultType) values ($tasPk,$maxPk,$flown,$penalty,'$resulttype')";
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
    $ssDist = $row['tasSSDistance'];

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
    $hdname = "<a href=\"task_admin.php?comPk=$comPk&tasPk=$tasPk\">$tasName</a> - <a href=\"competition_admin.php?comPk=$comPk\">$comName</a>";
}
else
{
    $hdname =  "$comName - $tasName";
}

//initializing template header
tpinit($link,$file,$row);

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

// FIX: Print out task quality information.

$sql = "select SUM(ABS(TR.tarPenalty)) AS totalPenalty from tblTaskResult TR where TR.tasPk=$tasPk";
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Penalty Sum failed: ' . mysqli_connect_error());
$row = mysqli_fetch_assoc($result);
$totalPenalty = $row['totalPenalty'];

if ($isadmin)
{
    echo "<form action=\"task_result.php?comPk=$comPk&tasPk=$tasPk\" name=\"resultupdate\" method=\"post\"><p>"; 
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
$header[] = fb("Speed");
if ($tasStoppedTime != '')
{
    $header[] = fb("S.Alt");
}
if ($tasHeightBonus == 'on')
{
    $header[] = fb("HBs");
}
$header[] = fb("Distance");
if ( $isadmin or ($totalPenalty != 0) )
{
	$header[] = fb("Pen");
}
$header[] = fb("Spd");
if ($depcol != 'off')
{
    $header[] = fb($depcol);
}
if ($tasArrival == 'on')
{
    $header[] = fb("Arv");
}
// $header[] = fb("Spd");
$header[] = fb("Dst");
$header[] = fb("Total");
$trtab[] = $header;
$count = 1;

$sql = "select TR.*, T.*, P.* from tblTaskResult TR, tblTrack T, tblPilot P where TR.tasPk=$tasPk $fdhv and T.traPk=TR.traPk and P.pilPk=T.pilPk order by TR.tarScore desc, P.pilFirstName";
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task result selection failed: ' . mysqli_connect_error());
$lastscore = 0;
$hh = 0;
$mm = 0;
$ss = 0;

while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $name = $row['pilFirstName'] . ' ' . $row['pilLastName'];
    $nation = $row['pilNationCode'];
    $tarPk = $row['tarPk'];
    $traPk = $row['traPk'];
    $dist = round($row['tarDistanceScore'], $rnd);
    $dep = round($row['tarDeparture'], $rnd);
    $arr = round($row['tarArrival'], $rnd);
    $spd = round($row['tarSpeedScore'], $rnd);
    $score = round($row['tarScore'], $rnd);
    $lastalt = round($row['tarLastAltitude']);
    $resulttype = $row['tarResultType'];
    $comment = $row['tarComment'];
    $start = $row['tarSS'];
    $end = $row['tarES'];
    $goal = $row['tarGoal'];
    $endf = "";
    $startf = "";
    $timeinair = "";
    $hh = floor(($comTOffset + $start) / 3600) % 24;
	$mm = floor((($comTOffset + $start) % 3600) / 60);
	$ss = ($comTOffset + $start) % 60;
	$startf = sprintf("%02d:%02d:%02d", $hh,$mm,$ss);
	# echo $startf." ".$tasStartTime;
	if ( $startf < $tasStartTime ) # If pilot did not make the start, do not print start time
	{
		$startf = "";
	}
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
        $speed = round($ssDist * 3.6 / ($end - $start), 2);
    }
    else
    {
        $timeinair = "";
        $speed = "";
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
    $glider = ( (stripos($row['traGlider'], 'Unknown') !== false) ? '' : htmlspecialchars($row['traGlider']) );
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

    $trrow = array(fb($place), "<a href=\"tracklog_map.php?trackid=$traPk&tasPk=$tasPk&comPk=$comPk\">$name</a>", $nation );
    if ($isadmin)
    {
        $trrow[] = fih("track$tarPk", $traPk) . fin("glider$tarPk", $glider, "wide");
        $trrow[] = fin("dhv$tarPk", $dhv, "medium");
    }
    else
    {
        $trrow[] = $glider;
    }
    $trrow[] = $startf;
    $trrow[] = ( $goal != 0 ? $endf : "<del>".$endf."</del>" );
    $trrow[] = ( $goal != 0 ? $timeinair : "<del>".$timeinair."</del>" );
    $trrow[] = ( $speed != 0 ? number_format((float)$speed,2) : "" );
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
        $trrow[] = fin("flown$tarPk", $tardist, "short");
        $trrow[] = fin("penalty$tarPk", $penalty, "short");
    }
    else
    {
        $trrow[] = number_format((float)$tardist,2);
        if ( $totalPenalty != 0 )
    	{
    		$trrow[] = $penalty;
    	}
    }
	$trrow[] = number_format($spd,1);
    if ($depcol != 'off')
    {
        $trrow[] = number_format($dep,1);
    }
    if ($tasArrival == 'on')
    {
        $trrow[] = $arr;
    }
//     $trrow[] = number_format($spd,1);
    $trrow[] = number_format($dist,1);
    $trrow[] = round($score);
    if ($isadmin) 
    {
        $trrow[] = fbut("submit", "tardel",  $traPk, "del");
        $trrow[] = fbut("submit", "tarup",  $tarPk, "up");
        $trrow[] = $comment;
    }

    $trtab[] = $trrow;

    $count++;
}
echo ftable($trtab, 'class=taskresult', '' , '');

if ($isadmin)
{
    // FIX: enable 'manual' pilot flight addition
    
    $piladd = [];
    $piladd[] =  array(fb("FAI"), fin("fai",'',6), fb("Type"), fselect('resulttype', 'lo', array('abs', 'dnf', 'lo', 'goal' )),
        fb("Dist"), fin("flown",'',4), fb("Glider"), fin("glider",'',6), fb("Class"), fselect('dhv', 'competition', array('1', '1/2', '2', '2/3', 'competition')), fb("Penalty"),fin("penalty",'',4), fbut("submit","addflight", "$tarPk", "Manual Addition"));
    echo ftable($piladd, 'class=taskpiladd', '', '');

    echo "</form>";
    echo "</p>";
}

tpfooter($file);

?>
