<?php
require 'admin_startup.php';

$comPk = intval($_REQUEST['comPk']);
$tasPk = intval($_REQUEST['tasPk']);
// adminbar($comPk);

$usePk = auth('system');
$link = db_connect();
$file = __FILE__;

tpadmin($link,$file);

if (addslashes($_REQUEST['sendmail']) == "Send Email to missing Pilots")
{
    check_admin('admin',$usePk,$comPk);
    echo "<p><h4>Send Email to missing Pilots: Task id ($tasPk)</h4></p>";

    # TEST MODE TO BE REMOVED WHEN IN PRODUCTION
    //$email = JFactory::getUser()->email;
    $email = get_user()->email;
    $command = "/home/ubuntu/opt/python-3.6.2/bin/python3 " . BINDIR . "email_pilots.py $tasPk reminder -t $email";
    # TEST MODE END

	#COMMENT TO BE REMOVED IN PRODUCTION
	//$command = "/home/ubuntu/opt/python-3.6.2/bin/python3 " . BINDIR . "email_pilots.py $tasPk reminder";

	$message = shell_exec($command);
	echo '<p class=\'email_script\'>';
	print_r($message);
	echo '</p>';
}

if (addslashes($_REQUEST['sendmail']) == "Send TEST Email to your address only")
{
    check_admin('admin',$usePk,$comPk);
    //$email = JFactory::getUser()->email;
    $email = get_user()->email;
    echo "<p><h4>Send TEST Email to your address only: Task id ($tasPk) - email: $email</h4></p>";

	$command = "/home/ubuntu/opt/python-3.6.2/bin/python3 " . BINDIR . "email_pilots.py $tasPk reminder -t $email";
	$message = shell_exec($command);
	echo '<p class=\'email_script\'>';
	print_r($message);
	echo '</p>';
}


tpfooter($file);

?>
