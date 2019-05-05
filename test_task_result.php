<?php
require './lib/format.php';

$json=file_get_contents("/web/dev/airscore/json/LEGA19_1_T1_20190505_135036.json");
$array =  json_decode($json, true);

print_r($array);
$info = $array['info'][0];
$jsondata = $array['data'][0];
$formula = $array['formula'][0];
$stats = $array['stats'][0];
$task = $array['task'];
$results = $array['results'];

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
$html .= "<table style='width:100%;border:0'>".PHP_EOL;
$html .= "<tr>".PHP_EOL;
$html .= "<td style='text-align:center'>".$info['comp_name']."</td>".PHP_EOL;
$html .= "</tr><tr>".PHP_EOL;
$html .= "<td style='text-align:center'>".$info['task_name']."</td>".PHP_EOL;
$html .= "</tr><tr>".PHP_EOL;
$html .= "<td style='color:red'>".$jsondata['status']."</td>".PHP_EOL;
$html .= "</tr><tr>".PHP_EOL;
$html .= "<td>Date: ".$info['task_date']."</td>".PHP_EOL;
$html .= "</tr>".PHP_EOL;
$html .= "</table>".PHP_EOL;

$html .= "<hr>";

## Task Table ##
$html .= "<table style='width:50%;border:0'>".PHP_EOL;
$html .= "<tr>".PHP_EOL;
$html .= "<td>ID</td><td>type</td><td></td><td>radius</td><td></td><td>dist.</td>".PHP_EOL;
$html .= "</tr><tr>".PHP_EOL;
foreach ($task as $wpt) {
    $html .= "      <td>".$wpt['ID']."</td>".PHP_EOL;
    $type = '';
    switch($wpt['type']) {
        case 'launch':
            $type = 'Take-off';
            break;
        case 'speed':
            $type = 'Start';
            break;
        case 'endspeed':
            $type = 'ESS';
            break;
        case 'goal':
            $type = 'Goal';
            break;
    }
    $html .= "      <td>".$type."</td>".PHP_EOL;
    $html .= "      <td>".(($wpt['type']=='launch' or  $wpt['how']=='entry') ? '' : $wpt['how'])."</td>".PHP_EOL;
    $html .= "      <td>".($wpt['type']=='launch' ? '' : ($wpt['radius'].' m.'))."</td>".PHP_EOL;
    $html .= "      <td>".($wpt['shape']=='circle' ? '' : $wpt['shape'])."</td>".PHP_EOL;
    $html .= "      <td>".(($wpt['type']=='launch' or  $wpt['type']=='goal') ? '' : round($wpt['cumulative_dist']/1000, 2).' Km'). "</td>".PHP_EOL;
    $html .= "</tr><tr>".PHP_EOL;
}
$html .= "<td colspan='6'>Opt. Distance: ".round($info['task_opt_dist']/1000, 2)." Km</td>".PHP_EOL;
$html .= "</tr><tr>".PHP_EOL;
$html .= "<td colspan='2'>Start Gate: ".$info['SS_time']."</td>".PHP_EOL;
if ( $info['SS_interval'] > 0 ) {
    $html .= "<td colspan='2'>Interval: ".$info['SS_interval']." min.</td>".PHP_EOL;
}
$html .= "<td colspan='2'>Start Closing Time: ".$info['SS_close_time']."</td>".PHP_EOL;
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
if (isset($stats['task_stopped_time']))
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
if ($tasArrival == 'on')
{
    $header[] = "Arr P";
}
// $header[] = fb("Spd");
$header[] = "Dst P";
$header[] = "Score";
$trtab[] = $header;
$html .= ftable($trtab, "class='format taskresult'", '' , '');
$count = 1;
    // Cycle through the array
    // foreach ($data->stand as $idx => $stand) {
    //
    //     // Output a row
    //     $html .= "<tr>";
    //     $html .= "<td>$stand->afko</td>";
    //     $html .= "<td>$stand->positie</td>";
    //     $html .= "</tr>";
    // }
    //
    // // Close the table
    // $html .= "</table>";

echo $html;
