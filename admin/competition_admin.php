<?php
require 'admin_startup.php';
require LIBDIR.'dbextra.php';

//
// Main Code Begins HERE //
//

$comPk = intval($_REQUEST['comPk']);

$usePk = auth('system');
$link = db_connect();
$file = __FILE__;
$message = '';

if ( reqexists('created') )
    $message .= "Competition ID = $comPk succesfully created. \n";


# Add a task
if ( reqexists('add') )
{
    $Name = reqsval('taskname');
    $Date = reqsval('date');
    $TaskStart = reqsval('taskstart');
    $TaskFinish = reqsval('taskfinish');
    $StartOpen = reqsval('starttime');
    $StartClose = reqsval('startclose');
    $TaskType = reqsval('tasktype');
    $Interval = reqival('interval');
    $regPk = reqsval('region');
    $depart = 'leadout'; # Default departure points type to leadout points
    
    # Check class to default arrival points
    $query = "SELECT comClass FROM tblCompetition WHERE comPk = $comPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Comp Class check failed: ' . mysqli_connect_error());
    $arrival = ( mysqli_result($result, 0, 0) == 'HG' ? 'on' : 'off' );
    
    # Defaults Height Bonus points to off
    // $heightbonus = 'off'; # Made in mysql default

    check_admin('admin',$usePk,$comPk);

//     if ($TaskType == 'speedrun-interval' && $Interval == 0)
//     {
//         echo "Unable to add task a speedrun-interval task with no gate interval times<br>";
//         exit(1);
//     }

    $query = "select * from tblTask where tasDate='$Date' and comPk=$comPk";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task check failed: ' . mysqli_connect_error());

    if (mysqli_num_rows($result) > 0)
    {
        echo "Unable to add task with duplicate date: $Date<br>";
        exit(1);
    }

    $query = "insert into tblTask (comPk, tasName, tasDate, tasTaskStart, tasFinishTime, tasStartTime, tasStartCloseTime, tasSSInterval, tasTaskType, regPk, tasDeparture, tasArrival) values ($comPk, '$Name', '$Date', '$Date $TaskStart', '$Date $TaskFinish', '$Date $StartOpen', '$Date $StartClose', $Interval, '$TaskType', $regPk, '$depart', '$arrival')";
    $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task add failed: ' . mysqli_connect_error());

    # Get the task we just inserted
    $tasPk = mysqli_insert_id($link);

    # Now check for pre-submitted tracks ..
    // FIX: check for task / track date match!
    // $query = "select traPk from tblComTaskTrack where comPk=$comPk and tasPk is null";
    $query = "select CTT.traPk from tblComTaskTrack CTT, tblTask T, tblTrack TR, tblCompetition C where CTT.comPk=$comPk and C.comPk=CTT.comPk and T.tasPk=$tasPk and CTT.traPk=TR.traPk and CTT.tasPk is null and TR.traStart > date_sub(T.tasStartTime, interval C.comTimeOffset+1 hour) and TR.traStart < date_sub(T.tasFinishTime, interval C.comTimeOffset hour)";
    $result = mysqli_query($link, $query);
    $tracks = [];
    while ($row = mysqli_fetch_assoc($result))
    {
        $tracks[] = $row['traPk'];
    }

    if (sizeof($tracks) > 0)
    {
        // Give them a task number 
        $sql = "update tblComTaskTrack set tasPk=$tasPk where comPk=$comPk and traPk in (" . implode(",",$tracks) . ")";
        $result = mysqli_query($link, $query);

        // Now verify the pre-submitted tracks against the task
        foreach ($tracks as $tpk)
        {
            echo "Verifying pre-submitted track: $tpk<br />";
            $out = '';
            $retv = 0;
            exec(BINDIR . "track_verify.pl $tpk", $out, $retv);
        }
    }
}

# Delete a task
if ( reqexists('delete') )
{
    $id = reqival('delete');
    check_admin('admin',$usePk,$comPk);

    if ($id > 0)
    {
        $query = "delete from tblTask where tasPk=$id";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task delete failed: ' . mysqli_connect_error());
    
        $query = "delete from tblComTaskTrack where tasPk=$id";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task CTT deletefailed: ' . mysqli_connect_error());
    
        $query = "delete from tblTaskWaypoint where tasPk=$id";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task TW delete failed: ' . mysqli_connect_error());
    
        $query = "delete from tblTaskResult where tasPk=$id";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Task TR delete failed: ' . mysqli_connect_error());

        $message .= "Task Removed\n";
    }
    else
    {
        $message .= "Unable to remove task: $id\n";
    }
}

// Update the competition
if ( reqexists('update') )
{
    check_admin('admin',$usePk,$comPk);
    
    # Update tblCompetition
    $comarr = [];
    $comarr['comName'] = reqsval('comname');
    $comarr['comLocation'] = reqsval('location');
    $comarr['comDateFrom'] = reqsval('datefrom');
    $comarr['comDateTo'] = reqsval('dateto');
    $comarr['comMeetDirName'] = reqsval('director');
    $comarr['comTimeOffset'] = floatval($_REQUEST['timeoffset']);
    $comarr['comType'] = reqsval('comptype');
    $comarr['comCode'] = reqsval('code');
    $comarr['comClass'] = reqsval('compclass');
    $comarr['claPk'] = reqival('classdef');
    $comarr['comEntryRestrict'] = reqsval('entry');
    $comarr['comSanction'] = reqsval('sanction');
    
    $query = mysql_update_array('tblCompetition', $comarr, 'comPk', $comPk);
    //echo $query;
    mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Competition update failed: ' . mysqli_connect_error());
    
    # Update tblForComp
    $comarr = [];
    $comarr['forPk'] = reqival('formula');
    $comarr['comOverallScore'] = reqsval('overallscore');
    $comarr['comOverallParam'] = 1 - floatval($_REQUEST['overallparam']) / 100; 
    $comarr['forNomTime'] = reqfval('nomtime');
    $comarr['forNomGoal'] = reqfval('nomgoal') / 100;
    $comarr['forNomDistance'] = reqfval('nomdist');
    $comarr['forMinDistance'] = reqfval('mindist');
    $comarr['forNomLaunch'] = reqfval('nomlaunch') / 100;
    $comarr['comTeamSize'] = reqival('teamsize');
    $comarr['comTeamScoring'] = reqsval('teamscoring');
    $comarr['comTeamOver'] = reqsval('teamover');
    
    $query = mysql_update_array('tblForComp', $comarr, 'comPk', $comPk);
    //echo $query;
    mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' tblForComp update failed: ' . mysqli_connect_error());

    $message .= "Competition details successfully updated. \n";
    
}

# Manage Admin
if ( reqexists('updateadmin') )
{
    check_admin('admin',$usePk,$comPk);

    $adminPk = reqival('adminlogin');
    if ($adminPk > 0)
    {
        $query = "  INSERT INTO tblCompAuth (usePk, comPk, useLevel) 
                    VALUES 
                        ($adminPk, $comPk, 'admin')";
        $result = mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' Adinistrator addition failed: ' . mysqli_connect_error());
    }
    
    $message .= "Admin ID $adminPk succesfully added. \n\n";
}

# Change Ladders
if ( reqexists('ladPk') )
{
    check_admin('admin',$usePk,$comPk);

    $id = reqival('ladPk');
    $active = isset($_POST["active$id"]) ? 1 : 0;
    
    //echo "ladPk=$id, active=".$_POST["active$id"]."<br />\n";

    if ( $id > 0 )
    {
        if ( $active == 0 )
        {
            $query = "DELETE FROM tblLadderComp WHERE ladPk=$id AND comPk=$comPk";
        }
        else
        {
            $query = "INSERT INTO tblLadderComp (ladPk, comPk) VALUES ($id, $comPk)";
        }
        //echo $query;
        mysqli_query($link, $query) or die('Error ' . mysqli_errno($link) . ' League status update failed: ' . mysqli_connect_error());

        $message .= "League status updated.<br />";
    }
    else
    {
        $message .= "Unable to update League status: $id\n";
    }
}

# Get Competition Info
$forPk = 0;
$ctype = '';
// $sql = "SELECT 
//             C.*, 
//             FC.*, 
//             F.forName 
//         FROM 
//             tblCompetition C 
//             JOIN tblForComp FC ON C.comPk = FC.comPk 
//             LEFT OUTER JOIN tblFormula F ON FC.forPk = F.forPk 
//         WHERE 
//             C.comPk = $comPk";

$sql = "SELECT * FROM CompetitionView WHERE comPk = $comPk";
$result = mysqli_query($link, $sql);
if ( $row = mysqli_fetch_assoc($result) )
{
    $cname = $row['comName'];
    $cdfrom = substr($row['comDateFrom'],0,10);
    $cdto = substr($row['comDateTo'],0,10);
    $cdirector = $row['comMeetDirName'];
    $clocation = $row['comLocation'];
    $ctimeoffset = $row['comTimeOffset'];
    $overallscore = $row['comOverallScore'];
    $overallparam = 100 - $row['comOverallParam'] * 100;
    $teamscoring = $row['comTeamScoring'];
    $teamover = $row['comTeamOver'];
    $teamsize = $row['comTeamSize'];
    $ccode = $row['comCode'];
    $ctype = $row['comType'];
    $forPk = $row['forPk'];
    $forName = $row['forName'];
    $entry = $row['comEntryRestrict'];
    $cclass = $row['comClass'];
    $clocked = $row['comLocked'];
    $claPk = $row['claPk'];
    $nomdist = $row['forNomDistance'];
    $mindist = $row['forMinDistance'];
    $nomtime = $row['forNomTime'];
    $nomgoal = $row['forNomGoal'] * 100;
    $nomlaunch = $row['forNomLaunch'] * 100;  
    $sanction = $row['comSanction']; 
    $ext = $row['comExt'] <> 0 ? "<strong>EXTERNAL EVENT</strong>" : null;
    $ext .= isset($row['comExtUrl']) ? ": <a href='".$row['comExtUrl']." target='_blank'>website</a>" : null;
}

if ( $ext )
{
    $message .= "* External Competition * \n";
}
# Create the tables
# Competition Details
$ctable = [];

# case External Competition
if ( $ext )
{
    $ctable[] = array('<h6>Type:</h6>', $ctype, '<h6>Category:</h6>', $cclass, '', '' );
    $ctable[] = array('<hr />','','','','','');
    $ctable[] = array('<h6>Name:</h6>', fin('comname', $cname, 14), 'Abbrev:', fin('code', $ccode, 10), 'Sanction:', fselect('sanction', $sanction, array('','none','League','FAI 2', 'PWC')) );
    $ctable[] = array('Location:', fin('location', $clocation, 10), 'Date From:', $cdfrom, 'Date To:', $cdto );
    $ctable[] = array('Director:', fin('director', $cdirector, 14), '', '', '', '' );
    $ctable[] = array('Time Offset:', $ctimeoffset,'','','','');
    $ctable[] = array('Pilot Entry:', $entry,'','','','');
}
else
{
    $ctable[] = array('<h6>Type:</h6>', fselect('comptype', $ctype, array('RACE','Route', 'Team-RACE')), '<h6>Category:</h6>', fselect('compclass', $cclass, array('PG','HG','mixed')), '', '' );
    $ctable[] = array('<hr />','','','','','');
    $ctable[] = array('<h6>Name:</h6>', fin('comname', $cname, 14), 'Abbrev:', fin('code', $ccode, 10), 'Sanction:', fselect('sanction', $sanction, array('','none','League','FAI 2', 'PWC')) );
    $ctable[] = array('Location:', fin('location', $clocation, 10), 'Date From:', fin('datefrom', $cdfrom, 10), 'Date To:', fin('dateto', $cdto, 10) );
    $ctable[] = array('Director:', fin('director', $cdirector, 14), '', '', '', '' );
    $ctable[] = array('Time Offset:', fin('timeoffset', $ctimeoffset, 10),'','','','');
    $ctable[] = array('Pilot Entry:', fselect('entry', $entry, array('open', 'registered')),'','','','');
}

$compinfo = ftable($ctable, 'class=compinfotable', '', '');

# Formula Details
$ftable = [];

# case External Competition
if ( $ext )
{
    $ftable[] = array('<h6>Formula:</h6>', $forName,'','', 'Class. Def: ', get_classifications($link, 'classdef', $cclass, $claPk));
    $ftable[] = array('<h6>Scoring:</h6>', $overallscore, 'Score param %:', $overallparam,'','');
    $ftable[] = array('<hr />','','','','','');
    $ftable[] = array('Nom Dist (km):', $nomdist, 'Min Dist (km):', $mindist,'Nom Time (min):', $nomtime, '','');
    $ftable[] = array('Nom Goal (%):', $nomgoal,'Nom Launch (%):', $nomlaunch, '', '');
    $ftable[] = array('<hr />','','','','','');
    $ftable[] = array('<h6>Team Scoring:</h6>', fselect('teamscoring', $teamscoring, array('aggregate', 'team-gap', 'handicap')), 'Team Over:', fselect('teamover', $teamover, array('best', 'selected')), 'Team Size:', fin('teamsize', $teamsize, 4));
    $ftable[] = array('<hr />','','','','','');
}
else
{
    $ftable[] = array('<h6>Formula:</h6>', get_formula($link, $cclass, $forPk),"<a href='formula_admin.php?edit=$forPk'>Manage Formula</a>",'', 'Class. Def: ', get_classifications($link, 'classdef', $cclass, $claPk));
    $ftable[] = array('<h6>Scoring:</h6>', fselect('overallscore', $overallscore, array('all', 'ftv', 'round')), 'Score param %:', fin('overallparam', $overallparam, 10),'','');
    $ftable[] = array('<hr />','','','','','');
    $ftable[] = array('Nom Dist (km):', fin('nomdist',$nomdist,4), 'Min Dist (km):', fin('mindist', $mindist, 4),'Nom Time (min):', fin('nomtime', $nomtime, 4), '','');
    $ftable[] = array('Nom Goal (%):', fin('nomgoal',$nomgoal,4),'Nom Launch (%):', fin('nomlaunch',$nomlaunch,4), '', '');
    $ftable[] = array('<hr />','','','','','');
    $ftable[] = array('<h6>Team Scoring:</h6>', fselect('teamscoring', $teamscoring, array('aggregate', 'team-gap', 'handicap')), 'Team Over:', fselect('teamover', $teamover, array('best', 'selected')), 'Team Size:', fin('teamsize', $teamsize, 4));
    $ftable[] = array('<hr />','','','','','');
}

$formulainfo = ftable($ftable, 'class=compinfotable', '', '');

# Get Administrators 
$atable = [];

$sql = "SELECT 
            U.useName AS name 
        FROM 
            tblCompAuth A 
            JOIN UserView U ON U.usePk = A.usePk 
        WHERE 
            A.comPk = $comPk";
$result = mysqli_query($link, $sql);
$admin = [];
while ( $admins = mysqli_fetch_assoc($result) )
    $admin[] = $admins['name'];

$atable[] = array('<h6>Administrators:</h6>', implode(", ", $admin),'');
$atable[] = array('<hr />','','');

# Populating a multiple choice with all admins not already active in the comp
$sql = "SELECT 
            U.usePk as user, 
            U.* 
        FROM 
            UserView U 
        WHERE 
            NOT EXISTS (
                SELECT 
                    A.* 
                FROM 
                    tblCompAuth A 
                WHERE 
                    A.usePk = U.usePk 
                    AND A.comPk = $comPk
            )";
$admin = [];
$result = mysqli_query($link, $sql);
while ( $admins = mysqli_fetch_assoc($result) )
    $admin[$admins['useLogin']] = intval($admins['user']);

$atable[] = array("<h6>Add Administrator: </h6>", fselect('adminlogin', '', $admin),fis('updateadmin', 'Add', '') );

$admininfo = ftable($atable, 'class=compinfotable', '', ''); 

# Populating a checkbox list with all active ladders for the season
$season = getseason($row['comDateFrom']);
//echo $season . "\n";
$ltable = [];
$sql = "    SELECT 
                DISTINCT LS.ladPk, 
                L.ladName, 
                LC.comPk AS active 
            FROM 
                tblLadderSeason LS 
                JOIN tblLadder L USING (ladPk) 
                LEFT OUTER JOIN tblLadderComp LC ON LS.ladPk = LC.ladPk 
                AND LC.comPk = $comPk 
            WHERE 
                ladActive = TRUE 
                AND seasonYear = $season";
//echo $sql ."\n";
$result = mysqli_query($link, $sql);
while ( $ladder = mysqli_fetch_assoc($result) )
{
    $name = $ladder['ladName'];
    $id = $ladder['ladPk'];
    $active = isset($ladder['active']) ? 1 : 0;
    //echo "name: $name, ladPk = $id, active=$active";
    $ltable[] = array("<form action=\"competition_admin.php?comPk=$comPk\" name=\"ladder$id\" id=\"ladder$id\" method=\"post\">" . "$name: ", "<input type='hidden' name='ladPk' value='$id'>" . fic("active$id", "", $active, "onchange='this.form.submit()'") . "</form>");
}
//print_r($ltable);

$ladderinfo = ftable($ltable, 'class=compinfotable', '', '');


//initializing template header
tpadmin($link,$file,$row);

if ( $message !== '')
{
    echo "<h4> <span style='color:red'>$message</span> </h4>";
}

echo "<h4>Competition Info:</h4>\n";
echo "<form action=\"competition_admin.php?comPk=$comPk\" name=\"comedit\" method=\"post\"> \n";
echo $compinfo;
echo "<hr /> \n";
echo "<h4>Scoring Formula Parameters:</h4>\n";
echo $formulainfo;
echo "<hr /> \n";
echo fis('update', 'Update Competition', '');
echo "</form>\n";
echo "<hr /> \n";
echo "<h4>League Partecipation:</h4>\n";
echo $ladderinfo;
echo "<hr /> \n";
echo "<h4>Management:</h4>\n";
echo "<form action=\"competition_admin.php?comPk=$comPk\" name=\"adminedit\" method=\"post\"> \n";
echo $admininfo;
echo "</form>\n";
echo "<hr /> \n";

# Tasks
echo "<hr />\n";
echo "<h3>Tasks</h3>\n";
echo "<form action=\"competition_admin.php?comPk=$comPk\" name=\"taskadmin\" method=\"post\">\n";
echo "<ol>\n";
$count = 1;
$sql = "SELECT T.*, traPk as Tadded FROM tblTask T left outer join tblComTaskTrack CTT on CTT.tasPk=T.tasPk where T.comPk=$comPk group by T.tasPk order by T.tasDate";
$result = mysqli_query($link, $sql);
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $tasPk = $row['tasPk'];
    $tasDate = $row['tasDate'];
    $tasName = $row['tasName'];
    $tasDistance = $row['tasDistance'];
    $tasTaskStart = $row['tasTaskStart'];
    $tasStartTime = $row['tasStartTime'];
    $tasFinishTime = $row['tasFinishTime'];
    $tasResultsType = $row['tasResultsType'];
    $tasTaskType = $row['tasTaskType'];
    $tasDistance = $row['tasDistance'];
    $tasSSDistance = $row['tasSSDistance'];
    $tasSSOpen = $row['tasSSOpen'];
    $tasSSClose = $row['tasSSClose'];
    $tasESClose = $row['tasESClose'];
    $tasDistFlown = $row['tasTotalDistanceFlown'];
    $tasShortRoute = $row['tasShortRouteDistance'];

    echo "<li>\n";
    if ($row['Tadded'] < 1)
    {
        echo "<button type=\"submit\" name=\"delete\" value=\"$tasPk\">del</button>\n";
    }
    echo "<a href=\"task_admin.php?comPk=$comPk&tasPk=$tasPk\">$tasName: " . round($tasShortRoute/1000,1) . " kms on " . $tasDate . " (" . substr($tasTaskStart,11) . " - " . substr($tasFinishTime,11) . ")</a></li>\n";

    $count++;
}
echo "</ol>\n";

$sql = "SELECT * FROM tblRegion R";
$regions = [];
$result = mysqli_query($link, $sql);
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $regPk = $row['regPk'];
    $regDesc = $row['regDescription'];
    $regions[$regDesc] = $regPk;
}

$sql = "SELECT T.* FROM tblCompetition C, tblTask T where T.comPk=C.comPk and C.comPk=$comPk order by T.tasPk limit 1";
$result = mysqli_query($link, $sql);
$defregion = array();
if (mysqli_num_rows($result) > 0)
{
    $row = mysqli_fetch_array($result, MYSQLI_BOTH);
    $defregion = $row['regPk'];
}


echo "<hr />\n";

if ( !$ext )
{
    $depdef = 'leadout'; 
    echo "<h4>Add new Task: </h4>\n";
    $out = ftable(
        array(
            array('Task Name:', fin('taskname', '', 10), 'Date:', fin('date', '', 10),'',''),
            array('Region:', fselect('region', $defregion, $regions), 'Task Type:', fselect('tasktype', 'race', array('race', 'elapsed time', 'free distance', 'distance with bearing')),'',''),
            array('Task Start:', fin('taskstart', '', 10), 'Task Finish:', fin('taskfinish', '', 10),'',''), 
            array('Start Open:', fin('starttime', '', 10), 'Start Close:', fin('startclose', '', 10), 'Gate Interval:', fin('interval', '', 4)) 
            //array('Depart Bonus:', fselect('departure', $depdef, array('on', 'off', 'leadout', 'kmbonus')), 'Arrival Bonus:', fselect('arrival', 'on', array('on', 'off')),'','')
        ), '', '', '');

    print_r($out);
    echo "<input type=\"submit\" name=\"add\" value=\"Add Task\">\n";
}
echo "</form>\n";


tpfooter($file);

?>


