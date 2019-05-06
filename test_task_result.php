<?php
require './lib/format.php';

function sec_to_time($s, $off = 0) {
  $t = round($s) + $off*3600;
  return sprintf('%02d:%02d:%02d', (($t)/3600),(($t)/60%60), ($t)%60);
}

$comPk = intval($_REQUEST['comPk']);
$tasPk = intval($_REQUEST['tasPk']);

$json=file_get_contents("/web/dev/airscore/json/LEGA19_1_T1_20190506_123332.json");
$array =  json_decode($json, true);
$rnd = 1;

print_r($array);
$info       = $array['info'][0];
$jsondata   = $array['data'][0];
$formula    = $array['formula'][0];
$stats      = $array['stats'][0];
$task       = $array['task'];
$results    = $array['results'];

$date = date_format(date_create_from_format('Y-m-d', $info['task_date']), 'D d M Y');
$offset     = $info['time_offset'];
$ssDist     = $info['SS_distance'];
$start      = $info['SS_time'];
$deadline   = $info['task_deadline'];
$stopped_time = $stats['task_stopped_time'];
$altitude_bonus = $formula['height_bonus'];

#order wpt array
foreach ($task as $wpt) {
    $order[] = $wpt['number'];
}
array_multisort($order,SORT_NUMERIC,$task);

#order results array
foreach ($results as $key => $row) {
    $order[$key] = $row['score'];
}
array_multisort($order,SORT_NUMERIC, SORT_DESC,$results);

$html = '';

## Title Table ##
$html .= "<table class='result_header_table'>".PHP_EOL;
$html .= "<tr>".PHP_EOL;
$html .= "<td class='result_comp_name'>".$info['comp_name']."</td>".PHP_EOL;
$html .= "</tr><tr>".PHP_EOL;
$html .= "<td class='result_task_name'>".$info['task_name'].", ".$date."</td>".PHP_EOL;
$html .= "</tr><tr>".PHP_EOL;
$html .= "<td class='result_status'>".$jsondata['status']."</td>".PHP_EOL;
$html .= "</tr>".PHP_EOL;
$html .= "</table>".PHP_EOL;

$html .= "<hr>";

## Task Table ##
$html .= "<table class='result_task_table'>".PHP_EOL;
$html .= "<tr>".PHP_EOL;
$html .= "<td>ID</td><td>type</td><td>radius</td><td>dist.</td>".PHP_EOL;
$html .= "</tr><tr>".PHP_EOL;
foreach ($task as $wpt) {
    $html .= "      <td>".$wpt['ID']."</td>".PHP_EOL;
    $type = '';
    switch($wpt['type']) {
        case 'launch':
            $type = 'TakeOff';
            break;
        case 'speed':
            $type = ($wpt['how']=='entry' ? 'SS' : 'SS (exit)');
            break;
        case 'endspeed':
            $type = ($wpt['how']=='entry' ? 'ESS' : 'ESS (exit)');
            break;
        case 'goal':
            $type = ($wpt['shape']=='circle' ? 'Goal' : 'Goal Line');
            break;
        default:
            ($wpt['how']=='entry' ? '' : '(exit)');
    }
    $html .= "      <td>".$type;
    $html .= "      <td>".($wpt['type']=='launch' ? '' : ($wpt['radius'].' m.'))."</td>".PHP_EOL;
    $html .= "      <td>".($wpt['type']=='launch' ? '' : round($wpt['cumulative_dist']/1000, 2).' Km'). "</td>".PHP_EOL;
    $html .= "</tr><tr>".PHP_EOL;
}

$html .= "<td colspan='4'>Start Gate Time: ".$start;
$html .= ($info['SS_close_time']>0 ? (" to ".$info['SS_close_time']) : '')."</td>".PHP_EOL;

if ( $info['SS_interval'] > 0 ) {
    $html .= "</tr><tr>".PHP_EOL;
    $html .= "<td colspan='4'>Interval: ".$info['SS_interval']." min.</td>".PHP_EOL;
}
if ( isset($stopped_time) ) {
    $html .= "</tr><tr>".PHP_EOL;
    $html .= "<td colspan='3' style='color:red;'>Task Stopped at: ".$stopped_time." </td>".PHP_EOL;
}
elseif ( $deadline > 0 ) {
    $html .= "</tr><tr>".PHP_EOL;
    $html .= "<td colspan='3'>Task Deadline: ".$deadline." </td>".PHP_EOL;
}

$html .= "</tr>".PHP_EOL;
$html .= "</table>".PHP_EOL;

$html .= "<hr>";

## Results Table ##

# create dep. points header
if ($formula['departure'] == 'leadout')
{
    $depcol = 'LO P';
}
elseif ($formula['departure'] == 'kmbonus')
{
    $depcol = 'Lkm';
}
elseif ($formula['departure'] == 'on')
{
    $depcol = 'Dep P';
}
else
{
    $depcol = 'off';
}

$trtab = [];

$header = array("Rank", "Name", "Nat", "Glider");
$header[] = "Sponsor";
$header[] = "Start";
$header[] = "Finish";
$header[] = "Time";
$header[] = "Speed";
if (isset($stopped_time))
{
    $goalalt = $stats['goal_altitude'];
    $header[] = "Height";
}
if ($tasHeightBonus == 'on')
{
    $header[] = "HBs";
}
$header[] = "Distance";

$header[] = "Spd P";
if ($depcol != 'off')
{
    $header[] = $depcol;
}
if ($formula['arrival'] == 'on')
{
    $header[] = "Arr P";
}
// $header[] = fb("Spd");
$header[] = "Dst P";
$header[] = "Score";
$trtab[] = $header;
$count = 1;

foreach ($results as $row)
{
    $track_id = $row['track_id'];
    $name = str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['name']))));
    $nation = $row['nat'];
    $glider = ( (stripos($row['glider'], 'Unknown') !== false) ? '' : htmlspecialchars(str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower(substr($row['glider'], 0, 25)))))) );
    $sponsor = isset($row['sponsor']) ? htmlspecialchars(str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower(substr($row['sponsor'], 0, 40)))))) : '';
    $class = $row['class'];
    $resulttype = strtoupper($row['type']);

    # Check if pilot did fly
    if ( $resulttype == 'ABS' || $resulttype == 'DNF' )
    {
    	$trrow = array($place, $name, $nation);
		$trrow[] = $glider;
		$trrow[] = $sponsor;
		array_push($trrow, '', '', '', '');
		$trrow[] = '';
		array_push($trrow, '', '', '', $resulttype);
    }
    else
    {
		$dist = round($row['dist_points'], $rnd);
		$dep = round($row['dep_points'], $rnd);
		$arr = round($row['arr_points'], $rnd);
		$spd = round($row['speed_points'], $rnd);
		$score = round($row['score'], $rnd);
		$lastalt = round($row['altitude']);
		$resulttype = $row['type'];
		$comment = $row['comment'];
		$start = $row['SS_time'];
		$end = $row['ES_time'];
		$goal = $row['goal_time'];
		$endf = "";
		$startf = "";
		$timeinair = "";
        $startf = sec_to_time($start, $offset);
		if ($end)
		{
            $timeinair = sec_to_time($end - $start);
            $endf = sec_to_time($end, $offset);
			$speed = round($ssDist * 3.6 / ($end - $start), 2);
		}
		else
		{
			$timeinair = "";
			$speed = "";
		}
		$time = ($end - $start) / 60;
		$tardist = round($row['distance']/1000,2);
		$penalty = round($row['penalty']);
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
		    $trrow = array(fb($place), "<a href=\"tracklog_map.php?trackid=$track_id&tasPk=$tasPk&comPk=$comPk\">$name</a>", $nation );
		}
		else
		{
		    $trrow = array(fb($place), $name, $nation );
		}

		$trrow[] = $glider;
		$trrow[] = $sponsor;

		$trrow[] = $startf;
        #strikesout if pilot did not make goal
		$trrow[] = ( $goal != 0 ? $endf : "<del>".$endf."</del>" );
		$trrow[] = ( $goal != 0 ? $timeinair : "<del>".$timeinair."</del>" );
		$trrow[] = ( $speed != 0 ? number_format((float)$speed,2) : "" );
		if ( isset($stopped_time) )
		{
			$alt = ( $lastalt - $goalalt >= 0 ? "+".($lastalt - $goalalt) : "");
			#strikesout if pilot made ESS
			$trrow[] = ( !$end ? $alt : "<del>".$alt."</del>" );
		}
		if ($altitude_bonus == 'on')
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
		$trrow[] = number_format((float)$tardist,2);
		if ( $totalPenalty != 0 )
		{
			$trrow[] = $penalty;
		}

		$trrow[] = number_format($spd,1);
		if ($depcol != 'off')
		{
			$trrow[] = number_format($dep,1);
		}
		if ($formula['arrival'] == 'on')
		{
			$trrow[] = $arr;
		}
	//     $trrow[] = number_format($spd,1);
		$trrow[] = number_format($dist,1);
		$trrow[] = round($score);
    }

    $trtab[] = $trrow;

    $count++;
}

$html .= ftable($trtab, "class='format taskresult'", '' , '');

echo $html;
