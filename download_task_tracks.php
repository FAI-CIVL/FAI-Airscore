<?php
require 'authorisation.php';
require 'xcdb.php';

function match_file($dir, $year, $base)	
{
    chdir($dir);
    # get the latest matching submission (or all?)
  //  $file = $dir . '/' . $base . '*';
    $matches = glob($base . '*');
  //  echo 'file: ' . $file . "\n";
 //   echo "matches: " . var_dump($matches) . "\n";
    #print "match_file: $year $base"; #var_dump($matches); echo "<br>";
    if (sizeof($matches) > 0)
    {
        return $matches[sizeof($matches)-1];
        //echo "size > 0 \n";
    }
    else
    {
       return 0;
       //echo "size = 0 \n";
    }
}

function send_zip_file( $file )
{
    if ( !is_file( $file ) )
    {
        header($_SERVER['SERVER_PROTOCOL'].' 404 Not Found');
        //require_once("404.php");
        exit;
    }
    elseif ( !is_readable( $file ) )
    {
        header($_SERVER['SERVER_PROTOCOL'].' 403 Forbidden');
        //require_once("403.php");
        exit;
    }
    else
    {
		header($_SERVER['SERVER_PROTOCOL'].' 200 OK');
        header("Pragma: public");
        header("Expires: 0");
        header("Accept-Ranges: bytes");
        header("Connection: keep-alive");
        header("Cache-Control: must-revalidate, post-check=0, pre-check=0");
        header("Cache-Control: public");
        header("Content-type: application/zip");
        header("Content-Description: File Transfer");
        header("Content-Disposition: attachment; filename=\"".basename($file)."\"");
		header('Content-Length: '.filesize($file));
        header("Content-Transfer-Encoding: binary");
		ob_clean(); //Fix to solve "corrupted compressed file" error!
        readfile($file);
    }
}

$tasPk=reqival('tasPk');
$comPk=reqival('comPk');
#$usePk = check_auth('system');
$link = db_connect();
#$isadmin = is_admin('admin', $usePk, $comPk);
$info = get_comtask($link, $tasPk);
$sql = "select T.traPk, T.traDate, P.pilLastName, P.pilHGFA from tblComTaskTrack C, tblTrack T, tblPilot P where C.tasPk=$tasPk and C.comPk=$comPk and C.traPk=T.traPk and P.pilPk=T.pilPk";
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Cannot get tracks associated with task: ' . mysqli_connect_error());

#Create Archive
$zip = new ZipArchive();
$bname = strtolower(preg_replace('/[\s+\/]/', '_', $info['comName'] . '_' . $info['tasName'] . ".zip"));
$filename = '/tmp/' . $bname;
//echo $filename . "\n";
if ( true !== ( $zip->open($filename, ZipArchive::CREATE | ZipArchive::OVERWRITE)) )
{
    exit("cannot open <$filename>\n");
}
//echo "File $filename created \n";

#Get tracks
$tracks = [];
while($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
	$tracks[] = $row;
}

$year = substr($info['tasDate'], 0, 4);
$dir = __DIR__ . "/../tracks/$year";
//echo "directory: " . $dir . "\n";
chdir($dir);

foreach ($tracks as $row)
{
    # Find the original tracks ..
    $basename =  strtolower($row['pilLastName']) . '_' . $row['pilHGFA'] . '_' . $row['traDate'];
    //echo "basename: " . $basename . "\n";
    $result = match_file($dir, $year, $basename);
    //echo "result: " . $result . "\n";
    if ($result)
    {
        $zip->addFile($result);
        $zip->renameName($result,$result.'.igc');
        //echo "file: " . $result . "\n";
    }
}
$zip->close();

send_zip_file($filename);

exit;
?>