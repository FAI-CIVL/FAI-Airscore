<?php
ob_start(); 

require 'template.php';

/**
 * Constant that is checked in included files to prevent direct access.
 * define() is used in the installation folder rather than "const" to not error for PHP 5.2 and lower
 */ 
define('_JEXEC', 1);

$message = '';

# Get a redirect url if available
$redirect =  ( isset($_REQUEST['location']) ? $_REQUEST['location'] : 'index.php' );
# Check if user came was redirected from another page
if ( isset($_REQUEST['logreq']) )
{
	$message ='You need to login first';
}
 

if (array_key_exists('login', $_REQUEST))
{
	
	## Login on WP multisite ##

	$user = $_REQUEST['login'];
	$pass = $_REQUEST['passwd'];
	$server = 'https://legapiloti.it';


	$curl = curl_init();
	curl_setopt($curl, CURLOPT_URL, $server.'/wp-json/');
	curl_setopt($curl, CURLOPT_USERPWD, $user.':'.$pass); //Your credentials goes here
	curl_setopt($curl, CURLOPT_NOBODY, TRUE); // remove body 

	$curl_response = curl_exec($curl);
	$httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
	curl_close($curl);
	//print_r($curl_response);
	
	if ( $httpCode == 200)
	{
		# USER CREDENTIALS EXIST 
		# GETTING USER ID
		
		//print_r('YAY');
		
		$curl = curl_init();
		curl_setopt($curl, CURLOPT_URL, $server.'/wp-json/wp/v2/users/me');
		curl_setopt($curl, CURLOPT_USERPWD, $user.':'.$pass); //Your credentials goes here
		curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
		curl_setopt($curl, CURLOPT_HTTPHEADER, array('Content-Type:application/json', 'Accept:application/json'));

		$curl_response = curl_exec($curl);
		//$info = curl_getinfo($curl);
		curl_close($curl);
		//var_dump(json_decode($curl_response));
		$user = json_decode($curl_response)->{'id'};
		create_session($user);
		
		#redirect logged in user
   		redirect($redirect);		
	}
	else
	{
		# LOGIN ERROR
		die('Cound not find user in the database');
	}
}
else if (array_key_exists('logout', $_REQUEST))
{
	close_session();
	$message = 'User logged out';
}

if (version_compare(PHP_VERSION, '5.3.1', '<'))
{
    die('Your host needs to use PHP 5.3.1 or higher to run this version of Joomla!');
}

//initializing template header
tpinit($link,$file,$row);

if ( isset($message) and $message !== '' )
{
	echo "<h4 style='color:red'>$message</h4>";
}
echo "	<p class='loginform'>
		<form action=\"jlogin.php?location=$redirect\" name=\"loginform\" method=\"post\">
			<center>
			<h3>airScore Admin - Login</h3>
			<table>
			<tr><td><b>Username</b></td><td><input type=\"text\" name=\"login\"></td></tr>
			<tr><td><b>Password</b></td><td><input type=\"password\" name=\"passwd\"></td></tr>
			</table>
			<input type=\"submit\" value=\"Login\">
			</center>
		</form>
		</p>
	";


tpfooter($file);
ob_end_flush();

?>