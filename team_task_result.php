<?php
require 'authorisation.php';
require 'hc.php';
require 'format.php';


//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

$link = db_connect();

function  handicap_result($tasPk, $link)
{
    $query = "select max(TR.tarScore) as maxScore from tblTaskResult TR where TR.tasPk=$tasPk";
    // $result = mysql_query($query) or die('Team handicap query failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Team handicap query failed: ' . mysqli_connect_error());
    $maxscore = 1000;
//    $row = mysql_fetch_array($result);
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    if ($row)
    {
        $maxscore = $row['maxScore'];
    }

    $query = "select TM.teaPk,TM.teaName,P.pilLastName,P.pilFirstName,P.pilPk,TR.tarScore-H.hanHandicap*$maxscore as handiscore from tblTaskResult TR, tblTask TK, tblTrack K, tblPilot P, tblTeam TM, tblTeamPilot TP, tblHandicap H, tblCompetition C where TP.teaPk=TM.teaPk and P.pilPk=TP.pilPk and H.comPk=C.comPk and C.comPk=TK.comPk and K.traPk=TR.traPk and K.pilPk=P.pilPk and H.pilPk=P.pilPk and TK.tasPk=$tasPk and TR.tasPk=TK.tasPk and TM.comPk=C.comPk order by TM.teaPk";
    // $result = mysql_query($query) or die('Team handicap query failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Team handicap query failed: ' . mysqli_connect_error());
    //    $row = mysql_fetch_array($result);
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    $htable = [];
    $hres = [];
    $teaPk = 0;
    $total = 0;
    // FIX: sort team results ..
    // $htable[] = array( fb("Place"), fb("Team"), fb("Pilot"), fb("Handicap"), fb("Score") );
    while ($row)
    {
        if ($teaPk != $row['teaPk'])
        {
            if ($teaPk == 0)
            {
                $teaPk = $row['teaPk'];
            }
            else
            {
                // wrap up last one
                $htable[] = array('', fb('Total'), fb("$total"));
                $htable[] = array('', '', '');
                $team = $row['teaName'];
                $hres["${total}${team}"] = $htable;
                $total = 0;
                $htable = [];
                $teaPk = $row['teaPk'];
            }
        }

        if ($row['handiscore'] > $maxscore)
        {
            $row['handiscore'] = $maxscore;
        }
        if ($total == 0)
        {
            $htable[] = array( fb($row['teaName']),  $row['pilFirstName'] . ' ' . $row['pilLastName'], round($row['handiscore'],2));
        }
        else
        {
            $htable[] = array( '',  $row['pilFirstName'] . ' ' . $row['pilLastName'], round($row['handiscore'],2));
        }
        $total = round($total + $row['handiscore'],2);
        //    $row = mysql_fetch_array($result);
    	$row = mysqli_fetch_array($result, MYSQLI_BOTH);
    }

    $htable[] = array('', fb('Total'), fb("$total"));
    $htable[] = array('', '', '');
    $team = $row['teaName'];
    $hres["${total}${team}"] = $htable;
    krsort($hres, SORT_NUMERIC);

    $htable = [];
    foreach ($hres as $res => $pils)
    {
        foreach ($pils as $row)
        {
            $htable[] = $row;
        }
    }

    echo ftable($htable, "border=\"5\" cellpadding=\"3\" alternate-colours=\"yes\" align=\"center\"", array('class="l"', 'class="d"'), '');
}

function aggregate_result($tasPk, $teamsize, $link)
{
    $query = "select TM.teaPk,TM.teaName,P.pilLastName,P.pilFirstName,P.pilPk,TR.tarScore*TP.tepModifier as tepscore from tblTaskResult TR, tblTask TK, tblTrack K, tblPilot P, tblTeam TM, tblTeamPilot TP, tblCompetition C where TP.teaPk=TM.teaPk and P.pilPk=TP.pilPk and C.comPk=TK.comPk and K.traPk=TR.traPk and K.pilPk=P.pilPk and TK.tasPk=$tasPk and TR.tasPk=TK.tasPk and TM.comPk=C.comPk order by TM.teaPk,TR.tarScore*TP.tepModifier desc";
    // $result = mysql_query($query) or die('Team aggregate query failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Team aggregate query failed: ' . mysqli_connect_error());
    //    $row = mysql_fetch_array($result);
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    $htable = [];
    $hres = [];
    $teaPk = 0;
    $total = 0;
    $size = 0;
    while ($row)
    {
        if ($teaPk != $row['teaPk'])
        {
            if ($teaPk == 0)
            {
                $teaPk = $row['teaPk'];
            }
            else
            {
                // wrap up last one
                $htable[] = array('', fb('Total'), fb("$total"));
                $htable[] = array('', '', '');
                $team = $row['teaName'];
                $hres["${total}${team}"] = $htable;
                $total = 0;
                $size = 0;
                $htable = [];
                $teaPk = $row['teaPk'];
            }
        }

        if ($row['tepscore'] > 1000)
        {
            $row['tepscore'] = 1000;
        }
        if ($total == 0)
        {
            $htable[] = array( fb($row['teaName']),  $row['pilFirstName'] . ' ' . $row['pilLastName'], round($row['tepscore'],2));
        }
        else
        {
            $htable[] = array( '',  $row['pilFirstName'] . ' ' . $row['pilLastName'], round($row['tepscore'],2));
        }
        if ($size < $teamsize)
        {
            $total = round($total + $row['tepscore'],2);
            $size = $size + 1;
        }
        //    $row = mysql_fetch_array($result);
    	$row = mysqli_fetch_array($result, MYSQLI_BOTH);
    }

    $htable[] = array('', fb('Total'), fb("$total"));
    $htable[] = array('', '', '');
    $team = $row['teaName'];
    $hres["${total}${team}"] = $htable;
    krsort($hres, SORT_NUMERIC);

    $htable = [];
    foreach ($hres as $res => $pils)
    {
        foreach ($pils as $row)
        {
            $htable[] = $row;
        }
    }

    echo ftable($htable, "border=\"5\" cellpadding=\"3\" alternate-colours=\"yes\" align=\"center\"", array('class="l"', 'class="d"'), '');
}

$comPk = intval($_REQUEST['comPk']);

$usePk = check_auth('system');
$link = db_connect();
$tasPk = intval($_REQUEST['tasPk']);
$isadmin = is_admin('admin',$usePk,$comPk);

if (array_key_exists('score', $_REQUEST))
{
    $out = '';
    $retv = 0;
    exec(BINDIR . "team_score.pl $tasPk", $out, $retv);
}

if (array_key_exists('tarup', $_REQUEST))
{
    $tarPk = intval($_REQUEST['tarup']);
    $flown = addslashes($_REQUEST["flown$tarPk"]) * 1000;
    $penalty = addslashes($_REQUEST["penalty$tarPk"]);
    $resulttype = 'lo';
    if (0 + $flown == 0) 
    {
        $resulttype = 'dnf';
    }

    $query = "update tblTeamResult set tarDistance=$flown, tarPenalty=$penalty, tarResultType='$resulttype' where tarPk=$tarPk";
    // $result = mysql_query($query) or die('Team Result update failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Team results update failed: ' . mysqli_connect_error());
    # recompute every time?
    $out = '';
    $retv = 0;
    exec(BINDIR . "task_score.pl $tasPk", $out, $retv);
}

if (array_key_exists('addflight', $_REQUEST))
{
    $fai = addslashes($_REQUEST['fai']);
    $query = "select pilPk from tblPilot where pilHGFA='$fai'";
    // $result = mysql_query($query) or die('Query pilot failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query pilot failed: ' . mysqli_connect_error());

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

        $query = "insert into tblTrack (pilPk,traGlider,traDHV,traDate,traLength) values ($pilPk,'$glider','$dhv','$tasDate',$flown)";
        // $result = mysql_query($query) or die('Track Insert result failed: ' . mysql_error());
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Track Insert result failed: ' . mysqli_connect_error());

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

$query = "select C.*, T.* from tblCompetition C, tblTask T where T.tasPk=$tasPk and T.comPk=C.comPk";
// $result = mysql_query($query) or die('Task select failed: ' . mysql_error());
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task select failed: ' . mysqli_connect_error());
//    $row = mysql_fetch_array($result);
$row = mysqli_fetch_array($result, MYSQLI_BOTH);
if ($row)
{
    $comName = $row['comName'];
    $comPk = $row['comPk'];
    $comTeamScoring = $row['comTeamScoring'];
    $comTeamSize = $row['comTeamSize'];
    $tasName = $row['tasName'];
    $tasDate = $row['tasDate'];
    $tasTaskType = $row['tasTaskType'];
    $tasStartTime = substr($row['tasStartTime'],11);
    $tasFinishTime = substr($row['tasFinishTime'],11);
    $tasDistance = round($row['tasDistance']/1000,2);
    $tasQuality = round($row['tasQuality'],2);
    $tasDistQuality = round($row['tasDistQuality'],2);
    $tasTimeQuality = round($row['tasTimeQuality'],2);
    $tasLaunchQuality = round($row['tasLaunchQuality'],2);
    $tasShortest = round($row['tasShortRouteDistance']/1000,2);
}

if ($isadmin)
{
    $hdname = "<a href=\"task.php?comPk=$comPk&tasPk=$tasPk\">$tasName</a> - <a href=\"competition.php?comPk=$comPk\">$comName</a>";
}
else
{
    $hdname =  "$tasName - $comName";
}
hcheader($hdname,2, "<b>Teams</b> - $tasDate");
echo "<div id=\"content\">";

$tinfo = [];
$tinfo[] = array( fb("Date"), $tasDate, fb("Start"), "$tasStartTime UTC", fb("End"), "$tasFinishTime UTC" );
$tinfo[] = array( fb("Type"), $tasTaskType,fb("WP Dist"), "$tasDistance km", fb("Short Dist"), "$tasShortest km" );
$tinfo[] = array( fb("Quality Dist"), $tasDistQuality, fb("Time"), $tasTimeQuality, fb("Launch"), $tasLaunchQuality );

echo "<br>";
echo ftable($tinfo, "border=\"5\" cellpadding=\"3\" alternate-colours=\"yes\" align=\"center\"", array('class="l"', 'class="d"'), '');

echo "<br>";

if ($comTeamScoring == "handicap")
{
    return handicap_result($tasPk, $link);
}
else if ($comTeamScoring == "aggregate")
{
    return aggregate_result($tasPk, $comTeamSize, $link);
}


if ($isadmin)
{
    echo "<form action=\"team_task_result.php?comPk=$comPk&tasPk=$tasPk\" name=\"resultupdate\" method=\"post\">"; 
}

$htable = [];
$htable[] = array( fb("Team"), fb("Pilot"), fb("Time"), fb("Dist"), fb("Total") );
$count = 1;

$sql = "select TR.*, P.*, L.*, TTR.* from tblTeamResult TR, tblTeam P, tblTeamPilot TP, tblPilot L, tblTaskResult TTR, tblTrack TK where TP.teaPk=P.teaPk and TP.pilPk=L.pilPk and TR.tasPk=$tasPk and TTR.traPk=TK.traPk and P.teaPk=TR.teaPk and TK.pilPk=TP.pilPk and TTR.tasPk=TR.tasPk and TK.traPk=TTR.traPk order by TR.terScore desc, P.teaName";

// $result = mysql_query($sql,$link) or die('Team Result Selection failed: ' . mysql_error());
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Team Result Selection failed: ' . mysqli_connect_error());
$lastscore = 0;
$lasttm = 0;
// while ($row = mysql_fetch_array($result))
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $traPk = $row['traPk'];
    if ($row['teaPk'] != $lasttm)
    {
        $tm = '';
        if ($row['terES'] > 0)
        {
            $tm = ftime($row['terES'] - $row['terSS']);
        }
        $htable[] = array( fb($row['teaName']), '', $tm, round($row['terDistance']/1000,2), fb(round($row['terScore'])) );
        $lasttm = $row['teaPk'];
    }
    if ($row['tarScore'] > 0)
    {
        if ($row['tarES'] > 0)
        {
            $tm = ftime($row['tarES'] - $row['tarSS']);
        }
        else
        {
            $tm = '';
        }
        $htable[] = array( '', "<a href=\"tracklog_map.php?trackid=$traPk&comPk=$comPk\">" . $row['pilFirstName'] . ' ' . $row['pilLastName'] . "</a>", $tm, round($row['tarDistance']/1000,2) );
    }

#    if ($isadmin) 
#    {
#        echo "<td>$timeinair</td><td><input name=\"flown$tarPk\" type=\"text\" value=\"$tardist\" size=4></td><td><input name=\"penalty$tarPk\" type=\"text\" value=\"$penalty\" size=4></td>\n";
#    }
#    else
#    {
#        echo "<td>$timeinair</td><td>$tardist</td><td>$penalty</td>\n";
#    }
#    if ($isadmin) 
#    {
#        echo "<td><button type=\"submit\" name=\"tarup\" value=\"$tarPk\">up</button></td>";     
#    }

    $count++;
}
echo ftable($htable, "border=\"5\" cellpadding=\"3\" alternate-colours=\"yes\" align=\"center\"", array('class="l"', 'class="d"'), '');

if ($isadmin)
{
    // FIX: enable 'manual' pilot flight addition
    echo "<br>"; 
    echo "FAI: <input type=\"text\" name=\"fai\" size=6>";
    echo "Type: ";
    output_select('resulttype', 'lo', array('abs', 'dnf', 'lo', 'goal' ));
    echo "Dist: <input type=\"text\" name=\"flown\" size=4>";
    echo "DHV&nbsp;";
    output_select('dhv', 'competition', array('1', '1/2', '2', '2/3', 'competition' ));
    echo "Penalty: <input type=\"text\" name=\"penalty\" size=4>";
    echo "<button type=\"submit\" name=\"addflight\" value=\"$tarPk\">Manual Addition</button><br>";     

    echo "</form>";
}

?>
</div>
</div>
</body>
</html>

