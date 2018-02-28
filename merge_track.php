<?php
require 'authorisation.php';
require 'xcdb.php';

header('Cache-Control: no-cache, must-revalidate');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Content-type: application/json');

$link = db_connect();
$comPk = intval($_REQUEST['comPk']);
$tasPk = intval($_REQUEST['tasPk']);
$traPk = intval($_REQUEST['traPk']);
$incPk = intval($_REQUEST['incPk']);

if ($comPk == 0)
{
    $sql = "select comPk from tblTask where tasPk=$tasPk";
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' can' . mysqli_connect_error());
    $comPk = mysqli_result($result,0,0);
}

// authorise ...
$usePk = check_auth('system');
$link = db_connect();
$isadmin = is_admin('admin',$usePk,$comPk);
if (!$isadmin)
{
    return 0;
}

#$sql = "insert into tblTrackLog ( trlLatDecimal, trlLongDecimal, trlAltitude, trlTime )
#select $traPk, trlLatDecimal, trlLongDecimal, trlAltitude, trlTime* from tblTrackLog where traPk in $incPk";

$sql = "update tblTrackLog set traPk=$traPk where traPk=$incPk";
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' cannot merge track' . mysqli_connect_error());

$sql = "delete from tblTrack where traPk=$incPk";
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' cannot delete merged track' . mysqli_connect_error());

// Re-verify
$out = '';
$retv = 0;
exec(BINDIR . "track_verify_sr.pl $traPk $tasPk", $out, $retv);

mysqli_close($link);

//print json_encode($retarr);
?>
