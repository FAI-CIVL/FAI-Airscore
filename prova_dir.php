<?php
header('Content-type: text/plain');

require 'authorisation.php';
require 'xcdb.php';

function match_file($dir, $year, $base)	
{
    chdir($dir);
    # get the latest matching submission (or all?)
    $file = $dir . '/' . $base . '*';
    foreach ( glob($base."*") as $filename ) 
    {
    	echo "$filename size " . filesize($filename) . "\n";
	}
}

$tasPk=reqival('tasPk');
$comPk=reqival('comPk');
#$usePk = check_auth('system');
$link = db_connect();
#$isadmin = is_admin('admin', $usePk, $comPk);
$info = get_comtask($link, $tasPk);
$sql = "select T.traPk, T.traDate, P.pilLastName, P.pilFAI from tblComTaskTrack C, tblTrack T, tblPilot P where C.tasPk=$tasPk and C.comPk=$comPk and C.traPk=T.traPk and P.pilPk=T.pilPk";
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Cannot get tracks associated with task: ' . mysqli_connect_error());




#Get tracks
$tracks = [];
while($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
	$tracks[] = $row;
}

$year = substr($info['tasDate'], 0, 4);
$dir = __DIR__ . "/../tracks/$year";
echo "directory: " . $dir . "\n";
chdir($dir);

foreach ($tracks as $row)
{
    # Find the original tracks ..
    $basename =  strtolower($row['pilLastName']) . '_' . $row['pilFAI'] . '_' . $row['traDate'];
    echo "basename: " . $basename . "\n";
    foreach ( glob($basename."*") as $filename ) 
    {
    	echo "$filename size " . filesize($filename) . "\n";
	}
}    


?>