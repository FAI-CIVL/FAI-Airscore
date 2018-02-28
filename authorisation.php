<?php
require_once('defines.php');

// function redirect($loc)
// {
//     echo "<script language=\"JavaScript\" type=\"text/javascript\">";
//     echo "<!--\n";
//     echo "window.location.href=\"$loc\";";
//     echo "//-->\n";
//     echo "</script>\n";
// }

// Function to substitute deprecated mysql_result, sure have to look for better solution
function mysqli_result($res,$row=0,$col=0){ 
    $numrows = mysqli_num_rows($res); 
    if ($numrows && $row <= ($numrows-1) && $row >=0){
        mysqli_data_seek($res,$row);
        $resrow = (is_numeric($col)) ? mysqli_fetch_row($res) : mysqli_fetch_assoc($res);
        if (isset($resrow[$col])){
            return $resrow[$col];
        }
    }
    return false;
}
//

function redirect($url, $permanent = false) {
	if($permanent) {
		header('HTTP/1.1 301 Moved Permanently');
	}
	header('Location: '.$url);
	exit();
}

function db_connect()
{
	$link = mysqli_connect(MYSQLHOST, MYSQLUSER, MYSQLPASSWORD, DATABASE);
	if (!$link) {
    	echo "Error: Unable to connect to MySQL." . PHP_EOL;
    	echo "Debugging errno: " . mysqli_connect_errno() . PHP_EOL;
    	echo "Debugging error: " . mysqli_connect_error() . PHP_EOL;
    	exit;
	}
    return $link;
}

function is_admin($what,$usePk,$comPk)
{
    $link = db_connect();
    $query = "select useLevel from tblCompAuth where usePk=$usePk and comPk in ($comPk,-1)";
	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Admin Check failed: ' . mysqli_connect_error());
	while ($row = mysqli_fetch_assoc($result))
    {
        $level = $row['useLevel'];
        if ($what == $level) 
        {
            return 1;
        }
    }
    return 0;
}

function check_admin($what,$usePk,$comPk)
{
    if (is_admin($what,$usePk,$comPk))
    {
        return 1;
    }
    echo "You are unauthorised to perform that action ($what $usePk $comPk).<br>";
    //redirect('unauthorised.php');
    return 0;
}

function check_auth($region)
{
    $link = db_connect();

    // FIX: check time/region/IP stuff too ...
    // but for no just validate the session
    if (!array_key_exists('XCauth', $_COOKIE))
    {
        return 0;
    }
    $magic = addslashes($_COOKIE['XCauth']);
    $query = "select usePk from tblUserSession where useSession='$magic'";
	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
    $usePk = 0;
	if (mysqli_num_rows($result) > 0)
    {
		$usePk = mysqli_result($result,0,0);
    }
	mysqli_close($link);

    if (!$usePk) 
    {
        return 0;
    }

    return $usePk;
}

function auth($region)
{
    $usePk = 0;
    $browser = addslashes($_SERVER['HTTP_USER_AGENT']);
    if ((strpos($browser, "MSIE 6.0; Windows") || strpos($browser, "MSIE 7.0; Windows")) && strpos($browser, "Opera") == FALSE)
    {
        redirect("better_browsers.php");
        exit;
    }

    $usePk = check_auth($region);
    if ($usePk == 0)
    {
        // auth fails - redirect to login.
        echo "<b><i>Authorisation Failed</i></b>";
        redirect("login.php?message=Authorisation%20Failed:$magic");
        exit;
    }

    return $usePk;
}

function menubar($comPk)
{
    if ($comPk != 0)
    {
        $link = db_connect();
        $query = "select comName,comType from tblCompetition where comPk=$comPk";
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());

        if (mysqli_num_rows($result) > 0)
        {
            $comName = mysqli_result($result,0,0);
            $comType =  mysqli_result($result,0,1);
        }
        else
        {
            $comName = 'Unknown Competition';
            $comType = 'OLC';
        }
        mysqli_close($link);
        
        echo "<div id=\"vhead\"><h1>$comName</h1></div>";
    }
    else
    {
        echo "<div id=\"vhead\"><h1>Skyhigh Cup</h1></div>";
        $comPk = 5;
    }
    echo "<div id=\"menu\">";
    echo "<ul>";
    if (check_auth("system"))
    {
        if ($comPk > 0)
        {
        echo "<li><a href=\"competition_admin.php?comPk=$comPk\">Admin</a></li>";
        }
        else
        {
            echo "<li><a href=\"comp_admin.php\">Admin</a></li>";
        }
    }
    if ($comType == 'OLC')
    {
        echo "<li><a href=\"index.php\">Home</a></li>";
        echo "<li><a href=\"top_scores.php?comPk=$comPk\">Top Scores</a></li>";
        echo "<li><a href=\"top.php?comPk=$comPk\">Top Tracks</a></li>";
        echo "<li><a href=\"recent.php?comPk=$comPk\">Recent Tracks</a></li>";
    }
    else
    {
        echo "<li><a href=\"compview.php?comPk=$comPk\">Home</a></li>";
        echo "<li><a href=\"comp_result.php?comPk=$comPk\">Scores</a></li>";
        echo "<li><a href=\"recent.php?comPk=$comPk\">Recent Tracks</a></li>";
    }
    echo "<li><a href=\"submit_track.php?comPk=$comPk\">Submit Track</a></li>";
    echo "</ul>";
    echo "</div>\n";
}

function adminbar($comPk)
{
    echo "<div id=\"container-eyecatcher\">";
    echo "<div id=\"menu\">";
    echo "<ul id=\"navigation\">";
    if (check_auth("system"))
    {
        echo "<li><a href=\"login.php?logout=1\">Logout</a></li>";
    }
    else
    {
        echo "<li><a href=\"login.php\">Login</a></li>";
    }

    echo "<li><a href=\"comp_admin.php\">Competition</a></li>";
    if ($comPk > 0)
    {
        $link = db_connect();
        $query = "select comName,comType,comEntryRestrict from tblCompetition where comPk=$comPk";
		$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Query failed: ' . mysqli_connect_error());
        if (mysqli_num_rows($result) > 0)
        {
            $comName = mysqli_result($result,0,0);
            $comType =  mysqli_result($result,0,1);
            $comEntryRestrict =  mysqli_result($result,0,2);
        }
        else
        {
            $comName = 'Unknown Competition';
            $comType = 'OLC';
        }
        mysqli_close($link);
        
        echo "<li><a href=\"comp_result.php?comPk=$comPk\">Scores</a></li>";
        echo "<li><a href=\"track_admin.php?comPk=$comPk\">Track</a></li>";
        echo "<li><a href=\"team_admin.php?comPk=$comPk\">Teams</a></li>";
        echo "<li><a href=\"pilot_admin.php?comPk=$comPk\">Pilots</a></li>";
        if ($comEntryRestrict == 'registered')
        {
            echo "<li><a href=\"registration.php?comPk=$comPk\">Registration</a></li>";
        }
    }
    else
    {
        echo "<li><a href=\"track_admin.php\">Track</a></li>";
        echo "<li><a href=\"pilot_admin.php\">Pilots</a></li>";
    }
    echo "<li><a href=\"region_admin.php\">Waypoints</a></li>";
    echo "<li><a href=\"airspace_admin.php\">Airspace</a></li>";
    echo "</ul>";
    echo "</div>";
    echo "</div>";
}

function output_select($name,$selected,$options)
{
    echo "<select name=\"$name\">";
    foreach ($options as $key => $value)
    {
        if (is_int($key))
        {
            $key = $value;
        }
        if ($selected == $value)
        {
            echo "<option value=\"$value\" selected>$key</option>\n";
        }
        else
        {
            echo "<option value=\"$value\">$key</option>\n";
        }
    }
    echo "</select>\n";
}

function waypoint_select($link,$tasPk,$name,$selected)
{
    $query="select distinct RW.* from tblTask T, tblRegion R, tblRegionWaypoint RW where T.tasPk=$tasPk and RW.regPk=R.regPk and R.regPk=T.regPk order by RW.rwpName";
	$result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Waypoint select failed: ' . mysqli_connect_error());
    $waypoints = [];
	while ($row = mysqli_fetch_assoc($result))
    {
        $rwpPk = $row['rwpPk'];
        $rname = $row['rwpName'];
        $waypoints[$rname] = $rwpPk;
    }
    //ksort($waypoints);
    output_select($name,$selected,$waypoints);
}

function cmdlinecheck()
{
    if (!$_REQUEST)
    {
        if (!isset($_SERVER["HTTP_HOST"])) 
        {
            global $argv;
            parse_str($argv[1], $_REQUEST);
            //parse_str($argv[1], $_POST);
        }
    }
}

function reqexists($key)
{
    cmdlinecheck();
    if (array_key_exists($key, $_REQUEST))
    {
        return 1;
    }
    return 0;
}

function reqival($key)
{
    cmdlinecheck();
    if (array_key_exists($key, $_REQUEST))
    {
        return intval($_REQUEST[$key]);
    }
    else
    {
        return 0;
    }
}

function reqfval($key)
{
    cmdlinecheck();
    if (array_key_exists($key, $_REQUEST))
    {
        return floatval($_REQUEST[$key]);
    }
    else
    {
        return 0;
    }
}

function reqsval($key)
{
    cmdlinecheck();
    if (array_key_exists($key, $_REQUEST))
    {
        return addslashes($_REQUEST[$key]);
    }
    else
    {
        return '';
    }
}

?>
