<?php
require 'authorisation.php';
require 'xcdb.php';

function match_file($year, $base)
{
    # get the latest matching submission (or all?)
    $matches = glob($base . '*');
    #print "match_file: $year $base"; #var_dump($matches); echo "<br>";
    if (sizeof($matches) > 0)
    {
        return $matches[sizeof($matches)-1];
    }
    else
    {
       return 0;
    }
}

$tasPk=reqival('tasPk');
$comPk=reqival('comPk');

$usePk = check_auth('system');

$link = db_connect();
$isadmin = is_admin('admin', $usePk, $comPk);
$info = get_comtask($link, $tasPk);

$sql = "select T.traPk, T.traDate, P.pilLastName, P.pilHGFA from tblComTaskTrack C, tblTrack T, tblPilot P where C.tasPk=$tasPk and C.comPk=$comPk and C.traPk=T.traPk and P.pilPk=T.pilPk";
$result = mysql_query($sql, $link) or die("Can't get tracks associated with task");
$tracks = [];

while($row = mysql_fetch_array($result))
{
    $tracks[] = $row;
}


$ziplist = [];
$year = substr($info['tasDate'], 0, 4);
chdir("../tracks/$year");

foreach ($tracks as $row)
{
    # Find the original tracks ..
    $basename =  strtolower($row['pilLastName']) . '_' . $row['pilHGFA'] . '_' . $row['traDate'];
    $result = match_file($year, $basename);
    if ($result)
    {
        $ziplist[] = $result;
    }
}

#print "Download tracks disabled at this time<br>\r\n";
#exit(0);

# zip them up ..
$allfiles = implode(' ', $ziplist);

$bname = strtolower(preg_replace('/[\s+\/]/', '_', $info['comName'] . '_' . $info['tasName'] . ".zip"));
$filename = '/tmp/' . $bname;
#echo ("zip \"$filename\" $allfiles 2>&1 > /dev/null");
system("zip \"$filename\" $allfiles 2>&1 > /dev/null");

header("Content-Type: application/zip");
header("Content-Disposition: attachment; filename=\"$bname\"");
header("Content-Length: " . filesize($filename));
readfile($filename);
#unlink($filename);
exit;

?>


