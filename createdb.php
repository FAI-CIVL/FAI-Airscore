<?php

if (array_key_exists('Create Database', $_REQUEST))
{
    
    $user = $_REQUEST['dbuser'];
    $pass = $_REQUEST['dbpassword'];
    $link = mysql_connect('localhost', $user, $pass);
    or die('Could not connect: ' . mysql_error());

    $file = file_get_contents('./xcdb.sql', false);
    foreach ($file as $com)
    {
        if (stripos("create database", $com))
        {
            $result = mysql_query($com) or die('Create database failed: ' . mysql_error());
            mysql_select_db('xcdb');
        }
        else if (stripos("create table", $com))
        {
            $result = mysql_query($com) or die('Create table failed: ' . mysql_error());
        }
        else if (stripos("insert into", $com))
        {
            $result = mysql_query($com) or die('Insert failed: ' . mysql_error());
        }
    }

    echo "Execute xcdb.sql - complete<br>";

    // Closing connection
    mysql_close($link);
    echo "</head><body>";
    echo "<div id=\"container\"><div id=\"vhead\">";
    echo "<h1>airScore admin - Database created</h1></div>";
}
else 
{
        echo "</head><body>";
        echo "<div id=\"container\"><div id=\"vhead\">";
        echo "<h1>airScore Admin - Database creation</h1></div>";
}
?>
<html>
<head>
<meta http-equiv="cache-control" content="no-cache">
<meta http-equiv="pragma" content="no-cache">
<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
<?php
if (array_key_exists('message', $_REQUEST))
{
    $message = addslashes($_REQUEST['message']);
    echo "<p><b>$message</b><p>\n";
}
else
{
    echo "<p>";
}
?>
<form action="createdb.php" name="xcdbform" method="post">
Enter your details to create the initial database. Only do this once (providing it succeeds!):
<form><center><table>
<tr><td><b>Database User</b></td><td><input type="text" name="dbuser"></td></tr>
<tr><td><b>Password</b></td><td><input type="password" name="dbpassword"></td></tr>
</table>
<input type="submit" value="Create Database">
</center>
</form>
</div>
</body>
</html>

