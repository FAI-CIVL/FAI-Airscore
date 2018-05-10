<?php

require_once 'authorisation.php';
require_once 'format.php';
require_once 'dbextra.php';
require 'template.php';
require 'track_ops.php';




// Main Code Begins HERE //

$comPk = intval($_REQUEST['comPk']);
$tasPk = intval($_REQUEST['tasPk']);
$class = reqsval('class');

$file = __FILE__;
$link = db_connect();
$title = 'AirScore'; # default
$message = '';

# Get pilot ID or redirect to login
$pilPk = get_juser();

# We check if there is a uploaded track
if ( reqexists('addtrack') )
{
    //echo $_FILES['userfile']['tmp_name'];
    $fh = fopen("/tmp/submit24", "w");
    foreach ($_REQUEST as $k=>$v)
    {
        fwrite($fh, "key=$k, value$v\n");
    }
    fclose($fh);

    //echo "<title>Track Accepted</title>\n";
    $traPk = accept_track($link, $pilPk, $comPk, $tasPk);
    //redirect("tracklog_map.php?trackid=$traPk&comPk=$comPk&ok=1");
    //exit(0);
    $message .= "Track accepted.";
    
    # Write task result
    $table = [];
	$table[] = array("<a href='check_status.php?traPk=$traPk'>Review Track result</a>",'','','');

}

# initializing template header
tpinit($link,$file,$row);

if ( isset($message) and $message !== '' )
{
	echo "<h4 style='color:red'>$message</h4>";
}

echo "<p>\n";
echo ftable($table,'class=submit-track', '', '');
echo "</p>\n";


tpfooter($file);

?>