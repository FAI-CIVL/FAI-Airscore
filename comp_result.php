<?php

function overall_handicap($comPk, $how, $param, $cls)
//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//
{
    $sql = "select T.tasPk, max(TR.tarScore) as maxScore from tblTask T, tblTaskResult TR where T.tasPk=TR.tasPk and T.comPk=$comPk group by T.tasPk";
//    $result = mysql_query($sql) or die('Handicap maxscore failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Handicap maxscore failed: ' . mysqli_connect_error());
    $maxarr = [];
//    while ($row = mysql_fetch_array($result))
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $maxarr[$row['tasPk']] = $row['maxScore'];
    }

    $sql = "select P.*,TK.*, TR.*, H.* from tblTaskResult TR, tblTask TK, tblTrack K, tblPilot P, tblHandicap H, tblCompetition C where H.comPk=C.comPk and C.comPk=TK.comPk and K.traPk=TR.traPk and K.pilPk=P.pilPk and H.pilPk=P.pilPk and H.comPk=TK.comPk and TK.comPk=$comPk and TR.tasPk=TK.tasPk order by P.pilPk, TK.tasPk";
    #$sql = "select TK.*,TR.*,P.* from tblTaskResult TR, tblTask TK, tblTrack T, tblPilot P, tblCompetition C where C.comPk=$comPk and TK.comPk=C.comPk and TK.tasPk=TR.tasPk and TR.traPk=T.traPk and T.traPk=TR.traPk and P.pilPk=T.pilPk $cls order by P.pilPk, TK.tasPk";

//    $result = mysql_query($sql) or die('Task result query failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task result query failed: ' . mysqli_connect_error());
    $results = [];
//    while ($row = mysql_fetch_array($result))
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
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
            $results[$pilPk] = [];
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

function comp_result($comPk, $how, $param, $cls, $tasktot)
{
    $sql = "select TK.*,TR.*,P.*,T.traGlider from tblTaskResult TR, tblTask TK, tblTrack T, tblPilot P, tblCompetition C where C.comPk=$comPk and TK.comPk=C.comPk and TK.tasPk=TR.tasPk and TR.traPk=T.traPk and T.traPk=TR.traPk and P.pilPk=T.pilPk $cls order by P.pilPk, TK.tasPk";
    $result = mysql_query($sql) or die('Task result query failed: ' . mysql_error());
    $results = [];
    while ($row = mysql_fetch_array($result, MYSQL_ASSOC))
    {
        $score = round($row['tarScore']);
        $validity = $row['tasQuality'] * 1000;
        $pilPk = $row['pilPk'];
        $tasName = $row['tasName'];
        $nation = $row['pilNationCode'];
        $pilnum = $row['pilHGFA'];
        $civlnum = $row['pilCIVL'];
        $glider = $row['traGlider'];
        $gender = $row['pilSex'];
    
        if (!array_key_exists($pilPk,$results) || !$results[$pilPk])
        {
            $results[$pilPk] = [];
            $results[$pilPk]['name'] = $row['pilFirstName'] . ' ' . $row['pilLastName'];
            $results[$pilPk]['hgfa'] = $pilnum;
            $results[$pilPk]['civl'] = $civlnum;
            $results[$pilPk]['nation'] = $nation;
            $results[$pilPk]['glider'] = $glider;
            $results[$pilPk]['gender'] = $gender;
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

    if ($how == 'ftv' && $tasktot < 2)
    {
        $param = 1000;
    }

    return filter_results($comPk, $how, $param, $results);
}

function filter_results($comPk, $how, $param, $results)
{
    // Do the scoring totals (FTV/X or Y tasks etc)
    $sorted = [];
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
require_once 'olc.php';
require_once 'team.php';
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
//$result = mysql_query($query) or die('Comp query failed: ' . mysql_error());
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Comp query failed: ' . mysqli_connect_error());
//$row = mysql_fetch_array($result, MYSQL_ASSOC);
$row = mysqli_fetch_assoc($result);
if ($row)
{
    $comName = isset($row['comName']) ? $row['comName'] : '';
    $title = isset($row['comName']) ? $row['comName'] : '';
    $comDateFrom = substr(isset($row['comDateFrom']) ? $row['comDateFrom'] : '',0,10);
    $comDateTo = substr(isset($row['comDateTo']) ? $row['comDateTo'] : '',0,10);
    #$comPk = $row['comPk'];
    $comOverall = isset($row['comOverallScore']) ? $row['comOverallScore'] : '';
    $comOverallParam = isset($row['comOverallParam']) ? $row['comOverallParam'] : ''; # Discard Parameter, Ex. 75 = 75% eq normal FTV 0.25
    $comDirector = isset($row['comMeetDirName']) ? $row['comMeetDirName'] : '';
    $comLocation = isset($row['comLocation']) ? $row['comLocation'] : '';
    $comFormula = ( isset($row['forClass']) ? $row['forClass'] : '' ) . ' ' . ( isset($row['forVersion']) ? $row['forVersion'] : '' );
    $forOLCPoints = isset($row['forOLCPoints']) ? $row['forOLCPoints'] : '';
    $comSanction = isset($row['comSanction']) ? $row['comSanction'] : '';
    $comOverall = isset($row['comOverallScore']) ? $row['comOverallScore'] : '';  # Type of scoring discards: FTV, ...
    $comTeamScoring = isset($row['comTeamScoring']) ? $row['comTeamScoring'] : '';
    $comCode = isset($row['comCode']) ? $row['comCode'] : '';
    $comClass = isset($row['comClass']) ? $row['comClass'] : '';
    $comType = isset($row['comType']) ? $row['comType'] : '';
    $forNomGoal = isset($row['forNomGoal']) ? $row['forNomGoal'] : '';
    $forMinDistance = isset($row['forMinDistance']) ? $row['forMinDistance'] : '';
    $forNomDistance = isset($row['forNomDistance']) ? $row['forNomDistance'] : '';
    $forNomTime = isset($row['forNomTime']) ? $row['forNomTime'] : '';
    $forDiscreteClasses = isset($row['forDiscreteClasses']) ? $row['forDiscreteClasses'] : '';
}


$fdhv= ''; #parameter to insert in mysql query in result calculations
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
    else if ($cval == 9)
    {
        $fdhv = '';
    }
    else
    {
        $fdhv = $carr[reqival('class')];
        $fdhv = "and T.traDHV<=$fdhv ";
        if ($forDiscreteClasses == 1)
        {
            $fdhv = "and T.traDHV=$fdhv ";
        }
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
//$result = mysql_query($query);
$result = mysqli_query($link, $query); // or die('Task total failed: ' . mysql_error());
if ($result)
{
//    $tasTotal = mysql_result($result, 0, 0);
    $tasTotal = mysqli_result($result, 0, 0);
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
// Fix: make this configurable
if (0 && $tdate == $comDateTo)
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

$rtable = [];
$rdec = [];

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
$copts = [];
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
    $hdr = array( fb('Res'),  fselect('class', "comp_result.php?comPk=$comPk$cind", $copts, ' onchange="document.location.href=this.value"'), fb('Nation'), fb('Sex'), fb('FAI'), fb('CIVL'), fb('Total') );
    $hdr2 = array( '', '', '', '', '', '', '' );
}
else
{
    $hdr = array( fb('Res'),  fselect('class', "comp_result.php?comPk=$comPk$cind", $copts, ' onchange="document.location.href=this.value"'), fb('Glider'), fb('Total') );
    $hdr2 = array( '', '', '', '' );
}

# find each task details
$alltasks = [];
$taskinfo = [];
$sorted = [];
if ($class == "8")
{
    if ($comTeamScoring == 'handicap')
    {
        team_handicap_result($comPk,$how,$param);
    }
}
else if ($comType == 'RACE' || $comType == 'Team-RACE' || $comType == 'Route' || $comType == 'RACE-handicap')
{
    $query = "select T.* from tblTask T where T.comPk=$comPk order by T.tasDate";
//    $result = mysql_query($query) or die('Task query failed: ' . mysql_error());
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task query failed: ' . mysqli_connect_error());
//    while ($row = mysql_fetch_array($result, MYSQL_ASSOC))
    while ($row = mysqli_fetch_assoc($result))
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
        $sorted = comp_result($comPk, $comOverall, $comOverallParam, $fdhv, $tasTotal);
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
        if ($row['tasTaskType'] == 'airgain')
        {
            $treg = $row['regPk'];
            $hdr2[] = "<a href=\"waypoint_map.php?regPk=$treg\">Map</a>";
        }
        else
        {
            $hdr2[] = "<a href=\"route_map.php?comPk=$comPk&tasPk=$tasPk\">Map</a>";
        }
    }
    $rtable[] = $hdr;
    $rtable[] = $hdr2;

    $lasttot = 0;
    $count = 1;
    foreach ($sorted as $pil => $arr)
    {
        $nxt = [];
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
            $nxt[] = $arr['gender'];
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
    echo ftable($rtable, "border=\"0\" cellpadding=\"2\" cellspacing=\"0\" alternate-colours=\"yes\" align=\"center\"", $rdec, '');
}
else
{
    // OLC Result
    $rtable[] = array( fb('Res'),  fselect('class', "comp_result.php?comPk=$comPk$cind", $copts, ' onchange="document.location.href=this.value"'), fb('Total') );
    $rtable[] = array( '', '', '' );
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
    if ($class == "9")
    {
        $sorted = olc_handicap_result($link, $comOverallParam, $restrict);
    }
    else
    {
        $sorted = olc_result($link, $comOverallParam, $restrict);
    }
    $size = sizeof($sorted);

    $count = $start+1;
    $sorted = array_slice($sorted,$start,$top+2);
    $count = display_olc_result($comPk,$rtable,$sorted,$top,$count);

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

    if ($comType == 'RACE' || $comType == 'Team-RACE' || $comType == 'RACE-handicap')
    {
        $scarr = [];
        $scarr[] = array("<b>Type</b> ", "<i>$comType ($comFormula)</i>");
        $scarr[] = array("<b>Scoring</b> ","<i>$overstr</i>");
        $scarr[] = array("<b>Min&nbsp;Dist</b>", "<i>$forMinDistance kms</i>");
        $scarr[] = array("<b>Nom&nbsp;Dist</b>", "<i>$forNomDistance kms</i>");
        $scarr[] = array("<b>Nom&nbsp;Time</b>", "<i>$forNomTime mins</i>");
        $scarr[] = array("<b>Nom&nbsp;Goal</b>", "<i>$forNomGoal%</i>");
        echo ftable($detarr, 'border="0" cellpadding="0" width="200"', '', array('', 'align="right"'));
        echo "<h1>Scoring Parameters</h1>";
        echo ftable($scarr, 'border="0" cellpadding="0" width="200"', '', array('', 'align="right"'));
    }
    else
    {
        if ($comType == 'OLC')
        {
            $detarr[] = array("<b>Type</b> ", "<i>$comType ($forOLCPoints)</i>");
        }
        else
        {
            $detarr[] = array("<b>Type</b> ", "<i>$comType ($comFormula)</i>");
        }
        $detarr[] = array("<b>Scoring</b> ","<i>$overstr</i>");
        echo ftable($detarr, 'border="0" cellpadding="0" width="200"', '', array('', 'align="right"'));
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

