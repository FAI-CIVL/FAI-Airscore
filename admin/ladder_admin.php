<?php
require 'admin_startup.php';

function hcincludedcomps($link,$ladPk)
{
    echo "<h1><span>Included Competitions</span></h1>";
    if ($ladPk > 0)
    {
        $sql = "select C.* from tblLadderComp LC, tblCompetition C where LC.comPk=C.comPk and ladPk=$ladPk order by LC.lcValue desc, comDateTo";
    }
    else
    {
        $sql = "select distinct C.* from tblLadderComp LC, tblCompetition C where LC.comPk=C.comPk and LC.lcValue > 0 order by comDateTo desc";
    }
    $result = mysqli_query($link, $sql);
    $comps = [];
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        // FIX: if not finished & no tracks then submit_track page ..
        // FIX: if finished no tracks don't list!
        $cpk = $row['comPk'];
        $comps[] = "<a href=\"comp_result.php?comPk=$cpk\">" . $row['comName'] . "</a>";
    }
    echo fnl($comps);
}
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
    $score = round($row['ladScore'] / $topnat);
    $validity = $row['tasQuality'] * 1000;
    $pilPk = $row['pilPk'];
    // $row['tasName'];
    $tasName = substr($row['comName'], 0, 5) . ' ' . substr($row['comDateTo'],0,4);
    $fullName = substr($row['comName'], 0, 3) . substr($row['comDateTo'],2,2) . '&nbsp;' . substr($row['tasName'],0,1) . substr($row['tasName'], -1, 1);

    if (!array_key_exists($pilPk,$results) || !$results[$pilPk])
    {
        $results[$pilPk] = [];
        $results[$pilPk]['name'] = $row['pilFirstName'] . ' ' . $row['pilLastName'];
        $results[$pilPk]['hgfa'] = $row['pilFAI'];
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

function ladder_result($ladPk, $ladder, $restrict)
{
    $start = $ladder['ladStart'];
    $end = $ladder['ladEnd'];
    $how = $ladder['ladHow'];
    $nat = $ladder['ladNationCode'];
    $ladParam = $ladder['ladParam'];

    $topnat = [];
    $sql = "select T.tasPk, max(T.tarScore) as topNat 
            from tblTaskResult T, tblTrack TL, tblPilot P
            where T.traPk=TL.traPk and TL.pilPk=P.pilPk and P.pilNationCode='$nat'
            group by tasPk";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Top National Query: ' . mysqli_connect_error());
    while ($row = mysqli_fetch_assoc($result))
    {
        $topnat[$row['tasPk']] = $row['topNat'];
    }

    // Select from the main database of results
    $sql = "select 0 as extPk, TR.tarScore,
        TP.pilPk, TP.pilLastName, TP.pilFirstName, TP.pilNationCode, TP.pilFAI, TP.pilSex,
        TK.tasPk, TK.tasName, TK.tasDate, TK.tasQuality, 
        C.comName, C.comDateTo, LC.lcValue, 
        case when date_sub('$end', INTERVAL 365 DAY) > C.comDateTo 
        then (TR.tarScore * LC.lcValue * 0.90 * TK.tasQuality) 
        else (TR.tarScore * LC.lcValue * TK.tasQuality) end as ladScore, 
        (TR.tarScore * LC.lcValue * (case when date_sub('$end', INTERVAL 365 DAY) > C.comDateTo 
            then 0.90 else 1.0 end) / (TK.tasQuality * LC.lcValue)) as validity
from    tblLadderComp LC 
        join tblLadder L on L.ladPk=LC.ladPk
        join tblCompetition C on LC.comPk=C.comPk
        join tblTask TK on C.comPk=TK.comPk
        join tblTaskResult TR on TR.tasPk=TK.tasPk
        join tblTrack TT on TT.traPk=TR.traPk
        join tblPilot TP on TP.pilPk=TT.pilPk
WHERE LC.ladPk=$ladPk and TK.tasDate > '$start' and TK.tasDate < '$end'
    and TP.pilNationCode=L.ladNationCode $restrict
    order by TP.pilPk, C.comPk, (TR.tarScore * LC.lcValue * TK.tasQuality) desc";

    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Ladder query failed: ' . mysqli_connect_error());
    $results = [];
    while ($row = mysqli_fetch_assoc($result))
    {
        add_result($results, $row, $topnat[$row['tasPk']], $how);
    }

    // Work out how much validity we want (not really generic)
    $sql = "select sum(tasQuality)*1000 from tblLadderComp LC 
        join tblLadder L on L.ladPk=LC.ladPk and LC.lcValue=450
        join tblCompetition C on LC.comPk=C.comPk
        join tblTask TK on C.comPk=TK.comPk
        WHERE LC.ladPk=$ladPk and TK.tasDate > '$start' and TK.tasDate < '$end'";

    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Total quality query failed: ' . mysqli_connect_error());
    $param = mysqli_result($result,0,0) * $ladParam / 100 ;

    // Add external task results (to 1/3 of validity)
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
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Ladder query failed: ' . mysqli_connect_error());
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

function output_ladder($ladPk, $ladder, $fdhv, $class)
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
    {
        $classopts = array ( 'open' => '', 'fun' => '&class=0', 'sports' => '&class=1', 
            'serial' => '&class=2', 'women' => '&class=4' );
    }
    $cind = '';
    if ($class != '')
    {
        $cind = "&class=$class";
    }
    $copts = [];
    foreach ($classopts as $text => $url)
    {
        $copts[$text] = "ladder_admin.php?ladPk=$ladPk$url";
    }
    
    $rdec[] = 'class="h"';
    $rdec[] = 'class="h"';
    $hdr = array( fb('Res'),  fselect('class', "ladder_admin.php?ladPk=$ladPk$cind", $copts, ' onchange="document.location.href=this.value"'), fb('HGFA'), fb('Total') );
    $hdr2 = array( '', '', '', '' );
    
    # find each task details
    $alltasks = [];
    $taskinfo = [];
    $sorted = [];
    
    $sorted = ladder_result($ladPk, $ladder, $fdhv);
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
            $nxt[] = $arr['name'];
        }
        else
        {
            $nxt[] = '';
            $nxt[] = $arr['name'];
        }
    
        $nxt[] = $arr['hgfa'];
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
                        $nxt[] = "<a href=\"task_result.php?tasPk=$tpk\">$tname $score</a>";
                    }
                    else
                    {
                        $nxt[] = "<a href=\"$tpk\">$tname $score</a>";
                    }
                }
                else if ($perc > 0)
                {
                    if ($tpk > 0)
                    {
                        $nxt[] = "<a href=\"task_result.php?tasPk=$tpk\">$tname $score $perc%</a>";
                    }
                    else
                    {
                        $nxt[] = "<a href=\"$tpk\">$tname $score $perc%</a>";
                    }
                }
                else
                {
                    //$nxt[] = "<del>$tname $score</del>";
                }
            }
        }
        $rtable[] = $nxt;
        $count++;
    }
    echo ftable($rtable, "border=\"0\" cellpadding=\"3\" alternate-colours=\"yes\" align=\"center\"", $rdec, '');
    
    //echo "</table>";
    if ($ladder['ladHow'] == 'ftv')
    {
        echo "1. Click <a href=\"ftv.php\">here</a> for an explanation of FTV<br>";
        echo "2. Highlighted scores 100%, or indicated %, other scores not included<br>";
    }
}

function output_ladder_list($link, $ladder, $season)
{
    $rtable = [];
//     $rdec = [];

    $hdr = array( fb('Name'), fb('Category'), fb('Nation'), fb("Season $season"), fb('Method'), fb('Classes Definition'),'');
    $rtable[] = $hdr;
//     $rdec[] = 'class="h"';
//     $max = sizeof($ladder);

    foreach ($ladder as $row)
    {
        $ladPk = $row['id'];
        $name = $row['ladName'];
        $active = $row['ladActive'] ? "<span style='color: green'>Active</span>" : "<span style='color: red'>Disable</span>";
        $class = $row['ladComClass'];
        $countrycode = get_countrycode($link, $row['ladNationCode']);
        if ( isset($row['seasonYear']) )
        {
			$claname = $row['claName'];
			$how = ($row['ladOverallScore'] == 'ftv') ? ( strtoupper($row['ladOverallScore']) . ' (' . (100 - $row['ladOverallParam'] * 100) . '%)' ) : $row['ladOverallScore'];
		}
		else
		{
			$claname = "<span style='color:red'>Not set for $season</span>";
			$how = "<span style='color:red'>Not set for $season</span>";
		}
        $rtable[] = array( "<a href=\"ladder_admin.php?ladPk=$ladPk&season=$season\">" . $name . "</a>", $class, $countrycode, $active, $how, $claname, "<a href=\"ladder_admin.php?ladPk=$ladPk&season=$season\">edit</a>");
    }

    return $rtable;
}

//
// Main Body Here
//

$link = db_connect();
$usePk = auth('system');
$comPk = reqival('comPk');
$file = __FILE__;
$message = '';
$content = '';
$isadmin = is_admin('admin',$usePk,-1);

$ladPk = reqival('ladPk');
$comclass = reqsval('category') !== '' ? reqsval('category') : 'PG';

# Get Season
$season = isset($_REQUEST['season']) ? $_REQUEST['season'] : getseason();



$ladder_list = [];
$new_ladder = [];
$sel_ladder = [];

# deletion message
if ( reqexists('del') )
	$message .= "Ladder ($ladPk) succesfully deleted.\n";

# Create new ladder
if (reqexists('addladder'))
{
    check_admin('admin',$usePk,-1);
    $lname = reqsval('lname');
    $nation = reqsval('nation');
    $comclass = reqsval('category');
    $method = reqsval('method');
    $param = 1 - reqival('param')/100;
	$claPk = reqsval('classdef');
    $query = "INSERT INTO tblLadder (ladName, ladComClass, ladNationCode) VALUE ('$lname', '$comclass', '$nation')";
    mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Ladder insert failed: ' . mysqli_connect_error() . ' - ' . $query);
    $ladPk = mysqli_insert_id($link);
    
    $query = "INSERT INTO tblLadderSeason (ladPk, seasonYear, ladOverallScore, ladOverallParam, claPk) VALUE ('$ladPk', '$season', '$method', '$param', '$claPk')";
    mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' LadderSeason insert failed: ' . mysqli_connect_error() . ' - ' . $query);
}
# Delete ladder if not used in any season
elseif (reqexists('delladder'))
{
    check_admin('admin',$usePk,-1);
    
    # Check ladder is not used before deleting
	$ladPk = reqival('ladPk');
	$query = "	SELECT 
					* 
				FROM 
					tblLadderComp
				WHERE 
					ladPk = $ladPk 
				LIMIT 1 ";
	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Ladder delete check failed: ' . mysqli_connect_error());
	if (mysqli_num_rows($result) > 0)
    {
        $message .= "Unable to delete ladder ($ladPk) as it is in use in a season.\n";
    }
	else
	{
		$query = "DELETE FROM tblLadder WHERE ladPk=$ladPk";
		mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Ladder delete failed: ' . mysqli_connect_error());
		$query = "DELETE FROM tblLadderSeason WHERE ladPk=$ladPk";
		mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' LadderSeason delete failed: ' . mysqli_connect_error());
		
		redirect("ladder_admin.php?ladPk=$ladPk&del=1");
	} 
}
# Update Ladder
elseif (reqexists('upladder'))
{    
    check_admin('admin',$usePk,-1);
    
//     # Check ladder is not used before changing it
//     $ladPk = reqival('ladPk');
// 	$query = "	SELECT 
// 					* 
// 				FROM 
// 					tblLadderComp  
// 				WHERE 
// 					ladPk = $ladPk 
// 				LIMIT 1 ";
// 	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Ladder update check failed: ' . mysqli_connect_error());
// 	if (mysqli_num_rows($result) > 0)
//     {
//         $message .= "Unable to change ladder ($ladPk) as it is in use in a competition.\n";
//     }
// 	else
// 	{
// 		$name = reqsval('lname');
// 		$nation = reqsval('nation');
// 		$comclass = reqsval('category');
// 		$method = reqsval('method');
// 		$param = 1 - reqival('param')/100;
// 		$claPk = reqsval('classdef');
// 		$query = "UPDATE tblLadder SET ladname='$name', ladComClass='$comclass', ladNationCode='$nation', ladHow='$method', ladOverallParam='$param', claPk='$claPk' WHERE ladPk=$ladPk";
// 		mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Ladder update failed: ' . mysqli_connect_error());
// 		
// 		$message .= "Ladder ($ladPk) succesfully updated.\n";
// 	}

		$ladPk = reqival('ladPk');
		$name = reqsval('lname');
		$nation = reqsval('nation');
		$comclass = reqsval('category');
		$active = isset($_POST["active"]) ? 1 : 0;
		$method = reqsval('method');
		$param = 1 - reqival('param')/100;
		$claPk = reqsval('classdef');
		
		$query = "UPDATE tblLadder SET ladname='$name', ladComClass='$comclass', ladNationCode='$nation' WHERE ladPk=$ladPk";
		mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Ladder update failed: ' . mysqli_connect_error());
		
		$query = "SELECT ladPk FROM tblLadderSeason WHERE ladPk = $ladPk AND seasonYear = $season LIMIT 1";
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' LadderSeason exists check failed: ' . mysqli_connect_error());
		if (mysqli_num_rows($result) > 0)
		{
			$query = "UPDATE tblLadderSeason SET ladOverallScore='$method', ladActive=$active, ladOverallParam='$param', claPk='$claPk' WHERE ladPk=$ladPk AND seasonYear = $season";
			echo $query;
		}
		else
		{
			$query = "INSERT INTO tblLadderSeason (ladPk, seasonYear, ladActive, ladOverallScore, ladOverallParam, claPk) VALUE ('$ladPk', '$season', '$active', '$method', '$param', '$claPk')";
		}		
		mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Ladder update failed: ' . mysqli_connect_error());

		$message .= "Ladder ($ladPk) succesfully updated.\n";
}

if (reqexists('addladcomp'))
{
    check_admin('admin',$usePk,-1);
    $sanction = reqival('sanction');
    $comPk = reqival('comp');

    if ($comPk == 0 || $ladPk == 0)
    {
        echo "Failed: unknown comPk=$comPk ladPk=$ladPk<br>";
    }
    else
    {
        $query = "INSERT INTO tblLadderComp (lcValue, ladPk, comPk) VALUE ($sanction, $ladPk, $comPk)";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' LadderComp insert failed: ' . mysqli_connect_error());
    }
}

if ($ladPk < 1)
{
    # Display all available ladders
    $title = 'Ladders Administration';
    $all_ladders = [];
    $query = "	SELECT 
					L.ladPk AS id, 
					L.*, 
					LS.*, 
					C.claName 
				FROM 
					tblLadder L 
					LEFT OUTER JOIN tblLadderSeason LS ON L.ladPk = LS.ladPk AND LS.seasonYear = $season 
					LEFT OUTER JOIN tblClassification C USING (claPk)  
				ORDER BY 
					ladComClass ASC, 
					ladName ";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Ladder query failed: ' . mysqli_connect_error());
    while ($row = mysqli_fetch_assoc($result))
    {
        $all_ladders[] = $row;
    }
    $ladder_list = output_ladder_list($link, $all_ladders, $season);
    if ( $isadmin )
    {
        # Add new ladder (for today season) table
        $thisseason = getseason();
        $new_ladder[] = array('Category: ', fselect('category', $comclass, array('PG', 'HG', 'mixed'), " onchange=\"document.getElementById('ladadmin').submit();\""), 'Name: ', fin('lname','', 20), 'Nation: ', get_countrylist($link, 'nation', 380));
        $new_ladder[] = array('Scoring: ', fselect('method', '', array('all', 'ftv', 'round' )), 'Score param %: ', fin('param',0, 10), 'Classes Definition: ', get_classifications($link, 'classdef', $comclass));
        $new_ladder[] = array(fis('addladder', 'Add Ladder', ''), "<input type='hidden' name='season' value='$thisseason'>", '', '', '', '' );
	}   

}
else
{
    # Update / Delete Ladder Mode
    $query = "	SELECT 
					L.*,
					LS.*, 
					C.claName 
				FROM 
					tblLadder L 
					LEFT OUTER JOIN tblLadderSeason LS ON L.ladPk = LS.ladPk AND LS.seasonYear = $season 
					LEFT OUTER JOIN tblClassification C USING (claPk) 
				WHERE 
					L.ladPk = $ladPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Ladder query failed: ' . mysqli_connect_error());
    $row = mysqli_fetch_assoc($result);
    if ($row)
    {
        $name = $row['ladName'];
        $comclass = $row['ladComClass'];
        $nat = $row['ladNationCode'];
        $active = $row['ladActive'];
        $method = $row['ladOverallScore'];
        $param = 100 - $row['ladOverallParam'] * 100;
        $claPk = $row['claPk'];
        $sel_ladder[] = array('Category: ', fselect('category-disabled', $comclass, array('PG', 'HG', 'mixed'), ' disabled'), 'Name: ', fin('lname',$name, 20), 'Nation: ', get_countrylist($link, 'nation', $nat));
        $sel_ladder[] = array('Scoring: ', fselect('method', $method, array('all', 'ftv', 'round', 'round-perc' )), 'Score param %: ', fin('param',$param, 10), 'Classes Definition: ', get_classifications($link, 'classdef', $comclass, $claPk));
        $sel_ladder[] = array("Active in $season: ", fic("active", '', $active), fis('upladder', 'Update', ''), fis('delladder', 'DELETE', ''), "<a href=\"ladder_admin.php\">cancel</a>", "<input type='hidden' name='season' value='$season'>"."<input type='hidden' name='category' value='$comclass'>");
        $title = $name . " ($season)";
	}
}


//initializing template header
tpadmin($link,$file);

echo "<h3>$title</h3>\n";
echo "<br /><hr />\n";
if ( $message !== '')
{
	echo "<h4> <span style='color:red'>$message</span> </h4>\n";
	echo "<br /><hr />\n";
}

echo "<form enctype='multipart/form-data' action=\"ladder_admin.php\" name='main' id='main' method='post'>\n";
echo "Season: " . fselect('season', $season, season_array($link), " onchange=\"document.getElementById('main').submit();\"");
echo "</form>\n";
echo "<hr />\n";

if ( $content !== '')
{
	echo $content;
	echo "<br /><hr />\n";
}

if ( !empty($sel_ladder) )
{
    # Update / Delete ladder Mode
	echo "<form  enctype='multipart/form-data' action=\"ladder_admin.php?ladPk=$ladPk\" name='ladadmin' id='ladadmin' method='post'>\n";
	echo "<p class='explanation'>Method and Classes Definition for $season</p>\n";
	echo ftable($sel_ladder, "class='format selladder'", '', '');
	echo "</form>\n"; 
}
if ( !empty($ladder_list) || !empty($new_ladder) )
{
    # Ladder List Mode
    echo "<p class='explanation'>Parameters for Season $season</p>\n";
    echo "<form enctype='multipart/form-data' action=\"ladder_admin.php\" name='ladadmin' id='ladadmin' method='post'>\n";
	echo ftable($ladder_list, "class='format ladderlist'", '', '');
	echo "<br /><hr />\n";
	echo "<h4>Create new Ladder</h4>\n";
	echo "<p class='explanation'>Method and Classes Definition for $thisseason</p>\n";
	echo ftable($new_ladder, "class='format newladder'", '', '');
	echo "</form>\n";
    
}

tpfooter($file);

?>