<?php
require 'format.php';
require 'dbextra.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

echo "<html><head>";
echo "<meta http-equiv=\"cache-control\" content=\"no-cache\">";
echo "<meta http-equiv=\"pragma\" content=\"no-cache\">";
echo "<link HREF=\"xcstyle.css\" REL=\"stylesheet\" TYPE=\"text/css\">";

if (array_key_exists('createdb', $_REQUEST))
{
    
    echo "Execute xcdb.sql - start<br>";
    
    $user = esc($_REQUEST['dbuser']);
    $pass = esc($_REQUEST['dbpassword']);
    $db = esc($_REQUEST['database']);
//    $link = mysql_connect('localhost', $user, $pass) or die('Could not connect: ' . mysql_error());
    $link = mysqli_connect('localhost', $user, $pass) or die('Error ' . mysqli_errno($link) . ' Could not connect: ' . mysqli_connect_error());

//    if (!mysql_select_db($db))
    if (!mysqli_select_db($link, $db))
    {
//        mysql_query("create database $db") or die("Unable to create $db: " . mysql_error());
//        mysql_select_db($db) or die("Failed to create $db");
        mysqli_query($link, "create database $db") or die('Error ' . mysqli_errno($link) . ' Unable to create $db: ' . mysqli_connect_error());
        mysqli_select_db($link, $db) or die("Failed to create $db");
    }

    # write a config file for later use

    # get the SQL and run it
    $file = file_get_contents('./xcdb.sql', false);
    $arr = explode("\n\n", $file);
    foreach ($arr as $com)
    {
        //echo $com . "<br>";
        $n = stripos($com, "create database");
        if ($n !== false)
        {
            // ignore since we've asked for it.
            echo "Ignoring create database: $com<br>";
            next;
            //$result = mysql_query($com) or die('Create database failed: ' . mysql_error());
            //mysql_select_db($db);
        }

        $n = stripos($com, "create table");
        if ($n !== false)
        {
            //echo substr($com,$n) . "<br>";
//            $result = mysql_query(substr($com,$n)) or die("Create table failed ($com): " . mysql_error());
            $result = mysqli_query($link, substr($com,$n)) or die('Error ' . mysqli_errno($link) . ' Create table failed ($com): ' . mysqli_connect_error());
            next;
        }

        $n = stripos($com, "insert into");
        if ($n !== false)
        {
            //echo substr($com,$n) . "<br>";
//            $result = mysql_query(substr($com,$n)) or die("Insert failed ($com): " . mysql_error());
            $result = mysqli_query($link, substr($com,$n)) or die('Error ' . mysqli_errno($link) . ' Insert failed  ($com): ' . mysqli_connect_error());
        }
    }

    echo "Execute xcdb.sql - complete<br>";
    // Closing connection
//    mysql_close($link);
    mysqli_close($link);

    mkdir("./Tracks", 0775);
    mkdir("./Tracks/2013", 0775);
    mkdir("./Tracks/2014", 0775);
    mkdir("./Tracks/2015", 0775);
    mkdir("./Tracks/2016", 0775);
    mkdir("./Tracks/2017", 0775);
    mkdir("./Tracks/2018", 0775);
    mkdir("./Tracks/2019", 0775);
    mkdir("./Tracks/2020", 0775);

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
Enter database details to create the initial tables for AirScore. <i>Only do this once (providing it succeeds!).</i>
<p>
<form>
<center>
<table>
<tr><td><b>Database</b></td><td><input type="text" name="database"></td></tr>
<tr><td><b>Database User</b></td><td><input type="text" name="dbuser"></td></tr>
<tr><td><b>Password</b></td><td><input type="password" name="dbpassword"></td></tr>
</table>
<input type="submit" name="createdb" value="Create Database">
</center>
</form>
</div>
</body>
</html>

