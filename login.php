<?php
ob_start();

require 'authorisation.php';

?>
<html>
<head>
	<meta http-equiv="cache-control" content="no-cache">
	<meta http-equiv="pragma" content="no-cache">
	<link HREF="xcstyle.css" REL="stylesheet" TYPE="text/css">
</head>
<body>

<?php

if (array_key_exists('login', $_REQUEST))
{
        // Connecting, selecting database
        $link = db_connect();

        $login = addslashes($_REQUEST['login']);
        $passwd = addslashes($_REQUEST['passwd']);
        $ip = $_SERVER['REMOTE_ADDR'];

        $query = "select usePk from tblUser where useLogin='$login' and usePassword='$passwd'";
//      $result = mysql_query($query) or die('Query failed: ' . mysql_error());
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
			
//      if (mysql_num_rows($result) > 0)
		if (mysqli_num_rows($result) > 0)
        {
//          $usePk = mysql_result($result,0,0);
			$usePk = mysqli_result($result,0,0);
        }
        else
        {
            $usePk = 0;
        }
        if ($usePk > 0)
        {
            $magic = rand() % 100000000000;
            $query= "insert into tblUserSession (usePk, useSession, useIP) values ($usePk, '$magic', '$ip')";
//          $result = mysql_query($query) or die('Query failed: ' . mysql_error());
			$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
            # setCookie 
            if (setcookie("XCauth", $magic))
            {
                # redirect to main screen ...
                redirect('comp_admin.php');
            }

        }

        // Closing connection
        mysqli_close($link);
        echo "<div id=\"container\"><div id=\"vhead\">";
        echo "<h1>airScore admin - authorisation failed</h1></div>";
}
else if (array_key_exists('logout', $_REQUEST))
{
        // Connecting, selecting database
        $link = db_connect();

        $magic = addslashes($_COOKIE['XCauth']);
        $ip = addslashes($_SERVER['REMOTE_ADDR']);
        $query = "delete from tblUserSession where useSession='$magic' and useIP='$ip'";
//      $result = mysql_query($query) or die('Query failed: ' . mysql_error());
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());

        setcookie("XCauth", '');
        echo "<div id=\"container\"><div id=\"vhead\">";
        echo "<h1>airScore Admin - Login</h1></div>";
}
else 
{
        echo "<div id=\"container\"><div id=\"vhead\">";
        echo "<h1>airScore Admin - Login</h1></div>";
}

ob_end_flush();
?>

<form action="login.php" name="loginform" method="post">
<form><center><table>
<tr><td><b>Username</b></td><td><input type="text" name="login"></td></tr>
<tr><td><b>Password</b></td><td><input type="password" name="passwd"></td></tr>
</table>
<input type="submit" value="Login">
</center>
</form>
</div>
</body>
</html>