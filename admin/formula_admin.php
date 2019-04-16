<?php
require 'admin_startup.php';
require LIBDIR.'dbextra.php';

$usePk = auth('system');
$link = db_connect();
$file = __FILE__;	
$message = '';

# Add a new Formula
if (reqexists('create'))
{
    $name = reqsval('name');
    $type = reqsval('formula');
    $category = reqsval('category');
    $query = "select * from tblFormula where forName='$name' limit 1";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Create region failed: ' . mysqli_connect_error());
    if (mysqli_num_rows($result) > 0)
    {
        $message .= "Unable to create formula $name as it already exists.\n";
    }
    else
    {
		$query = "INSERT INTO tblFormula (forName, forClass, forComClass) values ('$name', '$type', '$category')";
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Create formula failed: ' . mysqli_connect_error());
		$forPk = mysqli_insert_id($link);

		redirect("formula_admin.php?edit=$forPk&created=1");
	}
}

# Update the formula
if (array_key_exists('upformula', $_REQUEST))
{
    $forPk = reqival('forPk');
    $forarr = [];
    $forarr['forName'] = reqsval('name');
    $forarr['forComClass'] = reqsval('category');
    $forarr['forClass'] = reqsval('formula');
    $forarr['forVersion'] = reqsval('version');
    $forarr['forGoalSSPenalty'] = reqfval('sspenalty');
    $forarr['forLinearDist'] = reqfval('lineardist');
    $forarr['forDiffDist'] = reqfval('diffdist');
    $forarr['forDiffRamp'] = reqsval('difframp');
    $forarr['forDiffCalc'] = reqsval('diffcalc');
    $forarr['forDistMeasure'] = reqsval('distmeasure');
    $forarr['forArrival'] = reqsval('arrivalmethod');
	$forarr['forWeightStart'] = reqfval('weightstart');
	$forarr['forWeightArrival'] = reqfval('weightarrival');
	$forarr['forWeightSpeed'] = reqfval('weightspeed');
    $forarr['forStoppedGlideBonus'] = reqfval('glidebonus');

    # check margin percentage
    if ( reqfval('margin') <= 100 )
    {
    	$forarr['forMargin'] = abs( reqfval('margin') ); 
    }
	else
	{
		$forarr['forMargin'] = 0.5;
	}
	
	$sql = mysql_update_array('tblFormula', $forarr, 'forPk', $forPk);
	//echo $sql;
    mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Formula update failed: ' . mysqli_connect_error());
    $message .= "Formula " . reqsval('name') . " correctly updated. \n";
}

if ( reqexists('delformula') )
{
    // implement a nice 'confirm'
    $forPk = reqival('forPk');
	# Check if formula is used by any Comp before deleting
    $query = "SELECT comPk FROM tblForComp WHERE forPk = $forPk LIMIT 1";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Delete check failed: ' . mysqli_connect_error());
    if ( mysqli_num_rows($result) > 0 )
    {
        $message .= "Unable to delete Formula ($forPk) as it is in use in at least a Competition.\n";
    }
	else
	{
		$query = "DELETE FROM tblFormula WHERE forPk = $forPk";
		mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Formula delete failed: ' . mysqli_connect_error());
		
		$message .= "Formula ( $forPk ) correctly deleted. \n";
	}    
}

$ftable = [];

if ( reqexists('edit') )
{
	$forPk = reqival('edit');
	if ( reqexists('created') )
	{
		$message .= "New Formula correctly created ( ID = $forPk ).\n";
	}
	
	$sql = "SELECT F.* FROM tblFormula F WHERE forPk = $forPk";
	$result = mysqli_query($link, $sql);
	if ( mysqli_num_rows($result) == 0 )
	{
		$message .= "We didn't find any Formula with that ID.\n";
	}
	else
	{
		$row = mysqli_fetch_assoc($result);
		//print_r ($row);
		$name = $row['forName'];
		$class = $row['forClass'];
		$comclass = $row['forComClass'];
		$version = $row['forVersion'];
		$sspenalty = $row['forGoalSSpenalty'];
		$lineardist = $row['forLinearDist'];
		$arrival = $row['forArrival'];
		$departure = $row['forDeparture'];
		$diffdist = $row['forDiffDist'];
		$difframp = $row['forDiffRamp'];
		$diffcalc = $row['forDiffCalc'];		
		$distmeasure = $row['forDistMeasure'];
		$weightstart = $row['forWeightStart'];
		$weightarrival = $row['forWeightArrival'];
		$weightspeed = $row['forWeightSpeed'];
		$glidebonus = $row['forStoppedGlideBonus'];
		$arrival = $row['forArrival'];
		$margin = abs($row['forMargin']); # Radius tolerance
		$stoppedelapsed = $row['forStoppedElapsedCalc'];
		$heightarrbonus = $row['forHeightArrBonus'];
		$heightarrlow = $row['forHeightArrLower'];
		$heightarrhi = $row['forHeightArrUpper'];
		
		$ftable[] = array("<form action=\"formula_admin.php?forPk=$forPk\" name=\"formulaadmin\" method=\"post\"> Name: ", fin('name', $name, 8),'Category: ', fselect('category', $comclass, array('PG', 'HG', 'mixed')),'');
		$ftable[] = array('Formula: ', fselect('formula', $class, array('gap', 'pwc')),'Year: ', fin('version', $version, 4),'');
		$ftable[] = array('Distance Measure: ', fselect('distmeasure', $distmeasure, array('average', 'median')), 'Linear Dist (0-1): ', fin('lineardist', $lineardist, 4), '');
		$ftable[] = array('Diff Dist (km): ', fin('diffdist', $diffdist, 4), 'Diff Ramp: ', fselect('difframp', $difframp, array('fixed', 'flexible')), '');
		$ftable[] = array('Diff Calc: ', fselect('diffcalc', $diffcalc, array('all', 'lo')), 'Goal/SS Penalty (0-1): ', fin('sspenalty', $sspenalty, 4), '');
		$ftable[] = array('Speed weighting: ', fin('weightspeed', $weightspeed, 4), 'Start weighting: ', fin('weightstart', $weightstart, 4), '');
		$ftable[] = array('Arrival weighting: ', fin('weightarrival', $weightarrival, 4), 'Method: ', fselect('arrivalmethod', $arrival, [ 'place', 'timed' ]), '');
		$ftable[] = array('Stopped Glide Bonus: ', fin('glidebonus', $glidebonus, 4), 'Radius Margin %: ', fin('margin', $margin, 4), '');
		$ftable[] = array("<input type=\"hidden\" name=\"forPk\" value=\"$forPk\"><input type=\"submit\" name=\"upformula\" value=\"Update Formula\">","<input type=\"submit\" name=\"delformula\" value=\"Delete Formula\">" , "<a href=\"formula_admin.php\">Cancel</a>", '</form>');
	}
}
else
{
	# create a Class selector
	$comclass = "PG";
	
	$sql = "SELECT F.forPk, F.forClass, F.forVersion, F.forName FROM tblFormula F WHERE F.forComClass = '$comclass' ORDER BY F.forClass, F.forName";
	$result = mysqli_query($link, $sql);
	$count = mysqli_num_rows($result);
	//$ftable[] = array("There are $count defined Formulas in $comclass category: ",'','','','');
	$hdr = array(fb('Name'), '', fb('Type'), '', '');
	$ftable[] = $hdr;
	while ( $row = mysqli_fetch_assoc($result) )
	{
		$id = $row['forPk'];
		$name = str_replace('\' ', '\'', str_replace('\'', '\' ', strtoupper($row['forName'])));
		$class = isset($row['forVersion']) ? strtoupper($row['forClass']) . (' ('.$row['forVersion'].') ') : strtoupper($row['forClass']);
		
		# Create the table
		$ftable[] = array($name, '',$class, '', "<a href=\"formula_admin.php?edit=$id\">Edit</a>");
	}
	$ftable[] = array('<hr />', '', '', '', '');
	$ftable[] = array('New Formula:', '', '', '', '');
	$ftable[] = array("<form enctype=\"multipart/form-data\" action=\"formula_admin.php\" name=\"formula\" method=\"post\"><input type=\"hidden\" name=\"category\" value=\"$comclass\">Name: " . fin('name', '', 10), '', fselect('formula', $class, array('gap', 'pwc')), '', fis('create', 'Create', 10) . '</form>');
}






//initializing template header
tpadmin($link,$file);

if ( reqexists('edit') AND isset($name) )
{
	echo "<h4> Formula: $name ($version)</h4>";
}
else
{
	echo "<h4> Defined Formulas </h4>";
	echo "<hr />";
	echo "<i> We have " . $count . " defined formulas in $comclass category.</i>";
	echo "<hr />";
}

if ( $message !== '')
{
	echo "<h4> <span style='color:red'>$message</span> </h4>";
}


echo ftable($ftable,'class=formulatable', '', '');

// echo "<br />";
// echo "<hr />";
// 
// echo "<form enctype=\"multipart/form-data\" action=\"formula_admin.php\" name=\"formula\" method=\"post\">";
// echo "New Formula: " . fin('forname', '', 10);
// echo fis('create', 'Create', 10);
// echo "</form>";




tpfooter($file);

?>
