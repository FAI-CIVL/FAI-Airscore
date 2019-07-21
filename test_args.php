<html>
<head>
</head>
<body>
<hr />

<?php

//require 'authorisation.php';
//require_once 'format.php';
require_once('defines.php');

echo "cerco di eseguire il file: ".(BINDIR . "test.pl")."<br />";

echo exec(BINDIR . "test.pl")."<br />";

// echo "cerco di eseguire il file: ".(BINDIR . "task_up.pl 1")."<br />";
// $out = '';
// $retv = 0;
// exec(BINDIR . "task_up.pl 1", $out, $retv);
// echo exec(BINDIR . "task_up.pl 1", $out, $retv)."<br />";
// echo "out = "."<br />";
// var_dump($out);
// echo "<br />";
// 
echo "<hr />";

 echo "Hostname: ". @php_uname(n) ."<br />";
 if (function_exists( 'shell_exec' )) {
  echo "Shell Exec Exists " . "<br />";
 } else {
  echo "Shell Exec does NOT Exist " . "<br />";
 }
 echo "Hostname: ". @gethostbyname(trim(`hostname`)) . "<br />";
 echo "Server IP: ". $_SERVER['SERVER_ADDR'] . "<br />";
 echo "Platform: ". @php_uname(s) ." ". @php_uname(r) ." ". @php_uname(v) ."<br />";
 echo "Architecture: ". @php_uname(m) ."<br />";
 echo "Username: ". get_current_user () ." ( UiD: ". getmyuid() .", GiD: ". getmygid() ." )<br />";
 echo "Curent Path: ". getcwd () ."<br />";
 echo "Server Type: ". $_SERVER['SERVER_SOFTWARE'] . "<br />";
 echo "Server Admin: ". $_SERVER['SERVER_ADMIN'] . "<br />";
 echo "Server Signature: ". $_SERVER['SERVER_SIGNATURE'] ."<br />";
 echo "Server Protocol: ". $_SERVER['SERVER_PROTOCOL'] ."<br />";
 echo "Server Mode: ". $_SERVER['GATEWAY_INTERFACE'] ."<br />";
 echo "Userv Apache is using to run: " . exec('whoami')."<br />";
 
echo "<hr />";
echo "<br />cerco di eseguire il comando: "."python3 " . BINDIR . "test2.py"."<br />";
$message = shell_exec("python3 " . BINDIR . "test2.py reminder");
print_r($message);

$task =3;
$file = "reminder";
$confirm = "-c";
echo "<hr />";
echo "cerco di eseguire il comando: ".(BINDIR . "test_args.py $task $file $confirm")."<br />";



$command = "python3 " . BINDIR . "test_args.py $task $file $confirm";
$message = exec("python3 " . BINDIR . "test_args.py '".$task."' '".$file."' '".$confirm."'");
print_r($message);

?>

</body>
</html>
