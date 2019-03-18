<?php
require 'authorisation.php';
require 'format.php';
require 'template.php';

function DECtoDMS($dec)
{

// Converts decimal longitude / latitude to DMS
// ( Degrees / minutes / seconds ) 

// This is the piece of code which may appear to 
// be inefficient, but to avoid issues with floating
// point math we extract the integer part and the float
// part by using a string function.

	$vars = explode(".",$dec);
    $deg = floatval($vars[0]);
    $tempma = "0.".$vars[1];

    $tempma = $tempma * 3600;
    $min = floatval(floor($tempma / 60));
    $sec = floatval($tempma - ($min*60));

    return array("deg"=>$deg,"min"=>$min,"sec"=>$sec);
}

function parse_latlong($str, $neg)
{
    $val = floatval($str);

    $ns = substr($str, -1,1);
    if ($ns == $neg)
    {
        $val = -$val;
    }
    // radians? $loc{'lat'} = $loc{'lat'} * $pi / 180;

    return $val;
}

function parse_gpsd_latlong($str, $neg)
{
    $fields = explode(" ", $str);
    $val = '';
    if ( isset($fields[1]) && isset($fields[2]) && isset($fields[3]) ) {
    	$val = floatval($fields[1]) + floatval($fields[2] + floatval($fields[3])/60) / 60;
    }
    

    $ns = $fields[0];
    if ($ns == $neg)
    {
        $val = -$val;
    }

    return $val;
}

function parse_oziwpts($regPk, $link, $lines)

# OziExplorer Waypoint File Version 1.0
# WGS 84
# Reserved 2
# Reserved 3
#    1,03CARS        , -28.293917, 152.413861,40427.5383565,0, 1, 3, 0, 65535,CARRS LOOKOUT                           , 0, 0, 0, 3117
#

{
    $count = 1;
    for ($i = 0; $i < count($lines); $i++)
    {
        $fields = explode(",", $lines[$i]);
        if (0 + $fields[0] < $count) 
            continue;

        $count++;

        // waypoint
        $name = addslashes($fields[1]);
        $lat = parse_latlong($fields[2], "S");
        $long = parse_latlong($fields[3], "W");
        $alt = floatval($fields[14]) / 3.281;
        $desc = rtrim(addslashes($fields[10]));
        $xcode = 0;
        
        # If waypoint is a Takeoff looks for XContest ID in Description
        if ( strtoupper(substr($name, 0, 1)) == 'D' )
        {	
        	if ( preg_match('/[0-9]{4}/', $desc, $results) )
        	{
        		$xcode = $results[0];
        	}
        	//echo "$name  $lat $long  $alt  $desc  XContest = $xcode<br />";
        	$sql = "insert into tblRegionWaypoint (regPk, rwpName, rwpLatDecimal, rwpLongDecimal, rwpAltitude, rwpDescription, xccToID) values ($regPk,'$name',$lat,$long,$alt,'$desc',$xcode)";
        }
		else
		{
			//echo "$name  $lat $long  $alt  $desc<br />";
			$sql = "insert into tblRegionWaypoint (regPk, rwpName, rwpLatDecimal, rwpLongDecimal, rwpAltitude, rwpDescription) values ($regPk,'$name',$lat,$long,$alt,'$desc')";
		}
		
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Insert RegionWaypoint failed: ' . mysqli_connect_error());
    }

    return $count;
}

function parse_compegps($regPk, $link, $lines)

# G  WGS 84
# U  1
# W  A01 A 43.2975000000∫N 21.9973333333∫E 27-MAR-62 00:00:00 210.000000 Nbanja
# w Waypoint,4,-1.0,0,0,1,5,7,0.0,0.0
	
{
	$param = [];
    for ($i = 0; $i < count($lines); $i++)
    {
        $fields = explode(" ", $lines[$i]);
        if ($fields[0] == "W")
        {
            // waypoint
            $name = addslashes($fields[2]);
            $lat = parse_latlong($fields[4], "S");
            $long = parse_latlong($fields[5], "W");
            $alt = floatval($fields[8]);
            $desc = rtrim(addslashes($fields[9]));
            
            # If waypoint is a Takeoff looks for XContest ID in Description
			if ( strtoupper(substr($name, 0, 1)) == 'D' )
			{	
				if ( preg_match('/[0-9]{4}/', $desc, $results) )
				{
					$xcode = $results[0];
				}
				//echo "$name  $lat $long  $alt  $desc  XContest = $xcode<br />";
				$sql = "insert into tblRegionWaypoint (regPk, rwpName, rwpLatDecimal, rwpLongDecimal, rwpAltitude, rwpDescription, xccToID) values ($regPk,'$name',$lat,$long,$alt,'$desc',$xcode)";
			}
			else
			{
				//echo "$name  $lat $long  $alt  $desc<br />";
				$sql = "insert into tblRegionWaypoint (regPk, rwpName, rwpLatDecimal, rwpLongDecimal, rwpAltitude, rwpDescription) values ($regPk,'$name',$lat,$long,$alt,'$desc')";
			}
			
            $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Insert RegionWaypoint failed: ' . mysqli_connect_error());
            $count++;
        }
        else if ($fields[0] == "G")
        {
            // geodesic
            if (!($fields[1] == "WGS" && $fields[2] == "84"))
            {
                // ignore for now?
            }
        }
        else if ($fields[0] == "w")
        {
            // ignore?
        }
    }

    return $count;
}

function parse_gpsdump($regPk, $link, $lines)

# $FormatGEO
# B01       N 46 06 46.10    E 012 35 13.99   514  Turnpoint 1

{
    $count = 1;
    //echo "region=$regPk<br>";
    for ($i = 0; $i < count($lines); $i++)
    {
        // waypoint
        $fields = $lines[$i];
        $name = addslashes(rtrim(substr($fields,0, 10)));
        $lat = parse_gpsd_latlong(substr($fields,10,13), "S");
        $long = parse_gpsd_latlong(substr($fields,27,14), "W");
        $alt = floatval(substr($fields,43,5));
        $desc = addslashes(rtrim(substr($fields,49)));
        $xcode = 0;
        
        # If waypoint is a Takeoff looks for XContest ID in Description
        if ( strtoupper(substr($name, 0, 1)) == 'D' )
        {	
        	if ( preg_match('/[0-9]{4}/', $desc, $results) )
        	{
        		$xcode = $results[0];
        	}
        	//echo "$name  $lat $long  $alt  $desc  XContest = $xcode<br />";
        	$sql = "insert into tblRegionWaypoint (regPk, rwpName, rwpLatDecimal, rwpLongDecimal, rwpAltitude, rwpDescription, xccToID) values ($regPk,'$name',$lat,$long,$alt,'$desc',$xcode)";
        }
		else
		{
			//echo "$name  $lat $long  $alt  $desc<br />";
			$sql = "insert into tblRegionWaypoint (regPk, rwpName, rwpLatDecimal, rwpLongDecimal, rwpAltitude, rwpDescription) values ($regPk,'$name',$lat,$long,$alt,'$desc')";
		}

        if ($lat != 0.0)
        {
            $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Insert RegionWaypoint failed: ' . mysqli_connect_error());
            $count++;
        }
    }

    return $count;
}

function parse_kml($regPk, $link, $xml)
{
    for ($n = 0; $n < count($xml->Document->Folder->Placemark); $n++)
    {
        $placemark = $xml->Document->Folder->Placemark[$n];
        $name = $placemark->name;
        $arr = explode(",",$placemark->Point->coordinates);
        $lat = $arr[1];
        $long = $arr[0];
        $alt = $arr[2];
        $desc = $placemark->description;
        
		# If waypoint is a Takeoff looks for XContest ID in Description
        if ( strtoupper(substr($name, 0, 1)) == 'D' )
        {	
        	if ( preg_match('/[0-9]{4}/', $desc, $results) )
        	{
        		$xcode = $results[0];
        	}
        	//echo "$name  $lat $long  $alt  $desc  XContest = $xcode<br />";
        	$sql = "insert into tblRegionWaypoint (regPk, rwpName, rwpLatDecimal, rwpLongDecimal, rwpAltitude, rwpDescription, xccToID) values ($regPk,'$name',$lat,$long,$alt,'$desc',$xcode)";
        }
		else
		{
			//echo "$name  $lat $long  $alt  $desc<br />";
			$sql = "insert into tblRegionWaypoint (regPk, rwpName, rwpLatDecimal, rwpLongDecimal, rwpAltitude, rwpDescription) values ($regPk,'$name',$lat,$long,$alt,'$desc')";
		}
		
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Insert RegionWaypoint failed: ' . mysqli_connect_error());
    }

    return $n;
}

function parse_waypoints($filen, $regPk, $link)
{
    $count = 0;
    $fh = fopen($filen, 'r');
    if (!$fh)
    {
        echo "Unable to read file<br>";
        return;
    }
    clearstatcache();
    $sz = filesize($filen);
    // echo "file=$filen filesize=$sz<br>";
    $data = fread($fh, $sz);
    fclose($fh);

    $lines = explode("\n", $data);
    if (substr($lines[0],0,10) == '$FormatGEO')
    {
        return parse_gpsdump($regPk, $link, array_slice($lines,1));
    }

    elseif (substr($lines[0],0,3) == "Ozi")
    {
        return parse_oziwpts($regPk, $link, $lines);
    }

    elseif (substr($lines[0],0,5) == "<?xml")
    {
        $xml = new SimpleXMLElement($data);
        return parse_kml($regPk, $link, $xml);
    }
    
    elseif (substr($lines[0],0,9) == "G  WGS 84")
    {
        return parse_compegps($regPk, $link, $lines);
    }

}

function delete_unused_waypoints($regPk, $link)
{
    $mess = '';
    $query = "select * from tblRegion where regPk=$regPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Region check failed: ' . mysqli_connect_error());
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    $file = $row['regWptFileName'];

    # Check if there is an active waypoint file for the Region
    if ( $file !== '' )
    {
		# Check if some waypoints are in use in old Competitions
		$query = "	SELECT 
						* 
					FROM 
						tblRegionWaypoint W   
						JOIN tblTaskWaypoint T ON T.rwpPk = W.rwpPk 
					WHERE W.rwpOld = 0 
						AND W.regPk = $regPk 
					LIMIT 
						1";
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Used wpt check check failed: ' . mysqli_connect_error());
		if (mysqli_num_rows($result) > 0)
		{
			# Set used waypoint value to 1 to be not deleted
			$query = "	UPDATE 
							tblRegionWaypoint 
						SET 
							rwpOld = 1 
						WHERE 
							regPk = $regPk 
							AND EXISTS (
								SELECT 
									* 
								FROM 
									tblTaskWaypoint 
								WHERE 
									tblTaskWaypoint.rwpPk = tblRegionWaypoint.rwpPk
							)";
			$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' rwpOld value update failed: ' . mysqli_connect_error());

			$mess .= "Some Waypoints in $file are in use in a Competition and will not be deleted. <br />\n";
		}
		else
		{
			$mess .= "No waypoint is used in a task so we can safely delete them. <br />\n";
		}
		
		#delete unused waypoint
		$query = "delete from tblRegionWaypoint where rwpOld = 0 AND regPk = $regPk";
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Waipoint delete failed: ' . mysqli_connect_error());
		#delete Waypoint File Name from Region
		$query = "	UPDATE 
						tblRegion 
					SET 
						regWptFileName = '' 
					WHERE 
						regPk = $regPk";
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Waipoint name delete failed: ' . mysqli_connect_error());

		$mess .= "Waypoint file $file deleted. \n";

	}
	else
	{
		$mess .= "There aren't old waypoints to delete. <br />\n";
	}
	
	return $mess;
}

function accept_waypoints($regPk, $link, $filename)
{
    $name = 'waypoints';
    $mess = ''; 

     // add the region ..
//     $query = "insert into tblRegion (regDescription) values ('$region')";
//     $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
// 	$regPk = mysqli_insert_id($link);

    // Copy the upload so I can use it later ..
    if ($_FILES['waypoints']['tmp_name'] != '')
    {
        $copyname = tempnam(FILEDIR, $name . "_");
        copy($_FILES['waypoints']['tmp_name'], $copyname);
        chmod($copyname, 0644);

        // Process the file
        if (!parse_waypoints($copyname, $regPk, $link))
        {
            $mess .= "<b>Failed to upload your waypoints correctly.</b><br>\n";
            $mess .= "Contact the site maintainer if this was a valid waypoint file.<br>\n";
        }
		else
		{
		    $lastid = mysqli_insert_id($link);
			$query = "UPDATE tblRegion SET regCentre=$lastid, regWptFileName='$filename' WHERE regPk=$regPk";
			$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Filename and Centre update failed: ' . mysqli_connect_error());
			$mess .= "Waypoint file $filename correctly added\n";
		}
    }

    return $mess;
}

//
// Main Code Begins HERE //
//

auth('system');
$link = db_connect();
$usePk = auth('system');
$comPk = reqival('comPk');
$regPk = reqival('regPk');
$file = __FILE__;
$message = '';

if ( reqexists('regdel') )
{
    // implement a nice 'confirm'
    $regPk = reqival('regdel');
    $query = "select * from tblRegion where regPk=$regPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Region check failed: ' . mysqli_connect_error());
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    $region = $row['regDescription'];
    $query = "select * from tblTaskWaypoint T, tblRegionWaypoint W, tblRegion R where T.rwpPk=W.rwpPk and R.regPk=W.regPk and R.regPk=$regPk limit 1";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Delete check failed: ' . mysqli_connect_error());
    if (mysqli_num_rows($result) > 0)
    {
        $message .= "Unable to delete $region ($regPk) as it is in use in a Competition.\n";
    }
	else
	{
		$query = "delete from tblRegionWaypoint where regPk=$regPk";
		mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Waipoint delete failed: ' . mysqli_connect_error());
		$query = "delete from tblRegionXCSites where regPk=$regPk";
		mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' RegionXCSites delete failed: ' . mysqli_connect_error());
		$query = "delete from tblRegion where regPk=$regPk";
		mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Region delete failed: ' . mysqli_connect_error());
		
		redirect("area_admin.php?del=$region");
	}    
}

if ( reqexists('openairadd') )
{
    $upfile = $_FILES['openair']['tmp_name'];
    $filename = basename($_FILES['openair']['name']);
    $out = '';
    $retv = 0;
    exec(BINDIR . "airspace_openair.pl $upfile", $out, $retv);

    if ($retv)
    {
        $message .= "Failed to upload your airspace properly.<br />\n";
        foreach ($out as $txt)
        {
            echo "$txt<br>\n";
        }
    }
    else
	{ 
		$message = "Airspace file correctly uploaded. <br />";
	}
}

if ( reqexists('wptadd') )
{
    //echo "richiesta wptadd <br />";
    if (!$_FILES)
    {
        global $argv;
        $_FILES = [];
        $_FILES['waypoints'] = [];
        $_FILES['waypoints']['tmp_name'] = $argv[2];
    }
	//echo "temp_name: ".$_FILES['waypoints']['tmp_name']."<br />";
	$filename = basename($_FILES['waypoints']['name']);
	//echo "filename: $filename <br />";
	$message .= delete_unused_waypoints($regPk, $link);
    $message .= accept_waypoints($regPk, $link, $filename);
}

if (reqexists('wptdownload'))
{
    // implement a nice 'confirm'
    $id=reqival('download');
    redirect("download_waypoints.php?download=$id");
}

if (reqexists('wptdelete'))
{
    // implement a nice 'confirm'
    $id = reqival('wptdelete');
    $message .= delete_unused_waypoints($id, $link);
}

if (reqexists('sitedelete'))
{
    // implement a nice 'confirm'
    $siteid = reqival('sitedelete');
	$query = "DELETE FROM tblRegionXCSites WHERE regPk=$regPk AND xccSiteID=$siteid";
	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Site delete failed: ' . mysqli_connect_error());
	$message .= "Xcontest site unlinked\n";
}

if (reqexists('siteadd'))
{
    // implement a nice 'confirm'
    $siteid = reqival('siteadd');
    //echo "siteid: $siteid";
	$query = "INSERT INTO tblRegionXCSites (regPk, xccSiteID) VALUES ($regPk, $siteid)";
	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Site insert failed: ' . mysqli_connect_error());
	$message .= "Xcontest site linked\n";
}

if (reqexists('launchdelete'))
{
    // implement a nice 'confirm'
    $rwpPk = reqival('launchdelete');
	$query = "UPDATE tblRegionWaypoint SET xccToID=0 WHERE rwpPk=$rwpPk";
	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' launch delete failed: ' . mysqli_connect_error());
	$message .= "Xcontest launch unlinked\n";
}

if (reqexists('launchadd'))
{
    // implement a nice 'confirm'
    $xcid = reqival('launchadd');
    $rwpPk = reqival('rwpPk');
    //echo "launchid: $rwpPk | xcid: $xcid";
	$query = "UPDATE tblRegionWaypoint SET xccToID=$xcid WHERE rwpPk=$rwpPk";
	//echo $query . "<br />";
	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' launch insert failed: ' . mysqli_connect_error());
	$message .= "Xcontest site linked\n";
}

# Create Tables
$wtable = [];
$xtable = [];
$ttable = [];
$ftable = [];
$dtable = [];

$wpt = 0;
$openair = 0;

# Get Region Infos
$sql = "	SELECT 
				R.*, 
				COUNT(RW.rwpPk) AS wptNum, 
				MAX(RW.rwpLatDecimal) AS maxLat, 
				MIN(RW.rwpLatDecimal) AS minLat, 
				MAX(RW.rwpLongDecimal) AS maxLon, 
				MIN(RW.rwpLongDecimal) AS minLon, 
				(
					SUM(RW.rwpLatDecimal) / COUNT(RW.rwpPk)
				) AS centreLat, 
				(
					SUM(RW.rwpLongDecimal) / COUNT(RW.rwpPk)
				) AS centreLon 
			FROM 
				tblRegion R 
				LEFT JOIN tblRegionWaypoint RW ON RW.regPk = R.regPk 
				AND rwpOld = 0 
			WHERE 
				R.regPk = $regPk";
				
$result = mysqli_query($link, $sql);

if ( mysqli_num_rows($result) == 0 )
{
	$message .= 'We didn\'t find any Region with that ID.\n';
}
else
{
	$row = mysqli_fetch_array($result, MYSQLI_BOTH);
	$regname = str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['regDescription']))));

	# Get Messages
	if ( reqival('created') == 1)
	{
		$message .= "Region $regname created.\n";
	}
	
	# Region Infos about Waypoints and Airspaces
    if ( $row['regWptFileName'] !== '' )
    {
		$wpt = 1;
		$latdms = DECtoDMS($row['centreLat']);
		$londms = DECtoDMS($row['centreLon']);
		$lat = ($latdms['deg'] >= 0 ? 'N' : 'S') . ' ' . abs($latdms['deg']) . ' ' . $latdms['min'] . ' ' . round($latdms['sec'], 2);
		$lon = ($londms['deg'] >= 0 ? 'E' : 'W') . ' ' . abs($londms['deg']) . ' ' . $londms['min'] . ' ' . round($londms['sec'], 2);
		$wtable[] = array(fb('Area Centre GeoLoc:'), $lat . ' | ' . $lon, '', '');
		$wtable[] = array(fb('Waypoint File:'), "<a href=\"waypoint_map.php?regPk=$regPk\">" . str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['regWptFileName'])))) . "</a>", fbut('submit', 'wptdownload', $regPk, 'Download'), fbut('submit', 'wptdelete', $regPk, 'Delete Waypoints') );
		$wtable[] = array(fb('Waypoint Number:'), $row['wptNum'], '', '');    
    }
    else
    {
   		$wtable[] = array(fb('Area Centre GeoLoc:'), 'Not available', '', '');
		$wtable[] = array(fb('Waypoint File:'), "<span style='color:red'>File not yet uploaded</span>", '', '' );
		$wtable[] = array(fb('Waypoint Number:'), 'Not available', '', '');    

    }
    if ( $row['regOpenAirFile'] !== '' )
    {
		$openair = 1;
		$wtable[] = array(fb('OpenAir File:'), str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['regOpenAirFile'])))), fbut('submit', 'openairdownload', $regPk, 'Download'), fbut('submit', 'openairdelete', $regPk, 'Delete OpenAir') );
    }
    else
    {
   		$wtable[] = array(fb('OpenAir File:'), "<span style='color:red'>File not yet uploaded</span>", '', '' );
    }    

	# Region Infos about XContest Sites
	$sql = "	SELECT 
					DISTINCT XC.xccSiteID, 
					XC.xccSiteName, 
					XC.xccCountryName 
				FROM 
					tblRegionXCSites RX 
					LEFT JOIN tblXContestCodes XC on RX.xccSiteID = XC.xccSiteID 
				WHERE 
					RX.regPk = $regPk";
				
	$result = mysqli_query($link, $sql);

	$count = mysqli_num_rows($result);
	$xtable[] = array(fb('XContest Sites:'), '', '');

	if ( $count !== 0 )
	{
		$xtable[] = array($count . ' XContest ' . ($count == 1 ? 'site ' : 'sites ') . 'associated to this Region','','');
		while($row = mysqli_fetch_array($result, MYSQLI_BOTH))
		{
			$siteid = $row['xccSiteID'];
			$sitename = str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['xccSiteName']))));
			$country = str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['xccCountryName']))));
			$xtable[] = array($country, $sitename, fbut('submit', 'sitedelete', $siteid, 'Unlink Site'));
		}
	}
	else
	{
		$xtable[] = array("<span style='color:red'>No XContest sites yet associated</span>",'', '');
	}

	$country = reqsval('country') !== '' ? reqsval('country') : 'IT';
	$selsite = reqival('xcsite') !== 0 ? reqival('xcsite') : 0;
	//echo "Country: $country - selsite: $selsite <br />";
	$button = $selsite !== 0 ? fbut('submit', 'siteadd', $selsite, 'Link Site') : "<button type=\"submit\" name=\"siteadd\" value=\"\" disabled=disabled>Link Site</button>";
	$xtable[] = array( get_countries($link, $country),get_sites($link, $regPk, $country, $selsite), $button);
	//echo json_encode(get_countries($link,'ITALY'));

	# Region Infos about XContest Takeoffs
	# I need to have a form each takeoff, to set rwpPk parameter
	$sql = "	SELECT 
					RW.*, 
					XC.* 
				FROM 
					tblRegionWaypoint RW 
					LEFT JOIN tblXContestCodes XC ON RW.xccToID = XC.xccToID 
				WHERE 
					RW.rwpName LIKE 'D%' 
					AND RW.regPk = $regPk 
					AND RW.rwpOld = 0 
				ORDER BY 
					RW.rwpName ASC";
				
	$result = mysqli_query($link, $sql);

	$count = mysqli_num_rows($result);
	$ttable[] = array(fb('Region Takeoff:'), fb('XContest Takeoff:'), '');

	if ( $count !== 0 )
	{
		while($row = mysqli_fetch_array($result, MYSQLI_BOTH))
		{
			$launchname = str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['rwpName']))));
			$launchdesc = str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['rwpDescription']))));
			$id = $row['rwpPk'];
			if ( $row['xccToID'] > 0 )
			{
				$xcdesc = str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['xccToName']))));
				$button = fbut('submit', 'launchdelete', $id, 'Unlink takeoff');
			}
			else
			{
				$selto = ( (reqival('rwpPk') == $id) AND (reqival('xclaunch') !== 0) ) ? reqival('xclaunch') : 0;
				//echo "selto: $selto <br />";
				$xcdesc = get_launches($link, $regPk, $id, $selto);
				$button = fbut('submit', 'launchadd', $selto, 'Link takeoff');
			}
		
			//$country = str_replace('\' ', '\'', ucwords(str_replace('\'', '\' ', strtolower($row['xccCountryName']))));
			//$rtable[] = array($count . ' XContest ' . ($count == 1 ? 'site ' : 'sites ') . 'associated to this Region','','','' );
			$ttable[] = array($launchname . ' | ' . $launchdesc, "<form enctype=\"multipart/form-data\" action=\"region_admin.php?regPk=$regPk&rwpPk=$id\" name=\"rwpPk$id\" id=\"rwpPk$id\" method=\"post\">" . $xcdesc, $button . "</form>");
		}
	}
	else
	{
		$ttable[] = array("<span style='color:red'>No takeoffs (Dxx waypoints) in WPT File</span>",'', '');
	}

	# Upload Waypoint and Airspaces files
	$ftable[] = array("Waypoints File: ", "<input type=\"file\" name=\"waypoints\">", fis('wptadd', 'Add Waypoints File', 'width10'), $wpt == 1 ? "<span style='color:red'>Will delete old waypoints</span>" : '');
	$ftable[] = array("OpenAir File: ", "<input type=\"file\" name=\"openair\">", fis('openairadd', 'Add OpenAir File', 'width10'), $openair == 1 ? "<span style='color:red'>Will delete old airspaces</span>" : '');
	
	# Delete Region
	$dtable[] = array(fbut('submit', 'regdel', $regPk, 'Delete Region'), "<span style='color:red'>Will delete Region, Waypoints and Openair Files</span>");

}

// $country = reqsval('country') !== '' ? reqsval('country') : 'IT';
// $rtable[] = array( get_countries($link, $country),get_sites($link, $country), fbut('submit', 'siteadd', $id, 'Link Site'), '' );
//echo json_encode(get_countries($link,'ITALY'));

//initializing template header
tpadmin($link,$file);

echo "<h4> Region: $regname </h4>";
if ( $message !== '')
{
	echo "<h4> <span style='color:red'>$message</span> </h4>";
}
echo "<hr />";
echo "<form enctype=\"multipart/form-data\" action=\"region_admin.php?regPk=$regPk\" name=\"region1\" id=\"region1\" method=\"post\">";
echo ftable($wtable,'class=regionwtable', '', '');
echo "<br />";
echo "<hr />";
echo ftable($xtable,'class=regionxtable', '', '');
echo "</form>";
echo "<br />";
echo "<hr />";
echo ftable($ttable,'class=regionttable', '', '');
echo "<br />";
echo "<hr />";
echo "<form enctype=\"multipart/form-data\" action=\"region_admin.php?regPk=$regPk\" name=\"region2\" id=\"region2\" method=\"post\">";
echo ftable($ftable,'class=regionftable', '', '');
echo "<hr />";
echo ftable($dtable,'class=regiondtable', '', '');
echo "</form>";

tpfooter($file);

?>


