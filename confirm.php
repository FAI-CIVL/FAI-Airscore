<html>
<head>
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>
<div id="container">

<?php
require 'authorisation.php';
$restrict='';
$comPk = reqival('comPk');
menubar($comPk);

$return = $_REQUEST['return'];
$action = $_REQUEST['action'];

// Confirm buttons
echo "<p><p><center>\n";
echo "<form action=\"$return\" method=\"post\">";
echo "<table><tr>\n";
echo "<td><button type=\"submit\" name=\"$return?$action\" value=\"confirm\">Confirm $action</button></td>";
echo "<td><button type=\"submit\" name=\"$return\" value=\"cancel\">Cancel</button></td>";
echo "</tr></table>\n";
foreach ($_REQUEST as $key => $value)
{
    echo "<input type=\"hidden\" name=\"$key\" value=\"$value\">";
}
echo "</form>\n";
echo "</center>\n";

?> 
</div></body>
</html>

