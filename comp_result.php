<?php
function taskcmp($a, $b)
{
    if (!is_array($a)) return 0;
    if (!is_array($b)) return 0;

    if ($a['tname'] == $b['tname']) 
    {
        return 0;
    }
    return ($a['tname'] < $b['tname']) ? -1 : 1;
}
function olc_result($link,$top,$restrict)
{
    $lastpil = 0;
    $toptasks = array();
    $topscores = array();

    $sql = "SELECT P.*, T.traPk, T.traScore FROM tblTrack T, tblPilot P, tblComTaskTrack CTT, tblCompetition C where CTT.comPk=C.comPk and CTT.traPk=T.traPk and T.pilPk=P.pilPk and T.traScore is not null $restrict order by P.pilPk, T.traScore desc";
    $result = mysql_query($sql,$link) or die('Top score: ' . mysql_error());

    while ($row = mysql_fetch_array($result))
    {
        // another pilot .. finish it off
        $pilPk = $row['pilPk'];
        if (!array_key_exists($pilPk, $toptasks))
        {
            $toptasks[$pilPk] = array();
        }
        array_push($toptasks[$pilPk], $row);
    }

    // do the totals ...
    foreach ($toptasks as $pilPk => $scores)
    {
        // cut to max ..
        $scores = array_slice($scores,0,$top);
        $total = 0;

        foreach ($scores as $row)
        {
            $total = $total + $row['traScore'];
            $first = $row['pilFirstName'];
            $last = $row['pilLastName'];
        }

        $total = $total . $last;
        $topscores[$total] = array( 
                    'total' => $total,
                    'tasks' => $scores,
                    'pilpk' => $pilPk,
                    'firstname' => $first,
                    'lastname' => $last
            );
    }

    krsort($topscores, SORT_NUMERIC);

    return $topscores;
}

function team_gap_result($comPk, $how, $param)
{
    $sql = "select TK.*,TR.*,P.* from tblTeamResult TR, tblTask TK, tblTeam P, tblCompetition C where C.comPk=$comPk and TR.tasPk=TK.tasPk and TK.comPk=C.comPk and P.teaPk=TR.teaPk order by P.teaPk, TK.tasPk";
    $result = mysql_query($sql) or die('Task result query failed: ' . mysql_error());
    $results = array();
    while ($row = mysql_fetch_array($result))
    {
        $score = round($row['terScore']);
        $validity = $row['tasQuality'] * 1000;
        $pilPk = $row['teaPk'];
        $tasName = $row['tasName'];
    
        if (!$results[$pilPk])
        {
            $results[$pilPk] = array();
            $results[$pilPk]['name'] = $row['teaName'];
        }
        //echo "pilPk=$pilPk tasname=$tasName, result=$score<br>\n";
        $perf = 0;
        if ($how == 'ftv') 
        {
            $perf = 0;
            if ($validity > 0)
            {
                $perf = round($score / $validity, 3) * 1000;
            }
        }
        else
        {
            $perf = round($score, 0);
        }
        $results[$pilPk]["${perf}${tasName}"] = array('score' => $score, 'validity' => $validity, 'tname' => $tasName);
    }

    // Do the scoring totals (FTV/X or Y tasks etc)
    $sorted = array();
    foreach ($results as $pil => $arr)
    {
        krsort($arr, SORT_NUMERIC);

        $pilscore = 0;
        if ($how != 'ftv')
        {
            # Max rounds scoring
            $count = 0;
            foreach ($arr as $perf => $taskresult)
            {
                if ($perf == 'name') 
                {
                    continue;
                }
                if ($count < $param)
                {
                    $arr[$perf]['perc'] = 100;
                    $pilscore = $pilscore + $taskresult['score'];
                }
                else
                {
                    $arr[$perf]['perc'] = 0;
                }
                $count++;
                
            }
        }
        else
        {
            # FTV scoring
            $pilvalid = 0;
            foreach ($arr as $perf => $taskresult)
            {
                if ($perf == 'name') 
                {
                    continue;
                }

                //echo "pil=$pil perf=$perf valid=", $taskresult['validity'], " score=", $taskresult['score'], "<br>";
                if ($pilvalid < $param)
                {
                    $gap = $param - $pilvalid;
                    $perc = 0;
                    if ($taskresult['validity'] > 0)
                    {
                        $perc = $gap / $taskresult['validity'];
                    }
                    if ($perc > 1)
                    {
                        $perc = 1;
                    }
                    $pilvalid = $pilvalid + $taskresult['validity'] * $perc;
                    $pilscore = $pilscore + $taskresult['score'] * $perc;
                    $arr[$perf]['perc'] = $perc * 100;
                }
            }   
        }
        // resort arr by task?
        uasort($arr, "taskcmp");
        #echo "pil=$pil pilscore=$pilscore<br>";
        foreach ($arr as $key => $res)
        {
            if ($key != 'name')
            {
                $arr[$res['tname']] = $res;
                unset($arr[$key]);
            }
        }
        $pilscore = round($pilscore,0);
        $sorted["${pilscore}!${pil}"] = $arr;
    }

    krsort($sorted, SORT_NUMERIC);
    return $sorted;
}


function team_agg_result($comPk, $teamsize)
{
    $query = "select TM.teaPk,TK.tasPk,TK.tasName,TM.teaName,P.pilLastName,P.pilFirstName,P.pilPk,TR.tarScore*TP.tepModifier as tepscore from tblTaskResult TR, tblTask TK, tblTrack K, tblPilot P, tblTeam TM, tblTeamPilot TP, tblCompetition C where TP.teaPk=TM.teaPk and P.pilPk=TP.pilPk and C.comPk=TK.comPk and K.traPk=TR.traPk and K.pilPk=P.pilPk and TR.tasPk=TK.tasPk and TM.comPk=C.comPk and C.comPk=$comPk order by TM.teaPk,TK.tasPk,TR.tarScore*TP.tepModifier desc";
    $result = mysql_query($query) or die('Team aggregate query failed: ' . mysql_error());
    $row = mysql_fetch_array($result);
    $htable = array();
    $hres = array();
    $sorted = array();
    $teaPk = 0;
    $tasPk = 0;
    $tastot = 0;
    $total = 0;
    $size = 0;
    while ($row)
    {
        //$tasName = $row['tasName'];
        if ($tasPk != $row['tasPk'])
        {
            if ($size != 0)
            {
                $arr["${tasName}"] = array('score' => round($tastotal,0), 'perc' => 100, 'tname' => $tasName);
            }
            $tasName = $row['tasName'];
            $size = 0;
            $tastotal = 0;
            $tasPk = $row['tasPk'];
            //$arr = array();
        }
        if ($teaPk != $row['teaPk'])
        {
            if ($teaPk == 0)
            {
                $teaPk = $row['teaPk'];
                $tasPk = $tow['tasPk'];
                $arr = array();
                $arr['name'] = $row['teaName'];
            }
            else
            {
                // wrap up last one
                $total = round($total,0);
                $sorted["${total}!${teaPk}"] = $arr;
                $tastotal = 0;
                $total = 0;
                $size = 0;
                $arr = array();
                $arr['name'] = $row['teaName'];
                $teaPk = $row['teaPk'];
            }
        }

        if ($size < $teamsize)
        {
            $total = round($total + $row['tepscore'],2);
            $tastotal = round($tastotal + $row['tepscore'],2);
            $size = $size + 1;
        }
        $row = mysql_fetch_array($result);
    }

    // wrap up last one
    $total = round($total,0);
    $arr["${tasName}"] = array('score' => round($tastotal,0), 'perc' => 100, 'tname' => $tasName);
    $sorted["${total}!${teaPk}"] = $arr;

    krsort($sorted, SORT_NUMERIC);
    return $sorted;
}

function team_handicap_result($comPk,$how,$param)
{
    $query = "select T.tasPk, T.tasName, max(TR.tarScore) as maxScore from tblTaskResult TR, tblTask T where T.tasPk=TR.tasPk and T.comPk=$comPk group by TR.tasPk";
    $result = mysql_query($query) or die('Team aggregate query failed: ' . mysql_error());
    $row = mysql_fetch_array($result);
    $tinfo = array();
    while ($row)
    {
        $tinfo[$row['tasPk']] = array( 'name' => "<a href=\"team_task_result.php?tasPk=" . $row['tasPk'] . "\">" . $row['tasName'] . "</a>", 'maxscore' => $row['maxScore']);
        $row = mysql_fetch_array($result);
    }

    $hteams = array();
    $count = 0;
    foreach ($tinfo as $task => $tasinfo)
    {
        $maxscore = intval($tasinfo['maxscore']);
        if ($maxscore < 1)
        {
            next;
        }
        $query = "select TM.teaPk,TK.tasPk,TK.tasName,TM.teaName,sum(TR.tarScore-H.hanHandicap*$maxscore) as handiscore from tblTaskResult TR, tblTask TK, tblTrack K, tblPilot P, tblTeam TM, tblTeamPilot TP, tblHandicap H, tblCompetition C where TP.teaPk=TM.teaPk and P.pilPk=TP.pilPk and C.comPk=TK.comPk and K.traPk=TR.traPk and K.pilPk=P.pilPk and H.pilPk=P.pilPk and TR.tasPk=TK.tasPk and TM.comPk=C.comPk and TK.tasPk=$task and H.comPk=$comPk group by TM.teaPk";
        $result = mysql_query($query) or die('Team handicap query failed: ' . mysql_error());
        $row = mysql_fetch_array($result);
        while ($row)
        {
            //echo "task=$task teaPk=" . $row['teaPk'] . "=" . $row['handiscore'] . "<br>";
            if (array_key_exists($row['teaPk'], $hteams))
            {
                $htable = $hteams[$row['teaPk']];
                $htable['scores'][$count] = $row['handiscore'];
                $htable['total'] = round($htable['total'] + $row['handiscore'],0);
                $hteams[$row['teaPk']] = $htable;
            }
            else
            {
                $htable = array();
                $htable['team'] = $row['teaName'];
                $htable['scores'] = array();
                for ($i = 0; $i < $count; $i++)
                {
                    $htable['scores'][$i] = 0;
                }
                $htable['scores'][$count] = $row['handiscore'];
                $htable['total'] =  round($row['handiscore'],0);
                $hteams[$row['teaPk']] = $htable;
            }

            $row = mysql_fetch_array($result);
        }
        $count++;
    
    }
    $hres = array();
    foreach ($hteams as $res)
    {
        $total = $res['total'];
        $team = $res['team'];
        $hres["${total}${team}"] = $res;
    }
    krsort($hres, SORT_NUMERIC);

    $sorted = array();
    $place = 1;
    $htable = array();
    $title = array( fb("Res"), fb("Team"), fb("Total"));
    foreach ($tinfo as $task => $tasinfo)
    {
        $title[] = fb($tasinfo['name']);
    }
    $htable[] = $title;

    foreach ($hres as $res => $pils)
    {
        $row = array( fb("$place"), $pils['team'], $pils['total'] );
        foreach ($pils['scores'] as $tas => $sco)
        {
            $row[] = round($sco,0);
        }
        $htable[] = $row;
        $place = $place + 1;
    }

    echo ftable($htable, "border=\"0\" cellpadding=\"3\" alternate-colours=\"yes\" align=\"center\"", array('class="l"', 'class="d"'), '');
}

function overall_handicap($comPk, $how, $param, $cls)
{
    $sql = "select T.tasPk, max(TR.tarScore) as maxScore from tblTask T, tblTaskResult TR where T.tasPk=TR.tasPk and T.comPk=$comPk group by T.tasPk";
    $result = mysql_query($sql) or die('Handicap maxscore failed: ' . mysql_error());
    $maxarr = array();
    while ($row = mysql_fetch_array($result))
    {
        $maxarr[$row['tasPk']] = $row['maxScore'];
    }

    $sql = "select P.*,TK.*, TR.*, H.* from tblTaskResult TR, tblTask TK, tblTrack K, tblPilot P, tblHandicap H, tblCompetition C where H.comPk=C.comPk and C.comPk=TK.comPk and K.traPk=TR.traPk and K.pilPk=P.pilPk and H.pilPk=P.pilPk and H.comPk=TK.comPk and TK.comPk=$comPk and TR.tasPk=TK.tasPk order by P.pilPk, TK.tasPk";
    #$sql = "select TK.*,TR.*,P.* from tblTaskResult TR, tblTask TK, tblTrack T, tblPilot P, tblCompetition C where C.comPk=$comPk and TK.comPk=C.comPk and TK.tasPk=TR.tasPk and TR.traPk=T.traPk and T.traPk=TR.traPk and P.pilPk=T.pilPk $cls order by P.pilPk, TK.tasPk";

    $result = mysql_query($sql) or die('Task result query failed: ' . mysql_error());
    $results = array();
    while ($row = mysql_fetch_array($result))
    {
        $tasPk = $row['tasPk'];
        $score = round($row['tarScore'] - $row['hanHandicap'] * $maxarr[$tasPk]);
        if ($row['tarResultType'] == 'abs' || $row['tarResultType'] == 'dnf')
        {
            $score = 0;
        }
        $validity = $row['tasQuality'] * 1000;
        $pilPk = $row['pilPk'];
        $tasName = $row['tasName'];
    
        if (!$results[$pilPk])
        {
            $results[$pilPk] = array();
            $results[$pilPk]['name'] = $row['pilFirstName'] . ' ' . $row['pilLastName'];
        }
        //echo "pilPk=$pilPk tasname=$tasName, result=$score<br>\n";
        $perf = 0;
        if ($how == 'ftv') 
        {
            $perf = 0;
            if ($validity > 0)
            {
                $perf = round($score / $validity, 3) * 1000;
            }
        }
        else
        {
            $perf = round($score, 0);
        }
        $results[$pilPk]["${perf}${tasName}"] = array('score' => $score, 'validity' => $validity, 'tname' => $tasName);
    }

    return filter_results($comPk, $how, $param, $results);
}

function comp_result($comPk, $how, $param, $cls)
{
    $sql = "select TK.*,TR.*,P.*,T.traGlider from tblTaskResult TR, tblTask TK, tblTrack T, tblPilot P, tblCompetition C where C.comPk=$comPk and TK.comPk=C.comPk and TK.tasPk=TR.tasPk and TR.traPk=T.traPk and T.traPk=TR.traPk and P.pilPk=T.pilPk $cls order by P.pilPk, TK.tasPk";
    $result = mysql_query($sql) or die('Task result query failed: ' . mysql_error());
    $results = array();
    while ($row = mysql_fetch_array($result))
    {
        $score = round($row['tarScore']);
        $validity = $row['tasQuality'] * 1000;
        $pilPk = $row['pilPk'];
        $tasName = $row['tasName'];
        $nation = $row['pilNationCode'];
        $pilnum = $row['pilHGFA'];
        $civlnum = $row['pilCIVL'];
        $glider = $row['traGlider'];
    
        if (!array_key_exists($pilPk,$results) || !$results[$pilPk])
        {
            $results[$pilPk] = array();
            $results[$pilPk]['name'] = $row['pilFirstName'] . ' ' . $row['pilLastName'];
            $results[$pilPk]['hgfa'] = $pilnum;
            $results[$pilPk]['civl'] = $civlnum;
            $results[$pilPk]['nation'] = $nation;
            $results[$pilPk]['glider'] = $glider;
        }
        //echo "pilPk=$pilPk tasname=$tasName, result=$score<br>\n";
        $perf = 0;
        if ($how == 'ftv') 
        {
            $perf = 0;
            if ($validity > 0)
            {
                $perf = round($score / $validity, 3) * 1000;
            }
        }
        else
        {
            $perf = round($score, 0);
        }
        $results[$pilPk]["${perf}${tasName}"] = array('score' => $score, 'validity' => $validity, 'tname' => $tasName);
    }

    return filter_results($comPk, $how, $param, $results);
}

function filter_results($comPk, $how, $param, $results)
{
    // Do the scoring totals (FTV/X or Y tasks etc)
    $sorted = array();
    foreach ($results as $pil => $arr)
    {
        krsort($arr, SORT_NUMERIC);

        $pilscore = 0;
        if ($how != 'ftv')
        {
            # Max rounds scoring
            $count = 0;
            foreach ($arr as $perf => $taskresult)
            {
                //if ($perf == 'name') 
                if (ctype_alpha($perf))
                {
                    continue;
                }
                if ($count < $param)
                {
                    $arr[$perf]['perc'] = 100;
                    $pilscore = $pilscore + $taskresult['score'];
                }
                else
                {
                    $arr[$perf]['perc'] = 0;
                }
                $count++;
                
            }
        }
        else
        {
            # FTV scoring
            $pilvalid = 0;
            foreach ($arr as $perf => $taskresult)
            {
                //if ($perf == 'name') 
                if (ctype_alpha($perf))
                {
                    continue;
                }

                //echo "pil=$pil perf=$perf valid=", $taskresult['validity'], " score=", $taskresult['score'], "<br>";
                if ($pilvalid < $param)
                {
                    $gap = $param - $pilvalid;
                    $perc = 0;
                    if ($taskresult['validity'] > 0)
                    {
                        $perc = $gap / $taskresult['validity'];
                    }
                    if ($perc > 1)
                    {
                        $perc = 1;
                    }
                    $pilvalid = $pilvalid + $taskresult['validity'] * $perc;
                    $pilscore = $pilscore + $taskresult['score'] * $perc;
                    $arr[$perf]['perc'] = $perc * 100;
                }
            }   
        }
        // resort arr by task?
        uasort($arr, "taskcmp");
        #echo "pil=$pil pilscore=$pilscore<br>";
        foreach ($arr as $key => $res)
        {
            #echo "key=$key<br>";
            #if ($key != 'name')
            if (ctype_digit(substr($key,0,1)))
            {
                $arr[$res['tname']] = $res;
                unset($arr[$key]);
            }
        }
        $pilscore = round($pilscore,0);
        $sorted["${pilscore}!${pil}"] = $arr;
    }

    krsort($sorted, SORT_NUMERIC);
    return $sorted;
}

require_once 'authorisation.php';
require_once 'format.php';
require 'hc.php';

$comPk = intval($_REQUEST['comPk']);
$start = reqival('start');
$class = reqsval('class');
if ($start < 0)
{
    $start = 0;
}
$link = db_connect();
$title = 'highcloud.net';

$query = "SELECT T.*,F.* FROM tblCompetition T left outer join tblFormula F on F.comPk=T.comPk where T.comPk=$comPk";
$result = mysql_query($query) or die('Comp query failed: ' . mysql_error());
$row = mysql_fetch_array($result);
if ($row)
{
    $comName = $row['comName'];
    $title = $row['comName'];
    $comDateFrom = substr($row['comDateFrom'],0,10);
    $comDateTo = substr($row['comDateTo'],0,10);
    #$comPk = $row['comPk'];
    $comOverall = $row['comOverallScore'];
    $comOverallParam = $row['comOverallParam'];
    $comDirector = $row['comMeetDirName'];
    $comLocation = $row['comLocation'];
    $comFormula = $row['forClass'] . ' ' . $row['forVersion'];
    $comSanction = $row['comSanction'];
    $comOverall = $row['comOverallScore'];
    $comTeamScoring = $row['comTeamScoring'];
    $comCode = $row['comCode'];
    $comClass = $row['comClass'];
    $comType = $row['comType'];
    $forNomGoal = $row['forNomGoal'];
    $forMinDistance = $row['forMinDistance'];
    $forNomDistance = $row['forNomDistance'];
    $forNomTime = $row['forNomTime'];
}


$fdhv= '';
$classstr = '';
if (array_key_exists('class', $_REQUEST))
{
    $cval = intval($_REQUEST['class']);
    if ($comClass == "HG")
    {
        $carr = array ( "'floater'", "'kingpost'", "'open'", "'rigid'"       );
        $cstr = array ( "Floater", "Kingpost", "Open", "Rigid", "Women", "Seniors", "Juniors" );
    }
    else
    {
        $carr = array ( "'1/2'", "'2'", "'2/3'", "'competition'"       );
        $cstr = array ( "Fun", "Sport", "Serial", "Open", "Women", "Seniors", "Juniors" );
    }
    $classstr = "<b>" . $cstr[intval($_REQUEST['class'])] . "</b> - ";
    if ($cval == 4)
    {
        $fdhv = "and P.pilSex='F'";
    }
    else if ($cval == 5)
    {
        $fdhv = "and P.pilBirthdate < date_sub(C.comDateFrom, INTERVAL 50 YEAR)"; 
    }
    else if ($cval == 6)
    {
        $fdhv = "and P.pilBirthdate > date_sub(C.comDateFrom, INTERVAL 35 YEAR)";
    }
    else
    {
        $fdhv = $carr[intval($_REQUEST['class'])];
        $fdhv = "and T.traDHV<=$fdhv ";
    }
}

$embed = reqsval('embed');
if ($embed == '')
{
    hcheader($title, 2, "$classstr $comDateFrom - $comDateTo");

    echo "<div id=\"content\">";
    //echo "<div id=\"text\" style=\"overflow: auto; max-width: 600px;\">";
    echo "<div id=\"text\" style=\"overflow: auto;\">";
}
else
{
    echo "<link HREF=\"$embed\" REL=\"stylesheet\" TYPE=\"text/css\">";
    echo "</head><body>";
}

//echo "<h1>Details</h1>";
// Determine scoring params / details ..

$tasTotal = 0;
$query = "select count(*) from tblTask where comPk=$comPk";
$result = mysql_query($query); // or die('Task total failed: ' . mysql_error());
if ($result)
{
    $tasTotal = mysql_result($result, 0, 0);
}
if ($comOverall == 'all')
{
    # total # of tasks
    $comOverallParam = $tasTotal;
    $overstr = "All rounds";
}
else if ($comOverall == 'round')
{
    $overstr = "$comOverallParam rounds";
}
else if ($comOverall == 'round-perc')
{
    $comOverallParam = round($tasTotal * $comOverallParam / 100, 0);
    $overstr = "$comOverallParam rounds";
}
else if ($comOverall == 'ftv')
{
    $sql = "select sum(tasQuality) as totValidity from tblTask where comPk=$comPk";
    $result = mysql_query($sql) or die('Task validity query failed: ' . mysql_error());
    $totalvalidity = round(mysql_result($result, 0, 0) * $comOverallParam * 10,0);
    $overstr = "FTV $comOverallParam% ($totalvalidity pts)";
    $comOverallParam = $totalvalidity;
}

//echo ftable($detarr, '', '', '');

if ($class == "9")
{
    echo "<h1>Handicap Results</h1>";
}
else
{
    echo "<h1>Results</h1>";
}

$today = getdate();
$tdate = sprintf("%04d-%02d-%02d", $today['year'], $today['mon'], $today['mday']);
if ($tdate == $comDateTo)
{
    $usePk = check_auth('system');
    $link = db_connect();
    $isadmin = is_admin('admin',$usePk,$comPk);
    
    if ($isadmin == 0)
    {
        echo "<h2>Results currently unavailable</h2>";    
        exit(0);
    }
}

$rtable = array();
$rdec = array();

if ($comClass == "HG")
{
    $classopts = array ( 'open' => '', 'floater' => '&class=0', 'kingpost' => '&class=1', 
        'hg-open' => '&class=2', 'rigid' => '&class=3', 'women' => '&class=4', 'masters' => '&class=5', 'teams' => '&class=8' );
}
else
{
    $classopts = array ( 'open' => '', 'fun' => '&class=0', 'sports' => '&class=1', 
        'serial' => '&class=2', 'women' => '&class=4', 'masters' => '&class=5', 'teams' => '&class=8', 'handicap' => '&class=9' );
}
$cind = '';
if ($class != '')
{
    $cind = "&class=$class";
}
$copts = array();
foreach ($classopts as $text => $url)
{
    if ($text == 'teams' && $comTeamScoring == 'aggregate')
    {
        # Hack for now
        $copts[$text] = "team_comp_result.php?comPk=$comPk";
    }
    else
    {
        $copts[$text] = "comp_result.php?comPk=$comPk$url";
    }
}

$rdec[] = 'class="h"';
$rdec[] = 'class="h"';
if (reqival('id') == 1)
{
    $hdr = array( fb('Res'),  fselect('class', "comp_result.php?comPk=$comPk$cind", $copts, ' onchange="document.location.href=this.value"'), fb('Nation'), fb('FAI'), fb('CIVL'), fb('Total') );
    $hdr2 = array( '', '', '', '', '', '' );
}
else
{
    $hdr = array( fb('Res'),  fselect('class', "comp_result.php?comPk=$comPk$cind", $copts, ' onchange="document.location.href=this.value"'), fb('Glider'), fb('Total') );
    $hdr2 = array( '', '', '', '' );
}

# find each task details
$alltasks = array();
$taskinfo = array();
$sorted = array();
if ($class == "8")
{
    if ($comTeamScoring == 'handicap')
    {
        team_handicap_result($comPk,$how,$param);
    }
}
else if ($comType == 'RACE' || $comType == 'Team-RACE' || $comType == 'Route')
{
    $query = "select T.* from tblTask T where T.comPk=$comPk order by T.tasDate";
    $result = mysql_query($query) or die('Task query failed: ' . mysql_error());
    while ($row = mysql_fetch_array($result))
    {
        $alltasks[] = $row['tasName'];
        $taskinfo[] = $row;
    }

    if ($comType == 'Team-RACE')
    {
        $sorted = team_gap_result($comPk, $comOverall, $comOverallParam);
        $subtask = 'team_';
    }
    else if ($class == "9")
    {
        $sorted = overall_handicap($comPk, $comOverall, $comOverallParam, $fdhv);
        $subtask = '';
    }
    else
    {
        $sorted = comp_result($comPk, $comOverall, $comOverallParam, $fdhv);
        $subtask = '';
    }

    foreach ($taskinfo as $row)
    {
        $tasName = $row['tasName'];
        $tasPk = $row['tasPk'];
        $tasDate = substr($row['tasDate'],0,10);
        $hdr[] = fb("<a href=\"${subtask}task_result.php?comPk=$comPk&tasPk=$tasPk\">$tasName</a>");
    }
    foreach ($taskinfo as $row)
    {
        $tasPk = $row['tasPk'];
        $hdr2[] = "<a href=\"route_map.php?comPk=$comPk&tasPk=$tasPk\">Map</a>";
    }
    $rtable[] = $hdr;
    $rtable[] = $hdr2;

    $lasttot = 0;
    $count = 1;
    foreach ($sorted as $pil => $arr)
    {
        $nxt = array();
        if ($count % 2)
        {
            $rdec[] = 'class="d"';
        }
        else
        {
            $rdec[] = 'class="l"';
        }
        $tot = 0 + $pil;
        if ($tot != $lasttot)
        {
            $nxt[] = $count;
            $nxt[] = $arr['name'];
        }
        else
        {
            $nxt[] = '';
            $nxt[] = $arr['name'];
        }
        if (array_key_exists('id', $_REQUEST) and ($_REQUEST['id'] == '1'))
        {
            $nxt[] = $arr['nation'];
            $nxt[] = $arr['hgfa'];
            $nxt[] = $arr['civl'];
        }
        else
        {
            $nxt[] = $arr['glider'];
        }
        $nxt[] = fb($tot);
        $lasttot = $tot;

        foreach ($alltasks as $num => $name)
        { 
            $score = 0;
            $perc = 100;
            if (array_key_exists($name, $arr))
            {
                $score = $arr[$name]['score'];
                $perc = round($arr[$name]['perc'], 0);
            }
            if (!$score)
            {
                $score = 0;
            }
            if ($perc == 100)
            {
                $nxt[] = $score;
            }
            else if ($perc > 0)
            {
                $nxt[] = "$score $perc%";
            }
            else
            {
                $nxt[] = "<del>$score</del>";
            }
        }
        $rtable[] = $nxt;
        $count++;
    }
    echo ftable($rtable, "border=\"0\" cellpadding=\"1\" alternate-colours=\"yes\" align=\"center\"", $rdec, '');
}
else
{
    $rtable[] = $hdr;
    $rtable[] = $hdr2;
    $top = 25;
    if (!$comOverallParam)
    {
        $comOverallParam = 4;
    }
    $restrict = '';
    if ($comPk == 1)
    {
        $restrict = " $fdhv";
    }
    elseif ($comPk > 1)
    {
        $restrict = " and CTT.comPk=$comPk $fdhv";
    }
    $sorted = olc_result($link, $comOverallParam, $restrict);
    $size = sizeof($sorted);

    #echo "<tr class=\"h\"><td><b>Place</b></td><td><b>Pilot</b></td><td><b>Total</b></td><td><b>Task 1</b1></td><td><b>Task 2</b></td><td><b>Task 3</b></td><td><b>Task 4</b></td></tr>\n";
    $count = $start+1;
    $sorted = array_slice($sorted,$start,$top+2);
    foreach ($sorted as $total => $row)
    {
        $nxt = array();
        if ($count % 2)
        {
            $rdec[] = 'class="d"';
        }
        else
        {
            $rdec[] = 'class="l"';
        }
        $name = $row['firstname'] . " " . $row['lastname'];
        $key = $row['pilpk'];
        $total = round($total/1000,2);
        $nxt[] = $count;
        $nxt[] = "<a href=\"index.php?pil=$key\">$name</a>";
        $nxt[] = $total;
        foreach ($row['tasks'] as $task)
        {
            $score = round($task['traScore']/1000,1);
            $id = $task['traPk'];
            $nxt[] = "<a href=\"tracklog_map.php?comPk=$comPk&trackid=$id\">$score</a>";
        }
        $count++;
        if ($count >= $top + $start + 2) 
        {
            break;
        }
        $rtable[] = $nxt;
    }
    echo ftable($rtable, "border=\"0\" cellpadding=\"1\" alternate-colours=\"yes\" align=\"center\"", $rdec, '');
    
    if ($count == 1)
    {
        echo "<b>No tracks submitted for $comName yet.</b>\n";
    }
    else 
    {
        if ($start >= 0)
        {
            echo "<b class=\"left\"><a href=\"comp_result.php?comPk=$comPk&start=" . ($start-$top) . "\">Prev 25</a></b>\n";
        }
        if ($count < $size)
        {
            echo "<b class=\"right\"><a href=\"comp_result.php?comPk=$comPk&start=" . ($count) . "\">Next 25</a></b>\n";
        }
    }

}

//echo "</table>";
if ($comOverall == 'ftv')
{
    echo "1. Click <a href=\"ftv.php?comPk=$comPk\">here</a> for an explanation of FTV<br>";
    echo "2. Scores in bold 100%, or indicated %, other scores not counted<br>";
}
if ($embed == '')
{
    // Only emit image if results table is "narrow"
    echo "</div>";
    echo "<div id=\"sideBar\">";

    echo "<h1>Comp Details</h1>";
    $detarr = array(
        array("<b>Location</b> ", "<i>$comLocation</i>"),
        array ("<b>Director</b> ", "<i>$comDirector</i>"),
        array("<i>$comDateFrom</i>", "<i>$comDateTo</i>")
    );

    if ($comType == 'RACE' || $comType == 'Team-RACE')
    {
        $scarr = array();
        $scarr[] = array("<b>Type</b> ", "<i>$comType ($comFormula)</i>");
        $scarr[] = array("<b>Scoring</b> ","<i>$overstr</i>");
        $scarr[] = array("<b>Min Dist</b>", "<i>$forMinDistance kms</i>");
        $scarr[] = array("<b>Nom Dist</b>", "<i>$forNomDistance kms</i>");
        $scarr[] = array("<b>Nom Time</b>", "<i>$forNomTime mins</i>");
        $scarr[] = array("<b>Nom Goal</b>", "<i>$forNomGoal%</i>");
        echo ftable($detarr, 'border="0" cellpadding="0" width="185"', '', array('', 'align="right"'));
        echo "<h1>Scoring Parameters</h1>";
        echo ftable($scarr, 'border="0" cellpadding="0" width="185"', '', array('', 'align="right"'));
    }
    else
    {
        $detarr[] = array("<b>Type</b> ", "<i>$comType ($comFormula)</i>");
        $detarr[] = array("<b>Scoring</b> ","<i>$overstr</i>");
        echo ftable($detarr, 'border="0" cellpadding="0" width="185"', '', array('', 'align="right"'));
    }


    hcopencomps($link);
    //hcclosedcomps($link);
    echo "</div>";
    //if (sizeof($taskinfo) > 8)
    //{
    //    echo "<div id=\"image\" background=\"images/pilots.jpg\"></div>";
    //}
    //else
    {
        hcimage($link,$comPk);
    }
    hcfooter();
}
?>
</body>
</html>

