<?php
require 'startup.php';

function getseasoninfo($link, $season)
{
    $seasonstart = date(($season-1).'-11-01');
    //echo 'inizio stagione: '.$seasonstart;
    $seasonend = date(($season).'-10-31');
    //echo 'fine stagione: '.$seasonend;
    $today = date('Y-m-d');

    $sql = "SELECT  COUNT(comPk) AS comNum, 
                    (SELECT COUNT(comPk) FROM tblCompetition WHERE (comDatefrom > '$seasonstart' AND comDateTo < '$today') ) AS pastCom, 
                    (SELECT COUNT(comPk) FROM tblCompetition WHERE (comDatefrom > '$today' AND comDateTo < '$seasonend') ) AS nextCom, 
                    (SELECT COUNT(comPk) FROM tblCompetition WHERE (comDatefrom > '$seasonstart' AND ('$today' BETWEEN comDatefrom AND comDateTo) AND comDateTo < '$seasonend') ) AS openCom 
                    FROM tblCompetition 
                    WHERE (comDateFrom BETWEEN '$seasonstart' AND '$seasonend')";
    //echo 'sql = '.$sql;
    $result = mysqli_query($link, $sql);
    $row = mysqli_fetch_assoc($result);

    return $row;    
}


function getcomplist($link, $season, $list=0)
{
    $seasonstart = date(($season-1).'-11-01');
    $seasonend = date(($season).'-10-31');
    $today = date('Y-m-d');
    $complist = [];
    $complist[] = array("Competition", "Class", "Location", "Period", "" );
    
    $sql = "SELECT 
                * 
            FROM 
                tblCompetition 
            WHERE 
                (
                    comDateFrom BETWEEN '$seasonstart' 
                    AND '$seasonend'
                ) 
            ORDER BY 
                comDateFrom DESC";
    $result = mysqli_query($link, $sql);
    while ( $row = mysqli_fetch_array($result, MYSQLI_BOTH) )
    {
        // FIX: if not finished & no tracks then submit_track page ..
        // FIX: if finished no tracks don't list!
        $cpk = $row['comPk'];
        $name = $row['comName'];
        $location = ucwords(strtolower($row['comLocation']));
        $registration = date_create($row['comDateFrom']);
        $datefrom = date_format( date_create($row['comDateFrom']), 'd-m-Y ' );
        $dateto = date_format( date_create($row['comDateTo']), 'd-m-Y ' );
        $class = $row['comClass'];
        $today = new DateTime('now');
        $ext = $row['comExt'] <> 0 ? "External event" : null;
        $ext .= isset($row['comExtUrl']) ? ": <a href='".$row['comExtUrl']." target='_blank'>website</a>" : null;

        
        # Get class image
        $image = strtolower($class) . '.png';
        if ( $today < $registration )
        {
            $complist[] = array("<a href=\"registered_pilots.php?comPk=$cpk\">$name</a>", "<img src='./images/$image' alt='$class' class='compclass'>", $location, $datefrom." - ".$dateto, $ext );
        }
        else
        {
            $complist[] = array("<a href=\"comp_result.php?comPk=$cpk\">$name</a>", "<img src='./images/$image' alt='$class' class='compclass'>", $location, $datefrom." - ".$dateto, $ext );
        }
    }
    return $complist;
    
}

//
//       Main Code Begins HERE       //
//

$link = db_connect();
$list = isset($_REQUEST['list']) ? $_REQUEST['list'] : null;
$season = isset($_REQUEST['season']) ? $_REQUEST['season'] : getseason(date('Ymd'));

$file = __FILE__;

$page = 'LP AirScore';
$title = 'AirScore - Online Scoring Tool';

# Season selector
$stable = [];
$stable[] = array("Season: ", fselect('season', $season, season_array($link), " onchange=\"document.getElementById('main').submit();\"") );

$row = getseasoninfo($link,$season);

//initializing template header
tpinit($link,$file,$row);

echo "<form enctype='multipart/form-data' action=\"index.php\" name='main' id='main' method='post'>\n";
echo ftable($stable,"class='selector'", '', '');
echo "</form>\n";
echo "<hr />\n";
echo ftable(getcomplist($link, $season, $list),"class='format complist'", '', '');

tpfooter($file);

?>
