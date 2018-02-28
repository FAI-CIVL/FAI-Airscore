<?php
require_once 'authorisation.php';

function tpinit($link,$file,$row=0,$active=0)
{
	$title = '';
	$mainheader = '';
	$contentheader = '';
	// Retrieving correct Info to display in header
	if ( strpos($file, 'index') )
	{
		$title = 'AirScore - Online Scoring Tool';
		$mainheader = 'LP AirScore';
		$contentheader = '';
	}
	elseif ( strpos($file, 'comp') )
	{
		// Get Comp Info
		if ($row)
		{
			$comName = isset($row['comName']) ? $row['comName'] : '';
			$title = 'AirScore - '.isset($row['comName']) ? $row['comName'] : '';
			$comDateFrom = substr(isset($row['comDateFrom']) ? $row['comDateFrom'] : '',0,10);
			$comDateTo = substr(isset($row['comDateTo']) ? $row['comDateTo'] : '',0,10);
			$comPk = $row['comPk'];	
			$mainheader = $comName;		
			$contentheader = 'Results';			
		}
		else
		{
			echo "Sorry, no Competition found matching criteria.";
		}						
	}
	elseif ( strpos($file, 'task') )
	{
		// Get Task Info
		if ($row)
		{
			$comName = $row['comName'];
			$comUrl = '"comp_result.php?comPk='.$row['comPk'].'"';
			$tasName = $row['tasName'];
			$title = 'AirScore - '.(isset($row['comName']) ? $row['comName'] : '').' '.$tasName;
			$tasDate = $row['tasDate'];
			$tasTaskType = $row['tasTaskType'];			
			$mainheader = '<a href='.$comUrl.'>'.$comName.'</a> | '.$tasName;
			$contentheader = $tasName.' : '.$tasDate;
		}
		else
		{
			echo "Sorry, no Task found matching criteria.";
		}	
	}
	elseif ( strpos($file, 'map') )
	{
		// Check if it is a tracklog / task map or a waypoints map
		if ( strpos($file, 'waypoint') )
		{
			if ( isset($_REQUEST['regPk']) )
			{
				$regPk = intval($_REQUEST['regPk']);
				$sql = "SELECT regDescription FROM tblRegion WHERE regPk=$regPk";
				$result = mysqli_query($link, $sql);
				$row = mysqli_fetch_array($result, MYSQLI_BOTH);
				$title = 'AirScore - '.$row['regDescription'];
				$mainheader = 'Waypoints Map: '.$row['regDescription'];
				$contentheader = $row['regDescription'];
			}
			else
			{
				echo "Sorry, no Waypoints file found matching criteria.";
			}
		}
		// Get Task Info
		elseif ($row)
		{
			$comName = $row['comName'];
			$comUrl = '"comp_result.php?comPk='.$row['comPk'].'"';
			$tasName = $row['tasName'];
			$title = 'AirScore - '.(isset($row['comName']) ? $row['comName'] : '').' '.$tasName;
			$tasDate = $row['tasDate'];
			$tasTaskType = $row['tasTaskType'];			
			$mainheader = '<a href='.$comUrl.'>'.$comName.'</a> | '.$tasName;
			$contentheader = $tasName.' : '.$tasDate;
		}
		else
		{
			echo "Sorry, no Task found matching criteria.";
		}	
	}
	
	// displaying header
	htmlhead($file,$title);
	// adds google maps scripts to map pages
	if ( strpos($file, 'map') )
	{
		hcmapjs();
		hcscripts([ 'js/rjson.js', 'js/json2.js', 'js/sprintf.js', 'js/plot_trackv4.js', 'js/microajax.minified.js', 'js/uair.js', 'js/plot_task.js' ]);
		if ( !strpos($file, 'waypoint') )
		{
			echo '<script>';
			sajax_show_javascript();
			echo "</script>\n";
		}
	}
	echo "</head>";
	echo "<body id=\"page-top\">";
	// check if it's an admin side page
	if ( strpos($file, 'admin') or strpos($file, 'competition') )
	{
		tpnavadmin($link,$file,$row,$title,$active);
	}
	else
	{
		tpnavigator($link,$file,$row,$title,$active);
	}	
	tpheader($link,$file,$row,$mainheader);
	tpcontent($title,$contentheader);	
}

function tpadmin($link,$file,$row=0,$active=0)
{
	// Retrieving correct Info to display in header
// 	$comPk = intval($_REQUEST['comPk']);
// 	$tasPk = intval($_REQUEST['tasPk']);
// 	if ( isset($comPk) )
// 	{
// 		if ( isset($tasPk) )
// 		{
// 			// Get Task Info
// 			if ($row)
// 			{
// 				$comName = $row['comName'];
// 				$comUrl = '"comp_result.php?comPk='.$row['comPk'].'"';
// 				$tasName = $row['tasName'];
// 				$title = 'Administration - '.(isset($row['comName']) ? $row['comName'] : '').' '.$tasName;
// 				$tasDate = $row['tasDate'];
// 				$tasTaskType = $row['tasTaskType'];			
// 				$mainheader = '<a href='.$comUrl.'>'.$comName.'</a> | '.$tasName;
// 				$contentheader = $tasName.' : '.$tasDate;
// 			}
// 			else
// 			{
// 				echo "Sorry, no Task found matching criteria.";
// 			}	
// 
// 		}
// 		else
// 		{
// 			// Get Comp Info
// 			if ($row)
// 			{
// 				$comName = isset($row['comName']) ? $row['comName'] : '';
// 				$title = 'Administration - '.isset($row['comName']) ? $row['comName'] : '';
// 				$comDateFrom = substr(isset($row['comDateFrom']) ? $row['comDateFrom'] : '',0,10);
// 				$comDateTo = substr(isset($row['comDateTo']) ? $row['comDateTo'] : '',0,10);
// 				$comPk = $row['comPk'];	
// 				$mainheader = $comName;		
// 				$contentheader = 'Results';			
// 			}
// 			else
// 			{
// 				echo "Sorry, no Competition found matching criteria.";
// 			}
// 		}
// 	}
// 	else
// 	{
// 		$title = 'AirScore - Administration';
// 		$mainheader = 'LP AirScore Administration';
// 		$contentheader = '';
// 	}
	
	$title = 'LP AirScore Administration';
	if ( isset($row['comPk']) )
	{
		$comPk = $row['comPk'];
		$contentheader = $row['comName'];
	}
	else
	{
		$comPk = '';
		$contentheader = 'Global Admin';
	}
	// displaying header
	htmlhead($file,$title);
	// adds google maps scripts to map pages
	if ( strpos($file, 'map') )
	{
		hcmapjs();
		hcscripts([ 'js/rjson.js', 'js/json2.js', 'js/sprintf.js', 'js/plot_trackv4.js', 'js/microajax.minified.js', 'js/uair.js', 'js/plot_task.js' ]);
		echo '<script>';
		sajax_show_javascript();
		echo "</script>\n";
	}
	echo "</head>";
	echo "<body id=\"page-top\">";

	tpnavadmin($link,$file,$row,$title,$active);
// 	tpheader($link,$file,$row,$mainheader);
	echo "<!-- Header Place-holder -->";
	echo "<header class=\"place-holder\">";
	echo "</header>";
	tpcontent($title,$contentheader);	
}

function printhd($title)
{
	echo "
	<?xml version=\"1.0\" encoding=\"UTF-8\"?>
	<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\" \"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">
	<html xmlns=\"http://www.w3.org/1999/xhtml\">
	<head>
	  <title>$title</title>
	  <meta http-equiv=\"content-type\" content=\"application/xhtml+xml; charset=UTF-8\" />
	  <meta name=\"author\" content=\"highcloud.net\" />
	  <meta name=\"description\" content=\"Printable highcloud web page\" />
	  <link rel=\"stylesheet\" type=\"text/css\" href=\"printer.css\" media=\"screen\" />
	  <link rel=\"stylesheet\" type=\"text/css\" href=\"printer.css\" media=\"print\" />
	</head>
	";
}

function htmlhead($file,$title)
{
	echo "
	
	<!DOCTYPE html>
	<html lang=\"en\">
	
	<head>

		<meta charset=\"utf-8\">
		<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, shrink-to-fit=no\">
		<meta name=\"author\" content=\"fullahead.org\" />
		<meta name=\"keywords\" content=\"AirScore, paragliding, hangliding, competition, scoring software\" />
		<meta name=\"description\" content=\"A free opensource online scoring application for paragliding and hangliding competitions\" />
		<meta name=\"robots\" content=\"index, follow, noarchive\" />
		<meta name=\"googlebot\" content=\"noarchive\" />

		<title>$title</title>

		<!-- Bootstrap core CSS -->
		<link href=\"vendor/bootstrap/css/bootstrap.min.css\" rel=\"stylesheet\">

		<!-- Custom fonts for this template -->
		<link href=\"vendor/font-awesome/css/font-awesome.min.css\" rel=\"stylesheet\" type=\"text/css\">
		<link href=\"https://fonts.googleapis.com/css?family=Montserrat:400,700\" rel=\"stylesheet\" type=\"text/css\">
		<link href=\"https://fonts.googleapis.com/css?family=Lato:400,700,400italic,700italic\" rel=\"stylesheet\" type=\"text/css\">

		<!-- Plugin CSS -->
		<link href=\"vendor/magnific-popup/magnific-popup.css\" rel=\"stylesheet\" type=\"text/css\">

		<!-- Custom styles for this template -->
		<!-- <link href=\"css/freelancer.min.css\" rel=\"stylesheet\"> -->
		
		<!-- Styles added for AirScore -->
		";
		if ( strpos($file, 'admin') )
		{
			echo "<link href=\"css/airscore_admin.css\" rel=\"stylesheet\">";
		}
		else
		{
			echo "<link href=\"css/airscore.css\" rel=\"stylesheet\">";
		}
		echo "
		<!-- Custom styles for printing -->
		<link rel=\"stylesheet\" type=\"text/css\" href=\"css/printer.css\" media=\"print\" />
		";
	
}


function tptop($file,$link,$param,$title,$active=0,$page='')
{
	echo "<body id=\"page-top\">";
	tpnavigator($title,$active,$page);
	tpheader($file,$link,$param,$title,$active,$page);	
}

function tpnavigator($link,$file,$row,$title,$active=0)
{
	$comPk = isset($row['comPk']) ? $row['comPk'] : null;
	$tasPk = isset($row['tasPk']) ? $row['tasPk'] : null;
	$regPk = isset($row['regPk']) ? $row['regPk'] : null;
	// echo "in row regpk = ".$row['regPk'];
	// check if we have a comp and retrieves waypoints if not specified
	if ( isset($comPk) and !isset($regPk) )
	{
    	// echo "faccio la query";
    	$query = "SELECT DISTINCT T.regPk FROM tblTask T where T.comPk=$comPk";
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Comp query failed: ' . mysqli_connect_error());
		$reg = mysqli_fetch_assoc($result);
		if ($reg)
		{
			$regPk = $reg['regPk'];
			// echo "la query trova ".$reg['regPk'];
		}
	}
	elseif ( isset($_REQUEST['regPk']) )
	{
		$regPk = intval($_REQUEST['regPk']);
	}
	// echo "regpk= ".$regPk;
	echo "	
	<!-- Navigation -->
    <nav class=\"navbar navbar-expand-lg bg-secondary fixed-top text-uppercase\" id=\"mainNav\">
      <div class=\"container\">
        <a class=\"navbar-brand js-scroll-trigger\" href=\"#page-top\">LP AirScore</a>
        <button class=\"navbar-toggler navbar-toggler-right text-uppercase bg-primary text-white rounded\" type=\"button\" data-toggle=\"collapse\" data-target=\"#navbarResponsive\" aria-controls=\"navbarResponsive\" aria-expanded=\"false\" aria-label=\"Toggle navigation\">
          Menu
          <i class=\"fa fa-bars\"></i>
        </button>
        <div class=\"collapse navbar-collapse\" id=\"navbarResponsive\">
          <ul class=\"navbar-nav ml-auto\">
          	<li class=\"nav-item mx-0 mx-lg-1\">
              <a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"index.php\">Home</a>
            </li>
            ";
    if ( isset($comPk) )
	{
    	echo "
    		<li class=\"nav-item mx-0 mx-lg-1\">
              <a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"comp_result.php?comPk=$comPk\">Results</a>
            </li>
            ";
    }
    if ( isset($regPk) )
    {
    	echo "
            <li class=\"nav-item mx-0 mx-lg-1\">
              <a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"waypoint_map.php?regPk=$regPk\">Waypoints Map</a>
            </li>
            ";
    }
    echo "        
          </ul>
        </div>
      </div>
    </nav>	
	";
}

function tpnavadmin($link,$file,$row,$title,$active=0)
{
	$comPk = isset($row['comPk']) ? $row['comPk'] : null;
	echo "	
	<!-- Admin Navigation -->
    <nav class=\"navbar navbar-expand-lg bg-secondary fixed-top text-uppercase\" id=\"mainNav\">
      <div class=\"container\">
        <a class=\"navbar-brand js-scroll-trigger\" href=\"comp_admin.php\">AirScore Admin</a>
        <button class=\"navbar-toggler navbar-toggler-right text-uppercase bg-primary text-white rounded\" type=\"button\" data-toggle=\"collapse\" data-target=\"#navbarResponsive\" aria-controls=\"navbarResponsive\" aria-expanded=\"false\" aria-label=\"Toggle navigation\">
          Menu
          <i class=\"fa fa-bars\"></i>
        </button>
        <div class=\"collapse navbar-collapse\" id=\"navbarResponsive\">
          <ul class=\"navbar-nav ml-auto\">
            <li class=\"nav-item mx-0 mx-lg-1\">
    ";
    if (check_auth("system"))
    {
        echo "<a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"login.php?logout=1\">Logout</a>";
    }
    else
    {
        echo "<a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"login.php?logout=1\">Logout</a>";
    }
    
    echo "
            </li>
			<li class=\"nav-item mx-0 mx-lg-1\">
              <a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"comp_admin.php\">Competitions</a>
            </li>
    ";
    if ( isset($comPk) )
	{
        $comEntryRestrict = $row['comEntryRestrict'];
        echo "
        	<li class=\"nav-item mx-0 mx-lg-1\">
              <a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"comp_result.php?comPk=$comPk\">Scores</a>
            </li>
            <li class=\"nav-item mx-0 mx-lg-1\">
              <a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"track_admin.php?comPk=$comPk\">Tracks</a>
            </li>
            <li class=\"nav-item mx-0 mx-lg-1\">
              <a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"team_admin.php?comPk=$comPk\">Teams</a>
            </li>
            <li class=\"nav-item mx-0 mx-lg-1\">
              <a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"pilot_admin.php?comPk=$comPk\">Pilots</a>
            </li>
        ";
        if ($comEntryRestrict == 'registered')
        {
            echo "
            	<li class=\"nav-item mx-0 mx-lg-1\">
              		<a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"registration.php?comPk=$comPk\">Registration</a>
              	</li>
            ";
        }
    }
	else
	{
		echo "
			<li class=\"nav-item mx-0 mx-lg-1\">
			  <a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"track_admin.php\">Tracks</a>
			</li>
			<li class=\"nav-item mx-0 mx-lg-1\">
			  <a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"pilot_admin.php\">Pilots</a>
			</li>
		";

	}
	echo"    
            <li class=\"nav-item mx-0 mx-lg-1\">
              <a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"region_admin.php\">Waypoints</a>
            </li>
            <li class=\"nav-item mx-0 mx-lg-1\">
              <a class=\"nav-link py-3 px-0 px-lg-3 rounded js-scroll-trigger\" href=\"airspace_admin.php\">Airspace</a>
            </li>
          </ul>
        </div>
      </div>
    </nav>	
	";
}

function tpheader($link,$file,$row,$page='')
{
	echo "
	<!-- Header -->
    <header class=\"masthead bg-primary text-white text-center\">
      <div class=\"container\">
		<!-- <img class=\"img-fluid mb-5 d-block mx-auto\" src=\"img/profile.png\" alt=\"profile image\"> -->
        <h1 class=\"text-uppercase mb-0\">$page</h1>
        <!-- <hr class=\"star-light\"> -->
        <!-- <h2 class=\"font-weight-light mb-0\">Web Developer - Graphic Artist - User Experience Designer</h2> -->
	";
	if ( strpos($file, 'index') )
	{
	    $param = $row;
	    echo "	<div class=\"row\">
  					<div class=\"column\">
  			";
	    seasoninfo($row);
	    echo "
    		</div>
  			<div class=\"column\">
	  	";
// 			if ($param > 1)
// 			{
// 				hcclosedcomps($link, $page);
// 			}
// 			else
// 			{
// 				hcclosedcomps($link);
// 			}
 	   echo "
			</div>
		</div>
		";
	}
	elseif ( strpos($file, 'comp') )
	{
	    echo "	<div class=\"row\">
  					<div class=\"column\">
  			";
  		hccompinfo($row);
	    echo "
    		</div>
  			<div class=\"column\">
	  		";
		hcscoreinfo($link,$row);
		echo "
			</div>
		</div>
		";
	}
	elseif ( strpos($file, 'task') )
	{
	    echo "	<div class=\"row\">
  					<div class=\"column\">
  			";
  		waypointlist($link,$row);
	    echo "
    		</div>
  			<div class=\"column\">
	  	";
		taskinfo($row);

		echo "
			</div>
		</div>
		";
	}
	elseif ( strpos($file, 'map') )
	{
	    echo "	<div class=\"row\">
  					<div class=\"column\">
  			";
  		if ( isset($_REQUEST['regPk']) )
  		{
  			waypointinfo($link,$_REQUEST['regPk']);
  		}
	    echo "
    		</div>
  			<div class=\"column\">
	  	";
		//taskinfo($row);

		echo "
			</div>
		</div>
		";
	}
	echo "	</div>
    </header>
	";
}

function hccompinfo($row)
{
    $comDateFrom = substr(isset($row['comDateFrom']) ? $row['comDateFrom'] : '',0,10);
	$comDateTo = substr(isset($row['comDateTo']) ? $row['comDateTo'] : '',0,10);
	$comDirector = isset($row['comMeetDirName']) ? $row['comMeetDirName'] : '';
	$comLocation = isset($row['comLocation']) ? $row['comLocation'] : '';
	
    echo "<h3>Comp Details</h3>";
    $detarr = array(
    	array("<b>From:</b> <i>$comDateFrom</i>", "<b>To:</b> <i>$comDateTo</i>"),
        array("<hr>", "<hr>"),
        array("<b>Location:</b> ", "<i>$comLocation</i>"),
        array ("<b>Meet Director:</b> ", "<i>$comDirector</i>")
    );
    echo ftable($detarr, 'class=compinfo', '', array('', ''));
}

function hcscoreinfo($link,$row)
{
	$comOverall = isset($row['comOverallScore']) ? $row['comOverallScore'] : '';
	$comOverallParam = isset($row['comOverallParam']) ? $row['comOverallParam'] : ''; # Discard Parameter, Ex. 75 = 75% eq normal FTV 0.25
	$comType = isset($row['comType']) ? $row['comType'] : '';
	$forNomGoal = isset($row['forNomGoal']) ? $row['forNomGoal'] : '';
	$forMinDistance = isset($row['forMinDistance']) ? $row['forMinDistance'] : '';
	$forNomDistance = isset($row['forNomDistance']) ? $row['forNomDistance'] : '';
	$forNomTime = isset($row['forNomTime']) ? $row['forNomTime'] : '';
	$comFormula = ( isset($row['forClass']) ? $row['forClass'] : '' ) . ' ' . ( isset($row['forVersion']) ? $row['forVersion'] : '' );
	$comOverall = isset($row['comOverallScore']) ? $row['comOverallScore'] : '';  # Type of scoring discards: FTV, ...
	
	if ($comOverall == 'all')
	{
		$overstr = "All rounds";
	}
	elseif ($comOverall == 'round')
	{
		$overstr = "$comOverallParam rounds";
	}
	elseif ($comOverall == 'round-perc')
	{
		$comOverallParam = round($tasTotal * $comOverallParam / 100, 0);
		$overstr = "$comOverallParam rounds";
	}
	elseif ($comOverall == 'ftv')
	{
		$comPk = $row['comPk'];
		if ( strstr($comFormula, 'pwc') ) # calculates FTV parameters based on winner score (PWC)
		{
			$sql = "SELECT DISTINCT T.tasPk, (SELECT MAX(TR.tarScore) FROM tblTaskResult TR WHERE TR.tasPk=T.tasPk) AS maxScore FROM tblTask T, tblTaskResult TR WHERE T.comPk = $comPk";
			$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task validity query failed: ' . mysqli_connect_error());
			$totalvalidity = 0;
			while ( $rows = mysqli_fetch_assoc($result) )
			{
				$totalvalidity += $rows{'maxScore'};
			}
			$totalvalidity = round($totalvalidity * $comOverallParam / 100, 0); # gives total amount of available points
			$overstr = "FTV $comOverallParam% ($totalvalidity pts)";
			$comOverallParam = $totalvalidity;
		}
		else # calculates FTV parameters based on task validity (FAI)
		{
			$sql = "select sum(tasQuality) as totValidity from tblTask where comPk=$comPk";
			$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task validity query failed: ' . mysqli_connect_error());
			$totalvalidity = round(mysqli_result($result, 0, 0) * $comOverallParam * 10,0);
			$overstr = "FTV $comOverallParam% ($totalvalidity pts)";
		}
	}

	$scarr = [];
	$scarr[] = array("<b>Type:</b> ", "<i>$comType ($comFormula)</i>");
	$scarr[] = array("<b>Scoring:</b> ","<i>$overstr</i>");
	$scarr[] = array("<b>Min. Distance:</b>", "<i>$forMinDistance kms</i>");
	$scarr[] = array("<b>Nom. Distance:</b>", "<i>$forNomDistance kms</i>");
	$scarr[] = array("<b>Nom. Time:</b>", "<i>$forNomTime mins</i>");
	$scarr[] = array("<b>Nom. Goal %:</b>", "<i>$forNomGoal%</i>");
	echo "<h3>Scoring Parameters</h3>";
	echo ftable($scarr, 'class=scoreinfo', '', array('', ''));
}

function waypointlist($link,$row)
{
	# Waypoint Info
	$goalalt = 0;
	$tasPk = $row['tasPk'];
	$winfo = [];
	$winfo[] = array(fb("#"), fb("ID"), fb("Type"), fb("Radius"), fb("Distance"), fb("Description"));
	$waypoints = get_taskwaypoints($link,$tasPk);
	$i = 0;
	foreach ($waypoints as $row)
	{
		if ( $row['tawType'] == 'start' )
		{
			$winfo[] = array("", $row['rwpName'], "TakeOff", "", "", $row['rwpDescription']);
		}
		elseif ( $row['tawType'] == 'speed' )
		{
			$winfo[] = array($i, $row['rwpName'], "SS". " (" . $row['tawHow'] . ")", $row['tawRadius'] . "m", round($row['ssrCumulativeDist']/1000,1) . " Km", $row['rwpDescription']);
		}
		elseif ( $row['tawType'] == 'endspeed' )
		{
			$how = ( $row['tawHow'] == 'exit' ? " (" . $row['tawHow'] . ")" : "" );
			$winfo[] = array($i, $row['rwpName'], "ESS". $how, $row['tawRadius'] . "m", round($row['ssrCumulativeDist']/1000,1) . " Km", $row['rwpDescription']);
		}
		elseif ( $row['tawType'] == 'goal' )
		{
			$how = ( $row['tawShape'] == 'line' ? " (" . $row['tawShape'] . ")" : "" );
			$winfo[] = array($i, $row['rwpName'], "Goal" . $how, $row['tawRadius'] . "m", round($row['ssrCumulativeDist']/1000,1) . " Km", $row['rwpDescription']);
		}
		else
		{
			$how = ( $row['tawHow'] == 'exit' ? " (" . $row['tawHow'] . ")" : "" );
			$winfo[] = array($i, $row['rwpName'], $how, $row['tawRadius'] . " m", round($row['ssrCumulativeDist']/1000,1) . " Km", $row['rwpDescription']);
		}
		
		$i++;
		
		if ($row['tawType'] == 'goal')
		{
			$goalalt = $row['rwpAltitude'];
		}
	}
	echo "<h3>Waypoints</h3>";
	echo ftable($winfo,'class=tasktable', '', '');
}

function taskinfo($row)
{
	# Task Info
	
	$comName = $row['comName'];
	$comClass = $row['comClass'];
	$comPk = $row['comPk'];
	$tasPk = $row['tasPk'];
	$comTOffset = $row['comTimeOffset'] * 3600;
	$tasName = $row['tasName'];
	$title = 'AirScore - '.(isset($row['comName']) ? $row['comName'] : '').' '.$tasName;
	$tasDate = $row['tasDate'];
	$tasTaskType = ($row['tasTaskType'] = 'race' ? 'Race to Goal' : $row['tasTaskType']);
	$tasStartTime = substr($row['tasStartTime'],11);
	$tasFinishTime = substr($row['tasFinishTime'],11);
	$tasDistance = round($row['tasDistance']/1000,2);
	$tasShortest = round($row['tasShortRouteDistance']/1000,2);
	$tasQuality = round($row['tasQuality'],3);
	$tasComment = $row['tasComment'];
	$tasDistQuality = round($row['tasDistQuality'],2);
	$tasTimeQuality = round($row['tasTimeQuality'],2);
	$tasLaunchQuality = round($row['tasLaunchQuality'],2);
	$tasArrival = $row['tasArrival'];
	$tasHeightBonus = $row['tasHeightBonus'];
	$tasStoppedTime = substr($row['tasStoppedTime'],11);
	$ssDist = $row['tasSSDistance'];

	if ($row['tasDeparture'] == 'leadout')
	{
		$depcol = 'Ldo';
	}
	elseif ($row['tasDeparture'] == 'kmbonus')
	{
		$depcol = 'Lkm';
	}
	elseif ($row['tasDeparture'] == 'on')
	{
		$depcol = 'Dpt';
	}
	else
	{
		$depcol = 'off';
	}	

	$tinfo = [];
	$tinfo[] = array( fb("Task Type:"), $tasTaskType, "", "", fb("Class:"), classselector($comPk,$tasPk,$comClass) );
	if ($tasStoppedTime == "")
	{
		$tinfo[] = array( fb("Date:"), $tasDate, fb("Start:"), $tasStartTime, fb("End:"), $tasFinishTime );
	}
	else
	{
		$tinfo[] = array( fb("Date:"), $tasDate, fb("Start:"), $tasStartTime, fb("Stopped:"), $tasStoppedTime );
	}
	$tinfo[] = array( fb("Quality:"), number_format($tasQuality,3), fb("WP Dist:"), "$tasDistance km", fb("Task Dist:"), "$tasShortest km" );
	$tinfo[] = array( fb("DistQ:"), number_format($tasDistQuality,3), fb("TimeQ:"), number_format($tasTimeQuality,3), fb("LaunchQ:"), number_format($tasLaunchQuality,3) );
	echo "	<h3>Task Details</h3>";
	echo ftable($tinfo, 'class=taskinfo', '', '');
	echo "	<hr>
			<h3>Download Tracks</h3>";
	echo "	<form enctype=\"multipart/form-data\" action=\"download_task_tracks.php?tasPk=$tasPk&comPk=$comPk\" method=\"post\">";
	echo "	<input type=\"submit\" name=\"foo\" value=\"IGC Files (zip)\"></form>";
}

function waypointinfo($link,$regPk)
{
	# Waypoint Info
	$winfo = [];
	$sql = "SELECT COUNT(rwpPk) AS rwpNum, MAX(rwpLatDecimal) AS maxLat, MIN(rwpLatDecimal) AS minLat, MAX(rwpLongDecimal) AS maxLon, MIN(rwpLongDecimal) AS minLon, (select count(rwpName) FROM tblRegionWaypoint WHERE rwpName like 'A%' and regPk=6) as ANum, (select count(rwpName) FROM tblRegionWaypoint WHERE rwpName like 'D%' and regPk=6) as DNum FROM tblRegionWaypoint WHERE regPk=$regPk";
	$result = mysqli_query($link, $sql);
	$row = mysqli_fetch_array($result, MYSQLI_BOTH);
	if ( $row )
	{
		$numwpt = $row['rwpNum'];
		$totlat = $row['maxLat'] - $row['minLat'];
		$totlon = $row['maxLon'] - $row['minLon'];
		$numtoff = $row['DNum'];
		$numlan = $row['ANum'];
		$winfo[] = array( 'Number of points: ', $numwpt );
		$winfo[] = array( 'Number of take-offs: ', $numtoff );
		$winfo[] = array( 'Number of landings: ', $numlan );
	}

	echo "<h3>Info</h3>";
	echo ftable($winfo,'class=wpinfo', '', '');
}

function tpcontent($title='AirScore - Online Scoring Tool', $page='')
{
	echo "
	<!-- Main Content -->
	<section class=\"main-content\" id=\"main-content\">
		<div class=\"container\">
			<h2 class=\"text-center text-uppercase text-secondary mb-0\">$page</h2>
			<hr class=\"star-dark mb-5\">
	";
}

function tpfooter($file)
{
	echo "
		</div>
    </section>

    <!-- Footer -->
    <footer class=\"footer text-center\">
      <div class=\"container\">
        <div class=\"row\">
          <div class=\"col-md-4 mb-5 mb-lg-0\">
            <h4 class=\"text-uppercase mb-4\">About Us</h4>
            <p class=\"lead mb-0\"><a href=\"http://www.legapilotiparapendio.it/\">Lega Piloti Parapendio</a>
              <br><a href=\"mailto:info@legapilotiparapendio.it/\">contact us</a></p>
          </div>
          <div class=\"col-md-4 mb-5 mb-lg-0\">
            <h4 class=\"text-uppercase mb-4\">Around the Web</h4>
            <ul class=\"list-inline mb-0\">
              <li class=\"list-inline-item\">
                <a class=\"btn btn-outline-light btn-social text-center rounded-circle\" href=\"https://www.facebook.com/LegaPilotiParapendio/\">
                  <i class=\"fa fa-fw fa-facebook\"></i>
                </a>
              </li>
              <li class=\"list-inline-item\">
                <a class=\"btn btn-outline-light btn-social text-center rounded-circle\" href=\"http://www.legapilotiparapendio.it/?format=feed&type=rss\">
                  <i class=\"fa fa-fw fas fa-rss\"></i>
                </a>
              </li>
              <li class=\"list-inline-item\">
                <a class=\"btn btn-outline-light btn-social text-center rounded-circle\" href=\"http://twitter.com/LPPara/\">
                  <i class=\"fa fa-fw fa-twitter\"></i>
                </a>
              </li>
            </ul>
          </div>
          <div class=\"col-md-4\">
            <h4 class=\"text-uppercase mb-4\">About AirScore</h4>
            <p class=\"lead mb-0\">AirScore is an Online Scoring Application created by
              <a href=\"https://github.com/geoffwong/airscore\">Geoff Wong</a>.</p>
          </div>
        </div>
      </div>
    </footer>

    <div class=\"copyright py-4 text-center text-white\">
      <div class=\"container\">
        <small>Copyright &copy; Lega Piloti Parapendio 2018</small>
      </div>
    </div>

    <!-- Scroll to Top Button (Only visible on small and extra-small screen sizes) -->
    <div class=\"scroll-to-top d-lg-none position-fixed \">
      <a class=\"js-scroll-trigger d-block text-center text-white rounded\" href=\"#page-top\">
        <i class=\"fa fa-chevron-up\"></i>
      </a>
    </div>
    
    <!-- Bootstrap core JavaScript -->
    <script src=\"vendor/jquery/jquery.min.js\"></script>
    <script src=\"vendor/bootstrap/js/bootstrap.bundle.min.js\"></script>

    <!-- Plugin JavaScript -->
    <script src=\"vendor/jquery-easing/jquery.easing.min.js\"></script>
    <script src=\"vendor/magnific-popup/jquery.magnific-popup.min.js\"></script>

    <!-- Contact Form JavaScript -->
    <script src=\"js/jqBootstrapValidation.js\"></script>
    <script src=\"js/contact_me.js\"></script>

    <!-- Custom scripts for this template -->
    <script src=\"js/freelancer.min.js\"></script>
    
  	</body>
	</html>
	";
}

function classselector($comPk,$tasPk,$comClass)
{
	if ($comClass == "HG")
	{
		$classopts = array ( 'open' => '', 'floater' => '&class=0', 'kingpost' => '&class=1', 
			'hg-open' => '&class=2', 'rigid' => '&class=3', 'women' => '&class=4', 'masters' => '&class=5', 'teams' => '&class=6' );
	}
	else
	{
		$classopts = array ( 'open' => '', 'fun' => '&class=0', 'sports' => '&class=1', 
			'serial' => '&class=2', 'women' => '&class=4', 'masters' => '&class=5', 'teams' => '&class=6' );
	}
	$cind = '';
	if (reqexists('class'))
	{
		$cval = reqival('class');
		if ($cval != '')
		{
			$cind = "&class=$cval";
		}
	}
	$copts = [];
	foreach ($classopts as $text => $url)
	{
		if ($text == 'teams')
		{
			# Hack for now
			$copts[$text] = "team_task_result.php?comPk=$comPk&tasPk=$tasPk$url";
		}
		else
		{
			$copts[$text] = "task_result.php?comPk=$comPk&tasPk=$tasPk$url";
		}
	}

	$classfilter = fselect('class', "task_result.php?comPk=$comPk&tasPk=$tasPk$cind", $copts, ' onchange="document.location.href=this.value"');
	return $classfilter;
}

function seasoninfo($row)
{
	$sinfo = [];
	if ( $row )
	{
		$comNum = $row['comNum'];
		$pastCom = $row['pastCom'];
		$openCom = $row['openCom'];
		$nextCom = $row['nextCom'];
		$sinfo[] = array( 'Competitions in the season: ', $comNum );
		$sinfo[] = array( 'Competitions already scored: ', $pastCom );
		$sinfo[] = array( 'Competitions open now: ', $openCom );
		$sinfo[] = array( 'Next competitions in the season: ', $nextCom );
	}
	echo "<h3>Season Info</h3>";
	echo ftable($sinfo,'class=seasoninfo', '', '');		
}

function hcheadbar($title,$active,$titler)
{
	echo "
	  <div id=\"header\">
		<div id=\"menu\">
		  <ul>\n
	";
		$clarr = array     
		(
			'', '', '', '', '', '', '', ''
		);
		$clarr[$active] = ' class="active"';
		$comPk=reqival('comPk');
		echo "<li><a href=\"index.php?comPk=$comPk\" title=\"About\"" . $clarr[0]. ">About</a></li>\n";
		if (!$comPk)
		{
			echo "<li><a href=\"ladder.php\" title=\"Ladders\"" . $clarr[1] . ">Ladders</a></li>\n";
			$comPk = 1;
		}
		echo "<li><a href=\"submit_track.php?comPk=$comPk\" title=\"Submit\"" . $clarr[1] . ">Submit</a></li>\n";
		echo "<li><a href=\"comp_result.php?comPk=$comPk\" title=\"Results\"" . $clarr[2] . ">Results</a></li>\n";
		$regPk=reqival('regPk');
		if ($regPk > 0)
		{
		echo "<li><a href=\"http://highcloud.net/xc/waypoint_map.php?regPk=$regPk\" title=\"Waypoints\"" . $clarr[3] . ">Waypoints</a></li>\n";
		}
		//echo "<li><a href=\"comp_result.php?comPk=$comPk&tmsc=1\" title=\"Teams\"" . $clarr[4] . ">Teams</a></li>\n";
		//echo "<li><a href=\"track.php\" title=\"submit tracks\"" . $clarr[4] . ">Tracks</a></li>";
	echo "</ul>\n
		  <div id=\"title\">
			<h1>$title</h1>
		  </div>
		  <div id=\"titler\">
			<h1>$titler</h1>
		  </div>
		</div>
	  </div>";
}

function hcimage($link,$comPk)
{
    $image = "images/pilots.jpg";
    if (0+$comPk > 0)
    {
        $sql = "select comClass from tblCompetition where comPk=$comPk";
        $result = mysqli_query($link, $sql);
        if ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
        {
            $comClass = $row['comClass'];
            if ($comClass != 'PG')
            {
                $image = "images/pilots_$comClass.jpg";
            }
        }
    }
    echo "<div id=\"image\"><img src=\"$image\" alt=\"Pilots Flying\"/></div>";
}

function hcsidebar($link)
{
	echo "
		<div id=\"image\"><img src=\"images/pilots.jpg\" alt=\"Pilots Flying\"/></div>
		<div id=\"sideBar\">
		<h1><span>Longest 10</span></h1>
		<div id=\"comments\"><ol>";
	$count = 1;
	$sql = "SELECT T.*, P.* FROM tblTrack T, tblPilot P, tblComTaskTrack CTT where T.pilPk=P.pilPk and CTT.traPk=T.traPk order by T.traLength desc limit 10";
	$result = mysqli_query($link, $sql);
	while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
	{
		$id = $row['traPk'];
		$dist = round($row['traLength']/1000,2);
		$name = $row['pilFirstName'];
		echo "<span class=\"author\"><a href=\"tracklog_map.php?trackid=$id&comPk=5\"><li> $dist kms ($name)</a></span>\n";

		$count++;
	}
	echo "</ol>";
	echo "
		<img src=\"images/comment_bg.gif\" alt=\"comment bottom\"/>
		</div>
		<h1><span>Recent 10</span></h1><ol>";
	$count = 1;
	$sql = "SELECT T.*, P.* FROM tblTrack T, tblPilot P, tblComTaskTrack CTT where T.pilPk=P.pilPk and CTT.traPk=T.traPk order by T.traDate desc limit 10";
	$result = mysqli_query($link, $sql);
	while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
	{
		$id = $row['traPk'];
		$dist = round($row['traLength']/1000,2);
		$date = $row['traDate'];
		$name = $row['pilFirstName'];
		echo "<a href=\"tracklog_map.php?trackid=$id&comPk=5\"><li> $dist kms ($name)</a><br>\n";

		$count++;
	}

	echo "</ol>";
	echo "<img src=\"images/comment_bg.gif\" alt=\"comment bottom\"/>
		</div>\n";
}

function hcregion($link)
{
    echo "<h1><span>Tracks by Region</span></h1>\n";
    $sql = "select R.*, RW.* from tblCompetition C, tblTask T, tblRegion R, tblRegionWaypoint RW where T.comPk=C.comPk and T.regPk=R.regPk and C.comDateTo > date_sub(now(), interval 1 year) and R.regCentre=RW.rwpPk and R.regDescription not like '%test%' and R.regDescription not like '' group by R.regPk order by R.regDescription";
    $result = mysqli_query($link, $sql);
    $regions = [];
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $regPk=$row['regPk'];
        #$regions[] = "<a href=\"regional.php?${piln}regPk=$regPk\">" . $row['regDescription'] . "</a>";
        $regions[] = "<a href=\"regional.php?regPk=$regPk\">" . $row['regDescription'] . "</a>";
    }
    echo fnl($regions);
    //echo "<img src=\"images/comment_bg.gif\" alt=\"comment bottom\"/></div>\n";
}

function hcopencomps($link)
{
    echo "<h2 class=\"font-weight-light mb-0\">Open Competitions</span></h2>";
    // This is the one to use in Production
    // $sql = "select * from tblCompetition where comName not like '%test%' and comDateTo > date_sub(now(), interval 1 day) order by comDateTo";
    // This is the one we use to simulate
    $sql = "select * from tblCompetition where comDateTo > date_sub(now(), interval 1 day) order by comDateTo";
    $result = mysqli_query($link, $sql);
    $comps = [];
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        // FIX: if not finished & no tracks then submit_track page ..
        // FIX: if finished no tracks don't list!
        $cpk = $row['comPk'];
        $comps[] = "<span class=\"list\"><a href=\"comp_result.php?comPk=$cpk\">" . $row['comName'] . "</span></a>";
    }
    echo fnl($comps);
}

function hcclosedcomps($link, $like = '')
{
    echo "<h2 class=\"font-weight-light mb-0\">Closed Competitions</h2>";

    if ($like != '')
    {
        $arr = explode (" ", $like);
        $first = $arr[0];
        // This is the one to use in Production
    	// $sql = "select * from tblCompetition where comName not like '%test%' and comName like '%$first%' and comDateTo < date_sub(now(), interval 1 day) order by comDateTo desc limit 15";
    	// This is the one we use to simulate
        $sql = "select * from tblCompetition where comName like '%$first%' and comDateTo < date_sub(now(), interval 1 day) order by comDateTo desc limit 15";
    }
    else
    {
        // This is the one to use in Production
    	// $sql = "select * from tblCompetition where comName not like '%test%' and comDateTo < date_sub(now(), interval 1 day) order by comDateTo desc limit 15";
    	// This is the one we use to simulate
		$sql = "select * from tblCompetition where comDateTo < date_sub(now(), interval 1 day) order by comDateTo desc limit 15";
    }
    $result = mysqli_query($link, $sql);
    $comps = [];
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        // FIX: if not finished & no tracks then submit_track page ..
        // FIX: if finished no tracks don't list!
        $cpk = $row['comPk'];
        if ($row['comType'] == 'Route')
        {
            $comps[] = "<a href=\"compview.php?comPk=$cpk\">" . $row['comName'] . "</a>";
        }
        else
        {
            $comps[] = "<a href=\"comp_result.php?comPk=$cpk\">" . $row['comName'] . "</a>";
        }
    }
    echo fnl($comps);
}

function hcfooter()
{
    echo "<div id=\"footer\">
      <a href=\"http://openwebdesign.org\" title=\"designed by fullahead.org\">Open Web Design</a></div>
  </div>\n";
}

function hcmapjs()
{
    echo '<script src="http://maps.googleapis.com/maps/api/js?sensor=false&key=AIzaSyDz6hWZmvUXC6fOGP8teoO5brJKT2FB_F8"></script>';
    echo "\n";
    echo '<script src="js/elabelv3.js"></script>';
    echo "\n";
    echo '<script src="js/einsertv3.js"></script>';
    echo "\n";
}

function hcscripts($arr)
{
    foreach ($arr as $ele)
    {
        echo "<script src=\"$ele\"></script>\n";
    }
}

?>
