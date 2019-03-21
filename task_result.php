<?php
require 'authorisation.php';
require 'template.php';
require 'format.php';
require 'xcdb.php';

function get_goal_altitude($link, $taskPk)
{
	$query = "  SELECT
                    rwpAltitude
                FROM
                    tblRegionWaypoint
                WHERE
                    rwpPk = ( 
                    SELECT
                        TW.rwpPk
                    FROM
                        tblTaskWaypoint TW
                    WHERE
                        TW.tasPk = $taskPk AND TW.tawType = 'goal'
                    )";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Cannot get Goal Altitude: ' . mysqli_connect_error());
    $alt = mysqli_result($result,0,0);
    return $alt;
}

$comPk = intval($_REQUEST['comPk']);
$tasPk = intval($_REQUEST['tasPk']);

$usePk = check_auth('system');
$link = db_connect();
$isadmin = 0;
$cval = null;
$tarPk = null;

$file = __FILE__;

$message = '';

if (!array_key_exists('pr', $_REQUEST))
{
    $isadmin = is_admin('admin',$usePk,$comPk);
}

$rnd = 1;
if (array_key_exists('rnd', $_REQUEST))
{
    $rnd = intval($_REQUEST['rnd']);
}
//echo "usePk=$usePk isadmin=$isadmin<br>";

# Check if we have a classification request
$sel = get_class_info($link, $comPk);
$classstr = $sel['name'];
$fdhv = $sel['fdhv'];

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
    $traPk = intval($_REQUEST['tardel']);
    # Using new python script
	$command = "python3 " . BINDIR . "del_track.py $traPk";
	$message .= nl2br(shell_exec($command));

//     $out = '';
//     $retv = 0;
//     exec(BINDIR . "del_track.pl $traPk", $out, $retv);
//     if ($retv == 0)
//     {
//         echo "Deleted: $traPk<br>";
//     }
//     else
//     {
//         echo "$out<br>";
//     }
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
        $query = "select pilPk from tblPilot where pilFAI=$fai";
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
    $extComp = $row['comExt'];

    if ($row['tasDeparture'] == 'leadout')
    {
        $depcol = 'LO P';
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
//$waypoints = get_taskwaypoints($link,$tasPk);

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

if ($tasComment != '')
{
    echo "<div id=\"comment\" width=\"50%\" align=\"right\">";
    echo $tasComment;
    echo "</div>";
}

# Classification - State (provisional / final YET TO IMPLEMENT)
echo "<h5 class='classdef'> $classstr $state </h5> \n";

# Pilot Info
$pinfo = [];
# total, launched, absent, goal, es?

# Formula / Quality Info
$finfo = [];
# gap, min dist, nom dist, nom time, nom goal ?

// FIX: Print out task quality information.

// $sql = "select SUM(ABS(TR.tarPenalty)) AS totalPenalty from tblTaskResult TR where TR.tasPk=$tasPk";
$sql = "select SUM(ABS(TR.tarPenalty)) AS totalPenalty from tblResult TR where TR.tasPk=$tasPk";
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Penalty Sum failed: ' . mysqli_connect_error());
$row = mysqli_fetch_assoc($result);
$totalPenalty = $row['totalPenalty'];
//echo "TotalPenalty: $totalPenalty";

if ($isadmin)
{
	# Messages field
	if ( $message !== '')
	{
		echo "<h4> <span style='color:red'>$message</span> </h4>" . PHP_EOL;
		echo "<hr />" . PHP_EOL;
	}
    echo "<form action=\"task_result.php?comPk=$comPk&tasPk=$tasPk\" name=\"resultupdate\" method=\"post\"><p>"; 
}
// add in country from tblCompPilot if we have entries ...
$trtab = [];

$header = array(fb("Place"), fb("Pilot"), fb("Nat"), fb("Glider"));
if ($isadmin and $extComp != 1)
{
    $header[] = fb("DHV");
}
$header[] = fb("Sponsor");
$header[] = fb("SS");
$header[] = fb("ES");
$header[] = fb("Time");
$header[] = fb("Speed");
if ($tasStoppedTime != '')
{
    $goalalt = get_goal_altitude($link, $tasPk);
    $header[] = fb("Altitude");
}
if ($tasHeightBonus == 'on')
{
    $header[] = fb("HBs");
}
$header[] = fb("Distance");
if ( ($isadmin and $extComp != 1) or ($totalPenalty != 0) )
{
	$header[] = fb("Pen");
}
$header[] = fb("Spd P");
if ($depcol != 'off')
{
    $header[] = fb($depcol);
}
if ($tasArrival == 'on')
{
    $header[] = fb("Arv");
}
// $header[] = fb("Spd");
$header[] = fb("Dst P");
$header[] = fb("Score");
$trtab[] = $header;
$count = 1;

// $sql = "	SELECT 
// 				TR.*, 
// 				T.*, 
// 				P.*,
// 				( SELECT C.natIso3 FROM tblCountryCodes C WHERE C.natID = P.pilNat ) AS pilNationCode
// 			FROM 
// 				tblTaskResult TR, 
// 				tblTrack T, 
// 				tblPilot P 
// 			WHERE 
// 				TR.tasPk = $tasPk $fdhv 
// 				AND T.traPk = TR.traPk 
// 				AND P.pilPk = T.pilPk 
// 			ORDER BY 
// 				TR.tarScore DESC, 
// 				P.pilFirstName";

$sql = "SELECT 
            R.*,
            P.`pilFirstName`,
            P.`pilLastName`,
            P.`pilSponsor`,
            ( SELECT C.natIso3 FROM tblCountryCodes C WHERE C.natID = P.pilNat ) AS pilNationCode
        FROM
            `tblResult` R
            JOIN `tblPilot` P USING (`pilPk`) 
        WHERE 
            R.tasPk = $tasPk $fdhv 
        ORDER BY 
            R.tarScore DESC, 
            P.pilFirstName";

$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task result selection failed: ' . mysqli_connect_error());
$lastscore = 0;
$hh = 0;
$mm = 0;
$ss = 0;

while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $name = str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['pilFirstName'] . ' ' . $row['pilLastName']))));
    $nation = $row['pilNationCode'];
    $tarPk = $row['tarPk'];
    $traPk = $row['traPk'];
    $glider = ( (stripos($row['traGlider'], 'Unknown') !== false) ? '' : htmlspecialchars(str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower(substr($row['traGlider'], 0, 25)))))) );
    $sponsor = isset($row['pilSponsor']) ? htmlspecialchars(str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower(substr($row['pilSponsor'], 0, 40)))))) : '';
    $dhv = $row['traDHV'];
    $resulttype = strtoupper($row['tarResultType']);
    
    # Check if pilot did fly
    if ( $resulttype == 'ABS' || $resulttype == 'DNF' )
    {
    	$trrow = array(fb($place), $name, $nation);
    	if ($isadmin and $extComp != 1)
		{
			$trrow[] = fih("track$tarPk", $traPk) . fin("glider$tarPk", $glider, "wide");
			$trrow[] = fin("dhv$tarPk", $dhv, "medium");
			$trrow[] = $sponsor;
		}
		else
		{
			$trrow[] = $glider;
			$trrow[] = $sponsor;
		}
		array_push($trrow, '', '', '', '');
		if ($isadmin) 
		{
			$trrow[] = fin("flown$tarPk", '', "short");
			$trrow[] = fin("penalty$tarPk", '', "short");
		}
		else
		{
			$trrow[] = '';
			if ( $totalPenalty != 0 )
			{
				$trrow[] = '';
			}
		}		
		array_push($trrow, '', '', '', $resulttype);
    }
    else
    {
		$dist = round($row['tarDistanceScore'], $rnd);
		$dep = round($row['tarDepartureScore'], $rnd);
		$arr = round($row['tarArrivalScore'], $rnd);
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
		#$glider = ( (stripos($row['pilGlider'], 'Unknown') !== false) ? '' : htmlspecialchars(str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['pilGliderBrand'] . ' ' . $row['pilGlider']))))) );
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

		if ( $extComp != 1 )
		{
		    $trrow = array(fb($place), "<a href=\"tracklog_map.php?trackid=$traPk&tasPk=$tasPk&comPk=$comPk\">$name</a>", $nation );
		}
		else
		{
		    $trrow = array(fb($place), $name, $nation );
		}
		//$trrow = array(fb($place), "<a href=\"tracklog_map.php?trackid=$traPk&tasPk=$tasPk&comPk=$comPk\">$name</a>", $nation );
		if ($isadmin and $extComp != 1)
		{
			$trrow[] = fih("track$tarPk", $traPk) . fin("glider$tarPk", $glider, "wide");
			$trrow[] = fin("dhv$tarPk", $dhv, "medium");
			$trrow[] = $sponsor;
		}
		else
		{
			$trrow[] = $glider;
			$trrow[] = $sponsor;
		}
		$trrow[] = $startf;
		$trrow[] = ( $goal != 0 ? $endf : "<del>".$endf."</del>" );
		$trrow[] = ( $goal != 0 ? $timeinair : "<del>".$timeinair."</del>" );
		$trrow[] = ( $speed != 0 ? number_format((float)$speed,2) : "" );
		if ($tasStoppedTime != '')
		{
			$alt = ( $lastalt - $goalalt >= 0 ? "+".($lastalt - $goalalt) : "");
			#strikesout if pilot made ESS
			$trrow[] = ( !$end ? $alt : "<del>".$alt."</del>" );
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
		if ($isadmin and $extComp != 1) 
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
    }
    
    if ($isadmin and $extComp != 1) 
    {
        $trrow[] = fbut("submit", "tardel",  $traPk, "del");
        $trrow[] = fbut("submit", "tarup",  $tarPk, "up");
        $trrow[] = $comment;
    }

    $trtab[] = $trrow;

    $count++;
}
echo ftable($trtab, "class='format taskresult'", '' , '');

if ($isadmin and $extComp != 1)
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
