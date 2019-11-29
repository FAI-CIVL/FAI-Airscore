<?php

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
        echo "Debugging error: " . mysqli_connect_error() . PHP_EOL;
        exit;
    }
    mysqli_query($link,"SET CHARACTER SET 'utf8'");
    mysqli_query($link,"SET SESSION collation_connection ='utf8_unicode_ci'");
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

function check_auth($region=0)
{
    $user = get_user();                                     // Get the user object
    //$isSuperUser = JFactory::getUser()->authorise('core.admin');      // Checks if Super User
    //$isAdmin = JFactory::getUser()->authorise('core.login.admin');        // Checks if Admin
    if ( ($user->id != 0) && $user->isAdmin )
    {
        $usePk = $user->id;
    }
    else
    {
        // Redirect the user
        return 0;
    }
    return $usePk;
}

function get_juser()
{
    $pilPk = get_user()->id;
    if ($pilPk == 0)
    {
        // auth fails - redirect to login.
        //echo "<b><i>Authorisation Failed</i></b>";
        $redirect = trim($_SERVER['REQUEST_URI'], '/');
        redirect("/jlogin.php?logreq=1&location=$redirect");
        //exit;
    }

    return $pilPk;
}

function auth($region=0)
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
        //echo "<b><i>Authorisation Failed</i></b>";
        $redirect = trim($_SERVER['REQUEST_URI'], '/');
        redirect("/jlogin.php?logreq=1&location=$redirect");
        //exit;
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

function check_old_task($link, $tasPk)
{
    # We check if waypoints used in this task are old ones, not in use anymore
    $old = 0;
    $query="SELECT
                RW.*
            FROM
                tblRegionWaypoint RW
                INNER JOIN tblTaskWaypoint TW ON RW.rwpPk = TW.rwpPk
            WHERE
                TW.tasPk = $tasPk
                AND RW.rwpOld = 1
            LIMIT
                1";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Check old Waypoint in task failed: ' . mysqli_connect_error());
    if (mysqli_num_rows($result) > 0)
    {
        $old = 1;
    }

    return $old;
}

function waypoint_select($link,$tasPk,$name,$selected)
{
    # If waypoints are an old version, we will display only old ones
    # otherwise, only new ones, to avoid doubles
    $old = check_old_task($link, $tasPk);
    $query="SELECT
                DISTINCT RW.*
            FROM
                tblRegionWaypoint RW
                JOIN tblTask T ON RW.regPk = T.regPk
            WHERE
                T.tasPk = $tasPk
                AND RW.rwpOld = $old
            ORDER BY
                RW.rwpName";
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

#new class selector to be used with JSON scoring
function class_selector($link, $rankings, $selected)
{
    if ( !isset($selected) ) {
        $selected = 'Overall';
    }

    $list = '';
    $myurl = trim($_SERVER['REQUEST_URI'], '/');

    #order rankings array
    $order = [];
    foreach ($rankings as $key => $rank) {
        if ($rank <= 1) {
            $order[$key] = 0;
        }
        else {
            $order[$key] = count($rank);
        }
    }
    array_multisort($order,SORT_NUMERIC,SORT_DESC,$rankings);

    $list .= "<form enctype=\"multipart/form-data\" action=\"$myurl\" name=\"classsel\" id=\"classsel\" method=\"post\">".PHP_EOL;
    $list .= "<select name=\"class\" id=\"class\" onchange=\"document.getElementById('classsel').submit();\"\">".PHP_EOL;

    foreach ($rankings as $key=>$value) {
        if ($value != 0) {
            $name = $key;
            $list .= "<option value='$name'";
            if ($selected == $name) {
              $list .= " selected='selected'";
            }
            $list .= ">$name</option>".PHP_EOL;
        }
    }
    $list .= "</select>".PHP_EOL;
    $list .= "</form>".PHP_EOL;

    return $list;
}

function classselector($link, $claPk, $selected)
{
    //echo "selected: $selected \n";
    # Set the selected option
    if ( !isset($selected) )
    {
        $sql = "SELECT
                    MAX(ranPk) AS maxid
                FROM
                    tblClasCertRank
                WHERE
                    claPk = $claPk";
        $result = mysqli_query($link, $sql);
        $id = mysqli_fetch_object($result);
        $selected = $id->maxid;
        //echo "selected: $selected \n";
    }
    //echo "selected: $selected \n";

    # Create the select element
    $list = '';
    $myurl = trim($_SERVER['REQUEST_URI'], '/');

        //$list = "<select name=\"class\" id=\"class\" onchange=\"document.location.href='$myurl&class=' + this.value;\"> \n";
    $list .= "<form enctype=\"multipart/form-data\" action=\"$myurl\" name=\"classsel\" id=\"classsel\" method=\"post\"> \n";
    $list .= "<select name=\"class\" id=\"class\" onchange=\"document.getElementById('classsel').submit();\"\"> \n";
    $sql= " SELECT
                R.ranPk AS id,
                R.ranName AS name
            FROM
                tblRanking R
                JOIN tblClasCertRank CCR ON R.ranPk = CCR.ranPk
            WHERE
                CCR.cerPk > 0
                AND CCR.claPk = $claPk
            ORDER BY CCR.ranPk DESC ";

    $result = mysqli_query($link, $sql);
    while( $row = mysqli_fetch_assoc($result) )
    {
        $name = $row['name'];
        $id = $row['id'];
        $list .= "<option value='$id'";
        if ($selected == $id)
        {
          $list .= " selected='selected'";
        }
        $list .= ">$name</option>\n";
    }
    #adding the Female and Team choices
    $sql= " SELECT
                claFem,
                claTeam
            FROM
                tblClassification
            WHERE
                claPk = $claPk";

    $result = mysqli_query($link, $sql);
    $more = mysqli_fetch_object($result);
    $female = $more->claFem;
    $team = $more->claTeam;
    if ( $female == 1 )
    {
        $list .= "<option value='0'";
        if ($selected == 0)
        {
          $list .= " selected='selected'";
        }
        $list .= ">Female</option>\n";
    }
    if ( $team == 1 )
    {
        $list .= "<option value='-1'";
        if ($selected == -1)
        {
          $list .= " selected='selected'";
        }
        $list .= ">Team</option>\n";
    }
    $list .= "</select>\n";
    $list .= "</form>\n";
//  echo "$sql \n";
//  echo "<pre> $list </pre>";
//  print_r($row);
    return $list;
}

function get_class_info($link, $comPk)
{
    $fdhv= ''; #parameter to insert in mysql query in result calculations
    $classstr = "<b> Overall </b> - ";
    if (reqexists('class'))
    {
        $cval = reqival('class');
        //echo "cval: $cval \n";
        # Check Female and Team choices first
        if ( $cval == 0 )
        {
            $classstr = "<b> Female Ranking </b> - ";
            $fdhv = "and P.pilSex='F'";
        }
        elseif ( $cval == -1 )
        {
            redirect("team_task_result.php?comPk=$comPk&tasPk=$tasPk");
        }
        # Check Classification Definition
        else
        {
            $sql = "SELECT
                        R.ranName,
                        CCR.cerPk,
                        MAX(CCR2.ranPk) AS maxcval
                    FROM
                        tblCompetition C
                        JOIN tblClasCertRank CCR ON C.claPk = CCR.claPk
                        JOIN tblRanking R ON R.ranPk = CCR.ranPk,
                        tblClasCertRank CCR2
                    WHERE
                        C.comPk = $comPk
                        AND R.ranPk = $cval
                        AND CCR2.claPk = C.claPk
                        AND CCR2.cerPk > 0";
            $result = mysqli_query($link, $sql);
            $row = mysqli_fetch_object($result);
            $rank = $row->ranName;
            $cert = $row->cerPk;
            $maxcval = $row->maxcval;
            //echo "rank: $rank - cert: $cert - maxval: $maxcval \n";
            if ( $cval < $maxcval )
            {
                # Get all certifications allowed in selected Ranking
                $sql = "SELECT
                            CT.cerName
                        FROM
                            tblCertification CT
                            JOIN tblCompetition C ON CT.comClass = C.comClass
                        WHERE
                            CT.cerPk <= $cert
                            AND C.comPk = $comPk
                        ORDER BY CT.cerPk DESC";
                $result2 = mysqli_query($link, $sql);
                $cats = array();
                while ( $row = mysqli_fetch_assoc($result2) )
                {
                    $cats[] = $row['cerName'];
                }
                $fdhv = "AND `traDHV` IN ('" . implode("','",$cats) . "') ";
                //echo "cval < maxcval - fdhv = $fdhv \n";
                $classstr = "<b>" . $rank . "</b> - ";
            }
        }
    }
    return array("name" => $classstr, "fdhv" => $fdhv);
}

function get_ladder_class_info($link, $ladPk, $cval, $season)
{
    $fdhv= ''; #parameter to insert in mysql query in result calculations
    $classstr = "<b> Overall </b> - ";

    if ( !isset($season) )
    {
        $season = getseason();
    }

    # Check Female first
    if ( $cval === 0 )
    {
        $classstr = "<b> Female Ranking </b> - ";
        $fdhv = "and P.pilSex='F'";
    }
//      elseif ( $cval == -1 )
//      {
//          redirect("team_task_result.php?comPk=$comPk&tasPk=$tasPk");
//      }
    # Check Classification Definition
    else
    {
        $sql = "SELECT
                    `R`.`ranName`,
                    `CCR`.`cerPk`,
                    MAX(`CCR2`.`ranPk`) AS `maxcval`
                FROM
                    (
                    `tblLadderSeason` `LS`
                    JOIN `tblClasCertRank` `CCR` USING(`claPk`)
                    JOIN `tblRanking` `R` USING(`ranPk`)
                    ),
                    `tblClasCertRank` `CCR2`
                WHERE
                    `LS`.`ladPk` = '$ladPk'
                    AND `LS`.`seasonYear` = '$season'
                    AND `R`.`ranPk` = '$cval'
                    AND `CCR2`.`claPk` = `LS`.`claPk`
                    AND `CCR2`.`cerPk` > 0";
        $result = mysqli_query($link, $sql);
        $row = mysqli_fetch_object($result);
        $rank = $row->ranName;
        $cert = $row->cerPk;
        $maxcval = $row->maxcval;
        //echo "rank: $rank - cert: $cert - maxval: $maxcval \n";
        if ( $cval < $maxcval )
        {
            # Get all certifications allowed in selected Ranking
            $sql = "SELECT
                        CT.cerName
                    FROM
                        tblCertification CT
                        JOIN tblLadder L ON CT.comClass = L.ladComClass
                    WHERE
                        CT.cerPk <= $cert
                        AND L.ladPk = $ladPk
                    ORDER BY
                        CT.cerPk DESC";
            $result2 = mysqli_query($link, $sql);
            $cats = array();
            while ( $row = mysqli_fetch_assoc($result2) )
            {
                $cats[] = $row['cerName'];
            }
            $fdhv = "AND traDHV IN ('" . implode("','",$cats) . "') ";
            //echo "cval < maxcval - fdhv = $fdhv \n";
            $classstr = "<b>" . $rank . "</b> - ";
        }
    }
    return array("name" => $classstr, "fdhv" => $fdhv);
}

function check_registration($link, $comPk)
{
    $pilPk = get_user()->id;
    echo "<div class=\"register\">";
    if ($pilPk == 0)
    {
        $url = trim($_SERVER['REQUEST_URI'], '/');
        echo "<strong>You need to <a href=\"/jlogin.php?logreq=1&location=$url\">LOGIN </a> to register or cancel from the event</strong>";
    }
    else
    {
        # Check if pilot is already registered
        $sql = "SELECT
                    R.regPk
                FROM
                    tblParticipant R
                WHERE
                    R.pilPk = $pilPk
                    AND R.comPk = $comPk";
        $reg =  mysqli_query($link, $sql);
        # besed on result, makes the register or cancel button
        if (mysqli_num_rows($reg) > 0)
        {
            $button = "<button type=\"submit\" name=\"delpilot\" value=\"$comPk\">Cancel From This Competition</button>";
        }
        else
        {
            $button = "<button type=\"submit\" name=\"addpilot\" value=\"$comPk\">Register in This Competition</button>";
        }
        echo "<form action=\"registered_pilots.php?comPk=$comPk\" name=\"pilreg\" method=\"post\">\n";
        echo "$button \n";
        echo "</form>\n";
    }
    echo "</div>\n";
}

function get_countrycode($link, $id)
{

    $sql = "SELECT
                C.natIso3 AS Code
            FROM
                tblCountryCode C
            WHERE
                C.natID = $id";
    $result = mysqli_query($link, $sql);
    if ( !$result || mysqli_num_rows($result) == 0 )
    {
        $code = 'ITA'; #defaults to Italy
    }
    else
    {
        $country = mysqli_fetch_assoc($result);
        $code = $country['Code'];
    }
    return $code;
}

function get_countrylist($link, $selectname, $selected='')
{
    $list = '';
    $list = "<select name='$selectname' id='$selectname'\">\n";
    $list .= "<option value=''>Country...</option>\n";

    $sql = "    SELECT
                    DISTINCT C.natID AS id,
                    C.natIso3 AS name
                FROM
                    tblCountryCode C
                ORDER BY
                    C.natIso3 ASC";
    $result = mysqli_query($link, $sql);
    while( $country = mysqli_fetch_assoc($result) )
    {
        $name = $country['name'];
        $id = $country['id'];
        $list .= "<option value='$id'";
        if ($selected == $id)
        {
          $list .= " selected='selected'";
        }
        $list .= ">$name</option>\n";
    }
    $list .= "</select>\n";

    return $list;
}

function get_countries($link, $selected='')
{
    $list = '';
    $list = "<select name='country' id='country' onchange=\"document.getElementById('region1').submit();\">\n";
    $list .= "<option value=''>Country...</option>\n";

    $sql = "    SELECT
                    DISTINCT xccISO AS id,
                    xccCountryName AS name
                FROM
                    tblXContestCodes
                ORDER BY
                    xccCountryName ASC";
    $result = mysqli_query($link, $sql);
    while( $country = mysqli_fetch_assoc($result) )
    {
        $name = $country['name'];
        $id = $country['id'];
        $list .= "<option value='$id'";
        if ($selected == $id)
        {
          $list .= " selected='selected'";
        }
        $list .= ">$name</option>\n";
    }
    $list .= "</select>\n";

    return $list;
}

function get_sites($link, $regPk, $country = '', $selected = 0)
{
    //echo "selected in function: $selected <br />";
    $list = '';
    $list = "<select name='xcsite' id='xcsite' onchange=\"document.getElementById('region1').submit();\">\n";
    $list .= "<option value=''>Site...</option>\n";

    $sql = "    SELECT
                    DISTINCT XC.xccSiteID AS id,
                    XC.xccSiteName AS name
                FROM
                    tblXContestCodes XC
                WHERE
                    XC.xccISO = '$country'
                    AND NOT EXISTS (
                        SELECT
                            1
                        FROM
                            tblRegionXCSites RX
                        WHERE
                            RX.xccSiteID = XC.xccSiteID
                            AND RX.regPk = $regPk
                    )
                ORDER BY
                    xccSiteName ASC";
    $result = mysqli_query($link, $sql);
    while( $site = mysqli_fetch_assoc($result) )
    {
        $name = $site['name'];
        $id = $site['id'];
        $list .= "<option value='$id'";
        if ($selected == $id)
        {
          $list .= " selected='selected'";
        }
        $list .= ">$name</option>\n";
    }
    $list .= "</select>\n";

    return $list;
}

function get_launches($link, $regPk, $id, $selected = 0)
{
    $list = '';
    $list = "<select name='xclaunch' id='xclaunch' onchange=\"document.getElementById('rwpPk$id').submit();\">\n";
    $list .= "<option value=''>Launch...</option>\n";

    $sql = "    SELECT
                    DISTINCT xccToID AS id,
                    xccToName AS name
                FROM
                    tblXContestCodes XC
                    INNER JOIN tblRegionXCSites RX ON XC.xccSiteID = RX.xccSiteID
                WHERE
                    RX.RegPk = $regPk
                ORDER BY
                    xccToName ASC";
    $result = mysqli_query($link, $sql);
    while( $launch = mysqli_fetch_assoc($result) )
    {
        $name = $launch['name'];
        $id = $launch['id'];
        $list .= "<option value='$id'";
        if ($selected == $id)
        {
          $list .= " selected='selected'";
        }
        $list .= ">$name</option>\n";
    }
    $list .= "</select>\n";

    return $list;
}

function mysql_update_array($table, $data, $id_field, $id_value)
{
    $link = db_connect();

    foreach ($data as $field=>$value)
    {
        $fields[] = sprintf("`%s` = '%s'", $field, mysqli_real_escape_string($link, $value));
    }

    $field_list = join(',', $fields);

    $query = sprintf("UPDATE `%s` SET %s WHERE `%s` = %s", $table, $field_list, $id_field, intval($id_value));

    mysqli_close($link);

    return $query;
}

function get_formula($link, $cclass, $selected=0)
{
    $list = '';
    $list = "<select name='formula' id='formula'>\n";
    $list .= "<option value=''>Class...</option>\n";

    $sql = "    SELECT
                    DISTINCT forPk AS id,
                    forName AS name,
                    forClass AS type,
                    forVersion AS version
                FROM
                    tblFormula
                WHERE
                    forComClass = '$cclass'
                ORDER BY
                    forPk ASC";
    $result = mysqli_query($link, $sql);
    while( $for = mysqli_fetch_assoc($result) )
    {
        $name = $for['name'] . ' (' . $for['type'] . ' ' . $for['version'] . ')';
        $id = $for['id'];
        $list .= "<option value='$id'";
        if ($selected == $id)
        {
          $list .= " selected='selected'";
        }
        $list .= ">$name</option>\n";
    }
    $list .= "</select>\n";

    //echo $sql . "\n";
    return $list;
}

function secondsToTime($s)
{
    $h = floor($s / 3600);
    $s -= $h * 3600;
    $m = floor($s / 60);
    $s -= $m * 60;
    return $h.':'.sprintf('%02d', $m).':'.sprintf('%02d', $s);
}

function script_isRunning($pid)
{
    try {
        $result = shell_exec(sprintf('ps %d', $pid));
        if(count(preg_split("/\n/", $result)) > 2) {
            return true;
        }
    } catch(Exception $e) {}

    return false;
}

function task_set($link, $tasPk)
{
    $sql = "SELECT
                COUNT(tawPk) AS wpt
            FROM
                `tblTaskWaypoint`
            WHERE
                tasPk = $tasPk
                AND tawType IN ('launch', 'goal')";
    $result = mysqli_query($link, $sql);
    if ( mysqli_result($result,0,0) < 2 )
    {
        # we don't have a task properly set
        return 0;
    }

    return 1;
}

function get_classifications($link, $name, $cclass, $selected=0)
{
    $list = '';
    $list = "<select name='$name' id='classdef'>\n";
    $list .= "<option value=''>Class...</option>\n";

    $sql = "    SELECT
                    DISTINCT claPk AS id,
                    claName AS name
                FROM
                    tblClassification
                WHERE
                    comClass = '$cclass'
                ORDER BY
                    claPk ASC";
    $result = mysqli_query($link, $sql);
    while( $class = mysqli_fetch_assoc($result) )
    {
        $name = $class['name'];
        $id = $class['id'];
        $list .= "<option value='$id'";
        if ($selected == $id)
        {
          $list .= " selected='selected'";
        }
        $list .= ">$name</option>\n";
    }
    $list .= "</select>\n";

    //echo $sql . "\n";
    return $list;
}

function getseason( $date=0 )
{
    if ( $date == 0 )
    {
        # Get today
        $date = date('Ymd');
    }
    $day = date('md', strtotime($date));
    $season = date('Y', strtotime($date));;
    if ( $day > 1031 )
    {
        $season++;
    }
    return $season;
}

function season_array($link, $seasonstart=0)
{
    # Checks which is the oldest comp, and creates the seasons array
    $query = "  SELECT
                    comDateFrom
                FROM
                    tblCompetition
                ORDER BY
                    comDateFrom ASC
                LIMIT
                    1";
    $result = mysqli_query($link, $query);
    $oldest = mysqli_result($result,0,0);

    # Checks which season was the oldest comp
    $firstseason = getseason($oldest);
    $lastseason = getseason();

    $array = [];
    for ($i = $firstseason; $i <= $lastseason; $i++)
    {
        $array[] = $i;
    }

    return $array;
}

function safe_process($link, $command, $tasPk, $comPk, $type)
{
    # Function that launch a script, and redirects to a waiting page if it takes too long, to avoid timeout errors
    $out = '';
    $retv = 0;
    //$command = BINDIR . "task_up.pl $tasPk $param" . ' > /dev/null 2>&1 & echo $!; ';
    $pid = exec($command, $out, $retv);
    sleep(10);
    if ( script_isRunning($pid) )
    {
        $ptime = microtime(true);
        redirect("safe_process_admin.php?tasPk=$tasPk&comPk=$comPk&pid=$pid&time=$ptime&$type=1");
    }
    //redirect("task_scoring_admin.php?tasPk=$tasPk&comPk=$comPk&pid=$pid&time=$ptime&$type=1");
}

?>
