<?php
require 'admin_startup.php';

function get_classtype($link, $selected='PG')
{
	$list = '';
	$list = "<select name='classtype' id='classtype' onchange=\"document.getElementById('classmain').submit();\">\n";
	$list .= "<option value=''>Class...</option>\n";
	
// 	$sql = "	SELECT 
// 					DISTINCT comClass AS id, 
// 					comClass AS name
// 				FROM 
// 					tblclassification 
// 				ORDER BY 
// 					comClass ASC";
// 	$result = mysqli_query($link, $sql);
// 	while( $class = mysqli_fetch_assoc($result) )
	foreach ( array('PG', 'HG') as &$value )
	{
		$name = $value;
		$id = $value;
		$list .= "<option value='$id'";
		if ($selected == $id)
		{
		  $list .= " selected='selected'";
		}
		$list .= ">$name</option>\n";
	}
	$list .= "</select>\n";
	
	//echo $list . "\n";	
	return $list;
}

function get_certification($link, $claPk, $ranPk, $classtype = 'PG', $selected = 0)
{
	//echo "selected in function: $selected <br />";
	$list = '';
	$list = "<select name='claPk$claPk-rank$ranPk' id='claPk$claPk-rank$ranPk'>\n"; // onchange=\"document.getElementById('claPk$claPk').submit();\"
	$list .= "<option value=''>Certification...</option>\n";
	
	$sql = "	SELECT 
					cerPk AS id, 
					cerName AS name 
				FROM 
					tblCertification 
				WHERE 
					comClass = '$classtype' 
				ORDER BY 
					cerPk ASC";
	$result = mysqli_query($link, $sql);
	while( $cert = mysqli_fetch_assoc($result) )
	{
		$name = $cert['name'];
		$id = $cert['id'];
		$list .= "<option value='$id'";
		if ($selected == $id)
		{
		  $list .= " selected='selected'";
		}
		$list .= ">$name</option>\n";
	}
	#adding the Not used choice
	$list .= "<option value='0'";
	if ($selected == 0)
	{
	  $list .= " selected='selected'";
	}
	$list .= ">Not used</option>\n";
	$list .= "</select>\n";
		
	return $list;
}

function get_ranking($link, $classtype='PG')
{
	$sql = "	SELECT 
					ranPK, 
					ranName 
				FROM 
					tblRanking 
				WHERE 
					comClass = '$classtype' 
				ORDER BY 
					ranPk ASC";
	$result = mysqli_query($link, $sql);
	$row = mysqli_fetch_assoc($result);
		
	return $row;
}


//
// Main Code Begins HERE //
//

auth('system');
$link = db_connect();
$usePk = auth('system');
$claPk = reqival('claPk');
$delreq = reqsval('del');
$classtype = reqsval('classtype') !== '' ? reqsval('classtype') : 'PG';
$file = __FILE__;
$message = '';

if ( $delreq !== '' )
{
	$message .= "Classification <i>$delreq</i> deleted\n";
}

if ( reqexists('cladel') )
{
    // implement a nice 'confirm'
    $query = "select * from tblClassification where claPk=$claPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Classification check failed: ' . mysqli_connect_error());
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    $classification = $row['claName'];
    $query = "select * from tblCompetition C where C.claPk=$claPk limit 1";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Classification used check failed: ' . mysqli_connect_error());
    if (mysqli_num_rows($result) > 0)
    {
        $message .= "Unable to delete $classification as it is in use in at least a Competition.\n";
    }
	else
	{
		$query = "delete from tblClassification where claPk=$claPk";
		mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Classification delete failed: ' . mysqli_connect_error());
		$query = "delete from tblClasCertRank where claPk=$claPk";
		mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Classification Definitions delete failed: ' . mysqli_connect_error());
		
		$message .= "Classification <i>$classification</i> deleted\n";
	}    
}

if (reqexists('create'))
{
    $classname = reqsval('classname');
    $query = "select * from tblClassification where claName='$classname' limit 1";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Check Classification name failed: ' . mysqli_connect_error());
    if (mysqli_num_rows($result) > 0)
    {
        $message .= "Unable to create classification <i>$classname</i> as it already exists.\n";
    }
    else
    {
		$query = "insert into tblClassification (claName, comClass) values ('$classname', '$classtype')";
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Create classification failed: ' . mysqli_connect_error());
		$claPk = mysqli_insert_id($link);
		
		$query = "select * from tblRanking where comClass='$classtype'";
		//echo " query: " . $query . "<br />";
    	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Get Rankings failed: ' . mysqli_connect_error());
    	//echo "result rows:  " . mysqli_num_rows($result) . "<br />";
    	while( $row = mysqli_fetch_assoc($result) )
		{
			$ranPk = $row['ranPk'];
			$query = "insert into tblClasCertRank (claPk, ranPk, cerPk) values ($claPk, $ranPk, 0)";
			//echo " query: " . $query . "<br />";
			mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Create classification definitions failed: ' . mysqli_connect_error());
		}
		//redirect("region_admin.php?regPk=$regPk&created=1");
		$message .= "Classification <i>$classname</i> created.\n";
	}
}

if ( reqexists('claup') )
{
    // implement a nice 'confirm'
    $classname = addslashes($_REQUEST["claPk$claPk-name"]);
    
    //echo "\n UPDATE MODE: \n claPk = $claPk \n Name = $classname \n ";
    
    # Check if name is changed
    $query = "select * from tblClassification where claPk=$claPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Classification check failed: ' . mysqli_connect_error());
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    $oldname = $row['claName'];
    if ( !($oldname == $classname) )
    {
		# Check if new name is already used
		$query = "select * from tblClassification where claName='$classname' and claPk <> $claPk limit 1";
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Check Classification name failed: ' . mysqli_connect_error());
		if (mysqli_num_rows($result) > 0)
		{
			$message .= "Unable to change name as it is already used.<br />\n";
		}
		else
		{
			# Updates name
			$query = "update tblClassification set claName='$classname' where claPk=$claPk";
			mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Classification Name update failed: ' . mysqli_connect_error());
			$message .= "Classification <i>$classname</i> name updated. <br />\n";
		}	
	}
	# Check if classification is used in a comp
	$query = "select * from tblCompetition C where C.claPk=$claPk limit 1";
	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Classification used check failed: ' . mysqli_connect_error());
	if (mysqli_num_rows($result) > 0)
	{
		$message .= "Unable to update definition as <i>$classname</i> is in use in at least a Competition.<br />\n";
	}
	else
	{
		$query = "select * from tblRanking where comClass='$classtype'";
    	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Get Rankings failed: ' . mysqli_connect_error());
    	while( $row = mysqli_fetch_assoc($result) )
		{
			$ranPk = $row['ranPk'];
			$cerPk = addslashes($_REQUEST["claPk$claPk-rank$ranPk"]);
			$query = "UPDATE tblClasCertRank SET cerPk=$cerPk WHERE claPk=$claPk AND ranPk=$ranPk";
			mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Update classification definitions failed: ' . mysqli_connect_error());
		}
		
		# Check if female and team choice are changed
		$female = isset($_POST["femalebox-$claPk"]) ? 1 : 0;
		$team = isset($_POST["teambox-$claPk"]) ? 1 : 0;
		$query = "UPDATE tblClassification SET claFem=$female, claTeam=$team WHERE claPk=$claPk";
		mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Update female / team definitions failed: ' . mysqli_connect_error());
		//redirect("region_admin.php?regPk=$regPk&created=1");
		$message .= "<i>$classname</i> definition updated.\n";
	} 
}

# Create Tables
$dtable = [];

$wpt = 0;
$openair = 0;

# Get Classifications list
$sql = "	SELECT 
				* 
			FROM tblClassification 
			WHERE comClass = '$classtype' ";
				
$result = mysqli_query($link, $sql);

if ( mysqli_num_rows($result) == 0 )
{
	$message .= "We didn't find any defined Classification.\n";
}
else
{
	# Create Table Header
	$line = [];
	$line[] = 'Name';
	$sql = "	SELECT 
					DISTINCT ranPk, 
					ranName 
				FROM 
					tblRanking 
				WHERE 
					comClass = '$classtype'
				ORDER BY ranPk ASC";
	$head = mysqli_query($link, $sql);
	while( $ran = mysqli_fetch_assoc($head) )
	{
		//$name = $ran['ranName'];
		$line[] = $ran['ranName'];
	}
	$line[] = 'Female Results';
	$line[] = 'Team Results';
	$line[] = '';
	$line[] = '';
	$dtable[] = $line;
	
	# Get each Classification Details
	while ( $def = mysqli_fetch_assoc($result) )
	{
		//print_r($def);
		$claPk = $def['claPk'];
		$classname = $def['claName'];
		$clafemale = $def['claFem'];
		$clateam = $def['claTeam'];
		
		$line = [];
		//echo " claName: " . $def['claName'] . " claPk: " . $claPk . "female: " . $clafemale . "team: " . $clateam ."\n";
		$line[] = "<form enctype=\"multipart/form-data\" action=\"class_admin.php?claPk=$claPk\" name=\"claPk$claPk\" id=\"claPk$claPk\" method=\"post\"> \n <input type=\"text\" name=\"claPk$claPk-name\" id=\"claPk$claPk-name\" value=\"$classname\" size=15>";
		# Classification definitions
		$sql = "	SELECT 
						CC.cerPk AS Cert, 
						CC.ranPk AS Rank, 
						IF (
							CC.cerPk = 0, 
							'Not Used', 
							(
								SELECT 
									C.cerName 
								FROM 
									tblCertification C 
								WHERE 
									C.cerPk = CC.cerPk 
							)
						) AS Name 
					FROM 
						tblClasCertRank CC 
					WHERE 
						CC.claPk = $claPk 
					ORDER BY 
						CC.ranPk ASC";
				
		$res = mysqli_query($link, $sql);
		if ( mysqli_num_rows($res) > 0 )
		{
 			while( $cer = mysqli_fetch_assoc($res) )
 			{
				$ranPk =  $cer['Rank'];
				//echo " ranPk: " . $cer['Rank'];
				$selected = $cer['Cert'];
				//echo " selected: " . $selected . " \n";
				$line[] = get_certification($link, $claPk, $ranPk, $classtype, $selected);
				//print_r($line);
			}
		}
		$line[] = fic("femalebox-$claPk", "", $clafemale);
		$line[] = fic("teambox-$claPk", "", $clateam);		
		$line[] = fis('claup', 'Update', 10);
		$line[] = fis('cladel', 'DELETE', 10) . "</form>";
		$dtable[] = $line;
	}
}

//initializing template header
tpadmin($link,$file);

echo "<h4> Classification definitions </h4>" . PHP_EOL;
if ( $message !== '')
{
	echo "<h4> <span style='color:red'>$message</span> </h4>" . PHP_EOL;
}
echo "<hr />" . PHP_EOL;
echo "<form enctype=\"multipart/form-data\" action=\"class_admin.php?classtype=$classtype\" name=\"classmain\" id=\"classmain\" method=\"post\">";
echo "Class: " . get_classtype($link, $classtype);
echo "</form>" . PHP_EOL;
echo "<br />" . PHP_EOL;
echo "<hr />" . PHP_EOL;
echo ftable($dtable,'class=rclassdtable', '', '');
echo "<br />" . PHP_EOL;
echo "<hr />" . PHP_EOL;
echo "<form enctype=\"multipart/form-data\" action=\"class_admin.php\" name=\"create-class\" method=\"post\">";
echo "New Classification Definition: " . fin('classname', '', 10);
echo fis('create', 'Create', 10);
echo "</form>" . PHP_EOL;

// echo "<hr />";
// echo ftable($xtable,'class=regionxtable', '', '');
// echo "</form>";
// echo "<br />";
// echo "<hr />";
// echo ftable($ttable,'class=regionttable', '', '');
// echo "<br />";
// echo "<hr />";
// echo "<form enctype=\"multipart/form-data\" action=\"region_admin.php?regPk=$regPk\" name=\"region2\" id=\"region2\" method=\"post\">";
// echo ftable($ftable,'class=regionftable', '', '');
// echo "<hr />";
// echo ftable($dtable,'class=regiondtable', '', '');
// echo "</form>";

tpfooter($file);

?>


