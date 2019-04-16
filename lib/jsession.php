<?php 

function create_session($id)
{

	if ( isset($id) && $id > 0 )
	{	## Initializing Session ##
		$_SESSION['id'] = $id;

		$link = db_connect();
		$sql = "SELECT
					P.pilLogin AS login,
					CONCAT(
						P.pilFirstName,
						' ',
						P.pilLastName
					) AS name,
					IF(U.usePk > 0, TRUE, FALSE) AS isAdmin
				FROM
					tblPilot P
				LEFT JOIN tblUser U ON
					P.pilPk = U.usePk
				WHERE
					pilPk = $id
				LIMIT 1";
		$result = mysqli_query($link, $sql);
		$pil = mysqli_fetch_object($result);
		//$selected = $id->maxid;
		//$row = mysqli_fetch_assoc($result);
		
		//print_r($pil);
		$_SESSION['login'] = $pil->login;
		$_SESSION['name'] = $pil->name;
		$_SESSION['isAdmin'] = $pil->isAdmin;
		//print_r($_SESSION);
		
		mysqli_free_result($result);
		mysqli_close($link);
	}
}

function get_user()
{
	if ( isset($_SESSION['id']) && $_SESSION['id'] > 0 )
	{
		$user = new stdClass();
		$user->id = $_SESSION['id'];
		$user->login = $_SESSION['login'];
		$user->name = $_SESSION['name'];
		$user->isAdmin = $_SESSION['isAdmin'];
		//print_r($user);
	}
	return $user;
}

function close_session()
{
	// Desetta tutte le variabili di sessione.
	session_unset();
	// Infine , distrugge la sessione.
	session_destroy();
}
 
?>