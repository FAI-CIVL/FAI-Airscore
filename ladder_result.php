<?php
require_once 'authorisation.php';
require_once 'format.php';
require_once 'dbextra.php';
require_once 'template.php';



// function taskcmp($a, $b)
// {
//     if (!is_array($a)) return 0;
//     if (!is_array($b)) return 0;
// 
//     if ($a['tname'] == $b['tname']) 
//     {
//         return 0;
//     }
//     return ($a['tname'] < $b['tname']) ? -1 : 1;
// }

function add_result(&$results, $row, $topnat, $how)
{
    $score = round($row['tarScore']);
    //$validity = $row['tasQuality'] * 1000;
    $validity = $row['maxScore'];
    $pilPk = $row['pilPk'];
    // $row['tasName'];
    $tasName = substr($row['comName'], 0, 5) . ' ' . substr($row['comDateTo'],0,4);
    $fullName = substr($row['comCode'], 0, 8) . '&nbsp;' . substr($row['tasName'],0,1) . substr($row['tasName'], -1, 1);

    if (!array_key_exists($pilPk,$results) || !$results[$pilPk])
    {
        $results[$pilPk] = [];
        $results[$pilPk]['name'] = $row['pilFirstName'] . ' ' . $row['pilLastName'];
        $results[$pilPk]['hgfa'] = $row['pilFAI'];
        $results[$pilPk]['glider'] = $row['pilGliderBrand'] . ' ' . $row['pilGlider'];
        $results[$pilPk]['sponsor'] = $row['pilSponsor'];
        //$results[$pilPk]['civl'] = $civlnum;
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

    if ($perf >= 1)
    {
        $results[$pilPk]["${perf}${fullName}"] = array('score' => $score, 'validity' => $validity, 'tname' => $fullName, 'taspk' => $row['tasPk'], 'extpk' => 0 + $row['extPk']);
    }

    return "${perf}${fullName}";
}

function ladder_result($link, $ladPk, $ladder, $season, $restrict)
{
    $start = date(($season-1).'-11-01');
    $end = date(($season).'-10-31');
    $nat = $ladder['ladNationCode'];
    $how = $ladder['ladOverallScore'];
    $ladParam = $ladder['ladOverallParam'];

    # This query selects the Max score for a national pilot. I don't think we need this, FTV uses winner score anyway
//     $topnat = [];
//     $sql = "select T.tasPk, max(T.tarScore) as topNat 
//             from tblTaskResult T, tblTrack TL, tblPilot P
//             where T.traPk=TL.traPk and TL.pilPk=P.pilPk and P.pilNationCode='$nat'
//             group by tasPk";
//     $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Top National Query: ' . mysqli_connect_error());
//     while ($row = mysqli_fetch_assoc($result))
//     {
//         $topnat[$row['tasPk']] = $row['topNat'];
//     }

    # Select from the main database of results
//     $sql = "select 0 as extPk, TR.tarScore,
//         TP.pilPk, TP.pilLastName, TP.pilFirstName, TP.pilNationCode, TP.pilFAI, TP.pilSex,
//         TK.tasPk, TK.tasName, TK.tasDate, TK.tasQuality, 
//         C.comName, C.comDateTo, LC.lcValue, 
//         case when date_sub('$end', INTERVAL 365 DAY) > C.comDateTo 
//         then (TR.tarScore * LC.lcValue * 0.90 * TK.tasQuality) 
//         else (TR.tarScore * LC.lcValue * TK.tasQuality) end as ladScore, 
//         (TR.tarScore * LC.lcValue * (case when date_sub('$end', INTERVAL 365 DAY) > C.comDateTo 
//             then 0.90 else 1.0 end) / (TK.tasQuality * LC.lcValue)) as validity
// from    tblLadderComp LC 
//         join tblLadder L on L.ladPk=LC.ladPk
//         join tblCompetition C on LC.comPk=C.comPk
//         join tblTask TK on C.comPk=TK.comPk
//         join tblTaskResult TR on TR.tasPk=TK.tasPk
//         join tblTrack TT on TT.traPk=TR.traPk
//         join tblPilot TP on TP.pilPk=TT.pilPk
// WHERE LC.ladPk=$ladPk and TK.tasDate > '$start' and TK.tasDate < '$end'
//     and TP.pilNationCode=L.ladNationCode $restrict
//     order by TP.pilPk, C.comPk, (TR.tarScore * LC.lcValue * TK.tasQuality) desc";

	$sql = "SELECT 
				0 AS extPk, 
				TR.tarScore, 
				P.*, 
				T.tasPk, T.tasName, T.tasQuality, 
				(
					SELECT 
						MAX(tblTaskResult.tarScore) 
					FROM 
						tblTaskResult 
					WHERE 
						tblTaskResult.tasPk = T.tasPk 
				) AS maxScore,
				C.comName, C.comDateTo, C.comCode  
			FROM 
				tblLadderComp LC 
				JOIN tblLadder L USING (ladPk) 
				JOIN tblCompetition C ON LC.comPk = C.comPk AND (C.comDateFrom BETWEEN '$start' AND '$end') 
				JOIN tblTask T ON T.comPk = LC.comPk 
				JOIN tblTaskResult TR USING (tasPk) 
				JOIN tblTrack TT USING (traPk) 
				JOIN tblPilot P ON P.pilPk = TT.pilPk AND P.pilNat = L.ladNationCode 
			WHERE 
				LC.ladPk = $ladPk 
				$restrict 
			ORDER BY 
				P.pilPk, 
				C.comPk, 
				T.tasPk,
				TR.tarScore DESC";
    //echo "$sql \n";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Ladder tasks query failed: ' . mysqli_connect_error());
    $results = [];
    while ($row = mysqli_fetch_assoc($result))
    {
        add_result($results, $row, $row['maxScore'], $how);
    }

    // Work out how much validity we want (not really generic)
    $sql = "SELECT 
				SUM(tasQuality)* 1000 AS totQuality, 
				SUM(maxScore) AS totMaxScore 
			FROM 
				tblLadderComp LC 
				JOIN tblLadder L USING (ladPk) 
				JOIN tblCompetition C USING (comPk) 
				JOIN tblTask T USING (comPk) 
				JOIN (
					SELECT 
						tasPk, 
						MAX(tarScore) AS maxScore 
					FROM 
						tblTaskResult 
					GROUP BY 
						tasPk
				) TR using (tasPk) 
			WHERE 
				LC.ladPk = $ladPk 
				AND C.comDateFrom BETWEEN '$start' 
				AND '$end'";

    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Total quality query failed: ' . mysqli_connect_error());
    //$param = mysqli_result($result,0,0) * $ladParam / 100 ;
    
    # I will use Sum of Max Score as FTV param (PWC Style)
    $param = mysqli_result($result,0,1) * $ladParam;
    

    # Add external task results (to 1/3 of validity)
    if ($ladder['ladIncExternal'] > 0)
    {
        $sql = "select TK.extPk, TK.extURL as tasPk,
        TP.pilPk, TP.pilLastName, TP.pilFirstName, TP.pilNationCode, TP.pilFAI, TP.pilSex,
        TK.tasName, TK.tasQuality, TK.comName, TK.comDateTo, TK.lcValue, TK.tasTopScore,
        case when date_sub('$end', INTERVAL 365 DAY) > TK.comDateTo 
        then (ER.etrScore * TK.lcValue * 0.90 * TK.tasQuality) 
        else (ER.etrScore * TK.lcValue * TK.tasQuality) end as ladScore, 
        (ER.etrScore * TK.lcValue * (case when date_sub('$end', INTERVAL 365 DAY) > TK.comDateTo 
            then 0.90 else 1.0 end) / (TK.tasQuality * TK.lcValue)) as validity
        from tblExtTask TK
        join tblExtResult ER on ER.extPk=TK.extPk
        join tblPilot TP on TP.pilPk=ER.pilPk
WHERE TK.comDateTo > '$start' and TK.comDateTo < '$end'
        $restrict
        order by TP.pilPk, TK.extPk, (ER.etrScore * TK.lcValue * TK.tasQuality) desc";
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' ext tasks query failed: ' . mysqli_connect_error());
        while ($row = mysqli_fetch_assoc($result))
        {
            $res = add_result($results, $row, $row['tasTopScore'], $how);
        }

        return filter_results($ladPk, $how, $param, $param * 0.33, $results);
    }

    return filter_results($ladPk, $how, $param, 0, $results);
}

function filter_results($ladPk, $how, $param, $extpar, $results)
{
    # Do the scoring totals (FTV/X or Y tasks etc)
    //echo "<hr />how=$how, param=$param <br />\n";
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
            $pilext = 0;
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
                    // if external
                    if (0+$taskresult['extpk'] > 0) 
                    {
                        if ($pilext < $extpar)
                        {
                            $gap = $extpar - $pilext;
                            if ($gap > $param - $pilvalid)
                            {
                              $gap = $param - $pilvalid;
                            }
                            $perc = 0;
                            if ($taskresult['validity'] > 0)
                            {
                                $perc = $gap / $taskresult['validity'];
                            }
                            if ($perc > 1)
                            {
                                $perc = 1;
                            }
                            $pilext = $pilext + $taskresult['validity'] * $perc;
                            $pilvalid = $pilvalid + $taskresult['validity'] * $perc;
                            $pilscore = $pilscore + $taskresult['score'] * $perc;
                            $arr[$perf]['perc'] = $perc * 100;
                        }
                        else
                        {
                            // ignore
                        }
                    }
                    else
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
        }

        // resort arr by task?
        //uasort($arr, "taskcmp");
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
    //var_dump($sorted);
    return $sorted;
}

function output_ladder($link, $ladPk, $ladder, $fdhv, $class, $season)
{
    $today = getdate();
    $tdate = sprintf("%04d-%02d-%02d", $today['year'], $today['mon'], $today['mday']);
	    
    $rtable = [];
    $rdec = [];
    
    //if ($comClass == "HG")
    //{
    //    $classopts = array ( 'open' => '', 'floater' => '&class=0', 'kingpost' => '&class=1', 
    //        'hg-open' => '&class=2', 'rigid' => '&class=3', 'women' => '&class=4' );
    //}
    //else
//     {
//         $classopts = array ( 'open' => '', 'fun' => '&class=0', 'sports' => '&class=1', 
//             'serial' => '&class=2', 'women' => '&class=4' );
//     }
//     $cind = '';
//     if ($class != '')
//     {
//         $cind = "&class=$class";
//     }
//     $copts = [];
//     foreach ($classopts as $text => $url)
//     {
//         $copts[$text] = "ladder.php?ladPk=$ladPk$url";
//     }
    
    $claPk = $ladder['claPk'];
    $rdec[] = 'class="h"';
    $rdec[] = 'class="h"';
    $hdr = array( fb('Class. '), classselector($link, $claPk, $class), '', '', '');
    $hdr2 = array( fb('Pos.'), fb('Name'), fb('Glider'), fb('Sponsor'), fb('Total') );
    
    # find each task details
    $alltasks = [];
    $taskinfo = [];
    $sorted = [];
    
    $sorted = ladder_result($link, $ladPk, $ladder, $season, $fdhv);
    $subtask = '';
    
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
            $nxt[] = str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($arr['name']))));
        }
        else
        {
            $nxt[] = '';
            $nxt[] = str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($arr['name']))));
        }
    
        $nxt[] = ( (stripos($arr['glider'], '') !== false) ? '' : str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower(substr($arr['glider'], 0, 32))))) );
        $nxt[] = substr($arr['sponsor'], 0, 48);
        $nxt[] = fb($tot);
        $lasttot = $tot;
    
        //if (ctype_digit(substr($key,0,1)))
        foreach ($arr as $key => $sarr)
        { 
            $score = 0;
            $perc = 0;
            if (is_array($sarr) && array_key_exists('score', $sarr))
            {
                $score = $sarr['score'];
                $tname = $sarr['tname'];
                $tpk = $sarr['taspk'];
                if (array_key_exists('perc', $sarr))
                {
                    $perc = round($sarr['perc'], 0);
                }
                if (!$score)
                {
                    $score = 0;
                    
                }
                if ($perc == 100)
                {
                    if ($tpk > 0)
                    {
                        $nxt[] = "$score <a href=\"task_result.php?tasPk=$tpk\">[$tname]</a>";
                    }
                    else
                    {
                        $nxt[] = "$score <a href=\"$tpk\">[$tname]</a>";
                    }
                }
                else if ($perc > 0)
                {
                    if ($tpk > 0)
                    {
                        $nxt[] = "$score ($perc%) <a href=\"task_result.php?tasPk=$tpk\">[$tname]</a>";
                    }
                    else
                    {
                        $nxt[] = "$score ($perc%) <a href=\"$tpk\">[$tname]</a>";
                    }
                }
                else
                {
                    if ($tpk > 0)
                    {
                        $nxt[] = "<del>$score</del> <a href=\"task_result.php?tasPk=$tpk\">[$tname]</a>";
                    }
                    else
                    {
                        $nxt[] = "<del>$score</del> <a href=\"$tpk\">[$tname]</a>";
                    }
                }
            }
        }
        $rtable[] = $nxt;
        $count++;
    }
    echo ftable($rtable, "class='format format2 ladderresult'", $rdec, '');
    
	// FTV INFO
	if ($comOverall == 'ftv')
	{
		echo "1. Click <a href=\"ftv.php?comPk=$comPk\">here</a> for an explanation of FTV<br>";
		//echo "2. Scores in bold 100%, or indicated %, other scores not counted<br>";
	}

}

// function output_ladder_list($ladder, $fdhv, $class)
// {
//     $rtable = [];
//     $rdec = [];
// 
//     $hdr = array( fb('Name'),  fb('Nation'), fb('Start'), fb('End'), fb('Method') );
//     $rtable[] = $hdr;
//     $rdec[] = 'class="h"';
//     $max = sizeof($ladder);
// 
//     foreach ($ladder as $row)
//     {
//         $ladPk = $row['ladPk'];
//         $rtable[] = array( "<a href=\"ladder.php?ladPk=$ladPk\">" . $row['ladName'] . "</a>", $row['ladNationCode'], $row['ladStart'], $row['ladEnd'], $row['ladHow']);
//         if ($count % 2)
//         {
//             $rdec[] = 'class="d"';
//         }
//         else
//         {
//             $rdec[] = 'class="l"';
//         }
//         $count++;
//     }
// 
//     echo ftable($rtable, "border=\"0\" cellpadding=\"3\" alternate-colours=\"yes\" align=\"center\"", $rdec, '');
// }


// Main Code Begins HERE //

# Initializing variables to avoid esceptions
# Probably to remove when debugged and fully checked

$overstr = '';

$ladPk = reqival('ladPk');

if (reqexists('class'))
{
	$cval = reqival('class');
}

$file = __FILE__;
$link = db_connect();
$title = 'AirScore'; # default

$usePk = check_auth('system');
$isadmin = is_admin('admin',$usePk,-1);

# Get Season
$season = isset($_REQUEST['season']) ? $_REQUEST['season'] : getseason();


// if (reqexists('addladder'))
// {
//     check_admin('admin',$usePk,-1);
//     $lname = reqsval('lname');
//     $nation = reqsval('nation');
//     $start = reqsval('sdate');
//     $end = reqsval('edate');
//     $method = reqsval('method');
//     $param = reqival('param');
// 
//     $query = "insert into tblLadder (ladName, ladNationCode, ladStart, ladEnd, ladHow, ladParam) value ('$lname','$nation', '$start', '$end', '$method', $param)";
//     $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Ladder insert failed: ' . mysqli_connect_error());
// }
// 
// if (reqexists('addladcomp'))
// {
//     check_admin('admin',$usePk,-1);
//     $sanction = reqival('sanction');
//     $comPk = reqival('comp');
// 
//     if ($comPk == 0 || $ladPk == 0)
//     {
//         echo "Failed: unknown comPk=$comPk ladPk=$ladPk<br>";
//     }
//     else
//     {
//         $query = "insert into tblLadderComp (lcValue, ladPk, comPk) value ($sanction, $ladPk, $comPk)";
//         $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' LadderComp insert failed: ' . mysqli_connect_error());
//     }
// }

// $fdhv= '';
// $classstr = '';
// if (reqexists('class'))
// {
//     $cval = reqival('class');
//     if ($comClass == "HG")
//     {
//         $carr = array ( "'floater'", "'kingpost'", "'open'", "'rigid'"       );
//         $cstr = array ( "Floater", "Kingpost", "Open", "Rigid", "Women", "Seniors", "Juniors" );
//     }
//     else
//     {
//         $carr = array ( "'1/2'", "'2'", "'2/3'", "'competition'"       );
//         $cstr = array ( "Fun", "Sport", "Serial", "Open", "Women", "Seniors", "Juniors" );
//     }
//     $classstr = "<b>" . $cstr[reqival('class')] . "</b> - ";
//     if ($cval == 4)
//     {
//         $fdhv = "and TP.pilSex='F'";
//     }
//     else
//     {
//         $fdhv = $carr[reqival('class')];
//         $fdhv = "and TT.traDHV<=$fdhv ";
//     }
// }

# Check if we have a classification request
$sel = get_ladder_class_info($link, $ladPk, $cval, $season);
$class = $sel['name'];
$fdhv = $sel['fdhv'];
//echo "claPk: $cval, class: $class, restrict = $fdhv <br /> \n";
$all_ladders = [];

$query = "	SELECT 
				L.*, 
				LS.* 
			FROM 
				tblLadder L 
				JOIN tblLadderSeason LS USING (ladPk)
			WHERE 
				ladPk = $ladPk 
				AND LS.seasonYear = $season";
$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Ladder info query failed: ' . mysqli_connect_error());
$row = mysqli_fetch_assoc($result);
if ($row)
{
	$ladName = $row['ladName'];
	$title = "$ladName $season";
	$ladder = $row;
}
// hcheader($title, 2, "$classstr " . $ladder['ladStart'] . " - " . $ladder['ladEnd']);
// echo "<div id=\"content\">";
// //echo "<div id=\"text\" style=\"overflow: auto; max-width: 600px;\">";
// echo "<div id=\"text\" style=\"overflow: auto;\">";

//initializing template header
tpinit($link,$file,$row);

if ($ladPk > 0)
{
    output_ladder($link, $ladPk, $ladder, $fdhv, $cval, $season);

//     if ($isadmin)
//     {
//         echo "<br><br>";
//         echo "<form action=\"ladder.php?ladPk=$ladPk\" name=\"ladadmin\" method=\"post\">";
//         $query = "select C.comPk, C.comName from tblCompetition C, tblLadder L where L.ladPk=$ladPk and C.comDateFrom between L.ladStart and L.ladEnd";
//         $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Ladder query failed: ' . mysqli_connect_error());
//         $comparr = [];
//         while ($row = mysqli_fetch_assoc($result))
//         {
//             $comparr[$row['comName']] = $row['comPk'];
//         }
// 
//         $out = ftable(
//             array(
//                 array('Comp:', fselect('comp', '', $comparr), 'Value:', fin('sanction',0, 6), fis('addladcomp', 'Associate Comp', ''))
//             ), '', '', ''
//         );
//     
//         echo $out;
//         echo "</form>";
//     }
}


tpfooter($file);


?>
