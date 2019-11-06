<?php
require 'startup.php';

function sec_to_time($s, $off = 0) {
  $t = round($s) + $off;
  return sprintf('%02d:%02d:%02d', (($t)/3600),(($t)/60%60), ($t)%60);
}

function get_json($link, $tasPk, $refPk=NULL) {
    #check if we request a specific json, or the visible one
    if ($refPk != NULL) {
        $query = "  SELECT `refJSON`
                    FROM `tblResultFile`
                    WHERE `refPk` = $refPk
                    LIMIT 1";
    }
    else {
        $query = "  SELECT `refJSON`
                    FROM `tblResultFile`
                    WHERE `comPk` = $comPk
                    AND `refVisible` = 1
                    LIMIT 1";
    }
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Cannot get JSON file: ' . mysqli_connect_error());
    $file = mysqli_result($result,0,0);
    return $file;
}

// Main Code Begins HERE //

$comPk = intval($_REQUEST['comPk']);
$refPk = intval($_REQUEST['refPk']);
$link = db_connect();
$file = __FILE__;

$cval = (reqexists('class') ? reqsval('class') : '');

$html = '';

$file = get_json($link, $tasPk, $refPk);
//print "file: ".$file;

if ( isset($file) && !($file == NULL) ) {
    $json = file_get_contents($file);
    $array = json_decode($json, true);
    $rnd = 1;

    // print_r($array);
    $info       = $array['info'];
    $jsondata   = $array['data'];
    $formula    = $array['formula'];
    $rankings   = $array['rankings'];
    $stats      = $array['stats'];
    $tasks      = $array['tasks'];
    $results    = $array['results'];

    $date_from  = date_format(date_create_from_format('Y-m-d', $info['date_from']), 'D d M Y');
    $date_to    = date_format(date_create_from_format('Y-m-d', $info['date_to']), 'D d M Y');
    $offset     = $info['time_offset'];
    $created    = gmdate('D d M Y H:i:s', ($jsondata['timestamp'] + $offset));

    #order wpt array
    $order = [];
    foreach ($tasks as $key => $id) {
        $order[$key] = $id['id'];
    }
    array_multisort($order,SORT_NUMERIC,$tasks);

    #order results array
    $order = [];
    foreach ($results as $key => $row) {
        $order[$key] = $row['score'];
    }
    array_multisort($order,SORT_NUMERIC,SORT_DESC,$results);

    $html .= "<div class='result_header'>".PHP_EOL;
    ## Title Table ##
    $html .= "  <table class='result_header_table'>".PHP_EOL;
    $html .= "    <tr>".PHP_EOL;
    $html .= "    <td class='result_comp_name'>".$info['comp_name']."</td>".PHP_EOL;
    $html .= "    </tr><tr>".PHP_EOL;
    $html .= "    <td class='result_site_name'>".$info['comp_site']."</td>".PHP_EOL;
    $html .= "    </tr>".PHP_EOL;
    $html .= "  </table>".PHP_EOL;
    $html .= "</div>".PHP_EOL;

    $html .= "<div class='comp_header'>".PHP_EOL;
    ## Task Name and date Table ##
    $html .= "  <table class='comp_header_table'>".PHP_EOL;
    $html .= "    <td class='result_comp_date'> From: ".$date_from."  to: ".$date_to."</td>".PHP_EOL;
    $html .= "    </tr><tr>".PHP_EOL;
    if ( (stripos($jsondata['status'], 'provisional') !== false) || (stripos($jsondata['status'], 'test') !== false) ) {
        $html .= "    <td class='result_status' style='color:red; font-weight:600;'>".$jsondata['status']."</td>".PHP_EOL;
    }
    else {
        $html .= "    <td class='result_status'>".$jsondata['status']."</td>".PHP_EOL;
    }
    $html .= "    </tr>".PHP_EOL;
    $html .= "  </table>".PHP_EOL;
    $html .= "</div>".PHP_EOL;


    $html .= "<hr style ='float: none;'>";

    ## Task Definition Table ##
    $html .= "<table class='result_tasks_table'>".PHP_EOL;
    $html .= "<tr>".PHP_EOL;
    $html .= "<th>Task</th><th>Date</th><th>Distance</th>".PHP_EOL;
    $html .= "</tr><tr>".PHP_EOL;
    foreach ($tasks as $task) {
        $date = date_format(date_create_from_format('Y-m-d', $task['date']), 'D d M Y');

        $html .= "      <td>".$task['code']."</td>".PHP_EOL;
        $html .= "      <td>".$date."</td>".PHP_EOL;
        $html .= "      <td>".round($task['opt_dist']/1000, 2)." Km </td>".PHP_EOL;
        $html .= "</tr>".PHP_EOL;
    }

    $html .= "</table>".PHP_EOL;

    $html .= "<hr>";

    ## Rankings switch ##
    $html .= class_selector($link, $rankings, $cval);

    ## Results Table ##
    $trtab = [];

    $header = array("Rank", "Name", "Nat", "Glider", "Sponsor", "Score");
    foreach ($tasks as $task) {
        $header[] = $task['code'];
    }

    $trtab[] = $header;
    $count = 1;

    foreach ($results as $row)
    {
        #check if we have filtered ranking
        #team ranking to be implemented
        if ( ($cval == '') || ($cval=='Female' && $row['sex']=='F') || ($cval != null && is_array($rankings[$cval]) && array_search($row['class'],$rankings[$cval]) != NULL) ) {
            $pil_id = $row['pil_id'];
            $name   = $row['name'];
            $nation = $row['nat'];
            $glider = ( (stripos($row['glider'], 'Unknown') !== false) ? '' : htmlspecialchars(str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower(substr($row['glider'], 0, 25)))))) );
            $sponsor = isset($row['sponsor']) ? htmlspecialchars(str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower(substr($row['sponsor'], 0, 40)))))) : '';
            $class = $row['class'];

    		$score = round($row['score'], $rnd);
    		// $comment = $row['comment'];

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
    		    $trrow = array(fb($place), $name, $nation );
    		}
    		else
    		{
    		    $trrow = array(fb($place), $name, $nation );
    		}

    		$trrow[] = $glider;
    		$trrow[] = $sponsor;

    		$trrow[] = "<strong> $score </strong>";

            foreach ($tasks as $task) {
                $code   = $task['code'];
                $res    = $row['results'][$code]['score'];
                $pre    = $row['results'][$code]['pre'];
                if ($res == $pre) {
                    $trrow[] = $res;
                }
                else {
                    $trrow[] = "$res/<del>$pre</del>";
                }
            }

            $trtab[] = $trrow;

            $count++;
        }
    }

    $html .= ftable($trtab, "class='format taskresult'", '' , '');

    ## STATS TABLE ##

    #create task statistic table
    $sttbl = '';
    $sttbl .= "<table class='result_stats'>".PHP_EOL;
    $sttbl .= "<th colspan='2'>Event Statistics</th>".PHP_EOL;
    $sttbl .= "<tr><td class='result key'>Partecipants:</td><td class='result value'>".$stats['tot_pilots']."</td></tr>".PHP_EOL;
    $sttbl .= "<tr><td class='result key'>Valid tasks:</td><td class='result value'>".$stats['valid_tasks']."</td></tr>".PHP_EOL;
    $sttbl .= "<tr><td class='result key'>Total flights:</td><td class='result value'>".$stats['tot_flights']."</td></tr>".PHP_EOL;
    $sttbl .= "<tr><td class='result key'>Total Dist. Flown:</td><td class='result value'>".round($stats['tot_dist_flown']/1000, 2)." Km </td></tr>".PHP_EOL;
    $sttbl .= "<tr><td class='result key'>Winner score:</td><td class='result value'>".$stats['winner_score']."</td></tr>".PHP_EOL;
    $sttbl .= "</table>".PHP_EOL;

    #create task formula table
    $fortbl = '';
    $fortbl .= "<table class='result_stats'>".PHP_EOL;
    $fortbl .= "<th colspan='2'>Event Parameters</th>".PHP_EOL;
    $fortbl .= "<tr><td class='result key'>Formula:</td><td class='result value'>".$formula['formula']."</td></tr>".PHP_EOL;
    $fortbl .= "<tr><td class='result key'>Total Validity Method:</td><td class='result value'>";
    if ($formula['task_validity'] == 'ftv') {
        $fortbl .= strtoupper($formula['formula_class'])." FTV <i>(".(100 - $formula['validity_param']*100)."%)</i>";
    }
    elseif ($formula['task_validity'] == 'round') {
        $fortbl .= "DISCARDS <i>(1 dropped task every".$formula['validity_param']." valid tasks)</i>";
    }
    else {
        $fortbl .= "FULL";
    }
    $fortbl .= "</td></tr>".PHP_EOL;
    $fortbl .= "</table>".PHP_EOL;

    $html .= "<hr>".PHP_EOL;
    $html .= "<div class='comp_results stats_container'>".PHP_EOL;
    $html .= "  <div class='column'>".PHP_EOL;
    $html .= $sttbl;
    $html .= "  </div>".PHP_EOL;
    $html .= "  <div class='column'>".PHP_EOL;
    $html .= $fortbl;
    $html .= "  </div>".PHP_EOL;
    $html .= "</div>".PHP_EOL;

    $html .= "<hr>".PHP_EOL;
    $html .= "<p>created on ".$created."</p>";

}
else {
    $html .= "<p>Task has not been scored yet.<br /></p>";
}

//initializing template header
tpinit($link,$file,$info);

echo $html;
echo "<p><a href='comp_result.php?comPk=$comPk'>Back to competition Result</a></p>";

tpfooter($file);

?>
