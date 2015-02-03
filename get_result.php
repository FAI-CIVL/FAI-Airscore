<?php
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Content-type: application/json');

require 'authorisation.php';

function comp_result($comPk, $how, $param, $cls)
{
    $sql = "select TK.*,TR.*,P.*,T.traGlider from tblTaskResult TR, tblTask TK, tblTrack T, tblPilot P, tblCompetition C where C.comPk=$comPk and TK.comPk=C.comPk and TK.tasPk=TR.tasPk and TR.traPk=T.traPk and T.traPk=TR.traPk and P.pilPk=T.pilPk $cls order by P.pilPk, TK.tasPk";
    $result = mysql_query($sql) or die('Task result query failed: ' . mysql_error());
    $results = array();
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
            $results[$pilPk] = array();
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

$link = db_connect();
$comPk = reqival('comPk');
$comOverall = reqsval('overall');
$comOverallParam = reqival('param');
$class = reqival('class');
$carr = array();

$fdhv= '';
if ($class > 0)
{
    if ($comClass == "HG")
    {
        $carr = array ( "'floater'", "'kingpost'", "'open'", "'rigid'"       );
    }
    else
    {
        $carr = array ( "'1/2'", "'2'", "'2/3'", "'competition'"       );
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
        $fdhv = $carr[$class];
        $fdhv = "and T.traDHV<=$fdhv ";
    }
}

$sorted = comp_result($comPk, $comOverall, $comOverallParam, $fdhv);
print json_encode($sorted);
?>
