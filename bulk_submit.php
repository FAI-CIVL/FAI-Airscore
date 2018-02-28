<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">
<div id="vhead"><h1>airScore admin</h1></div>
<?php
require 'authorisation.php';

$comPk = intval($_REQUEST['comPk']);
$tasPk = intval($_REQUEST['tasPk']);
adminbar($comPk);

echo "<p><h2>Bulk Track Submission ($tasPk)</h2></p>";

auth('system');
$link = db_connect();

if (addslashes($_REQUEST['foo']) == 'Send Tracklog')
{
    $copyname = tempnam(FILEDIR, "Task_");

    echo 'copyname: ' . $copyname . "<br />";
    echo 'file name: ' . $_FILES['userfile']['tmp_name'] . "<br />";
    
    clearstatcache();
    if (!file_exists($copyname)) {
    	mkdir($copyname, 0755, true);
    }
    copy($_FILES['userfile']['tmp_name'], $copyname . basename($_FILES['userfile']['tmp_name']));
    chmod($copyname . basename($_FILES['userfile']['tmp_name']), 0644);

    $tempnm = $_FILES['userfile']['tmp_name'];

    $out = '';
    $retv = 0;
    exec(BINDIR . "bulk_igc_reader.pl $tasPk $tempnm", $out, $retv);

    foreach ($out as $txt)
    {
        echo "$txt<br>\n";
    }
}

echo "<b>Done</b><br>";
?>
</div>
</body>
</html>
