<?php
require 'authorisation.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

$debug = 0;

// mapping one field to another name for insert ...
// valmap is original table key => val pairs
// map gives field mapping name changes or absolute values
// or "-" exclude the field 
function insert_map($table,$map,$valmap)
{
    $sql = "insert into $table (";

    $count = 0;
    $fieldarr = [];
    #print_r($valmap);
    foreach ($valmap as $key => $val)
    {
        if (key_exists($key, $map))
        {
            $altkey = $map[$key];
            if (is_numeric($altkey))
            {
                $fieldarr[] = $key;
                $valarr[] = $altkey;
            }
            elseif ($altkey != "-")
            {
                $fieldarr[] = $altkey;
                if (!$val || is_numeric($val))
                {
                    $valarr[] = 0 + $val;
                }
                else
                {
                    $valarr[] = "'$val'";
                }
            }
        }
        else
        {
            $fieldarr[] = $key;
            if (!$val || is_numeric($val))
            {
                $valarr[] = 0 + $val;
            }
            else
            {
                $valarr[] = "'$val'";
            }
        }
    }

    $sql = $sql . join(",",$fieldarr) . ") values (" . join(",", $valarr) . ")";

    return $sql;
}

$comPk=reqival('comPk');
if ($debug)
{
    $comPk = 7;
}

$link = db_connect();
$usePk = check_auth('system');

$link = db_connect();
$isadmin = is_admin('admin',$usePk,$comPk);

# nuke normal header - for exported race file
#header("Content-type: text/plain");
#header("Cache-Control: no-store, no-cache");
#AXXXZZZGPSBabel
#HFDTE040207
#HFPLTPILOT:Unknown

# insert new competition .. get hgfa_ladder.comPk 
# check if it exists .. if so update/delete other stuff ..

$sql = "select comName,comType,comLocation,comDateFrom,comDateTo,comMeetDirName,comTimeOffset,comSanction,forPk from xcdb.tblCompetition where comPk=$comPk";
print $sql;
//$result = mysql_query($sql, $link) or die("can't select comp details");
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' cannnot select comp details' . mysqli_connect_error());
//$row = mysql_fetch_array($result, MYSQL_ASSOC);
$row = mysqli_fetch_assoc($result);

$cname = $row['comName'];
$ctype = $row['comType'];
$cloc = $row['comLocation'];
$cfrom = $row['comDateFrom'];
$cto = $row['comDateTo'];
$cdirname = $row['comMeetDirName'];
$coffset = $row['comTimeOffset'];
$csanction = $row['comSanction'];
$forPk = $row['forPk'];

$sql = "select comPk from hgfa_ladder.tblCompetition where comName='$cname' and comDateFrom='$cfrom'";
//$result = mysql_query($sql, $link) or die("can't select comp details" . mysql_error() . "\n");
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' cannot select comp details' . mysqli_connect_error());
$HcomPk = 0;
//if (mysql_num_rows($result) > 0)
if (mysqli_num_rows($result) > 0)
{
//    $HcomPk = 0 + mysql_result($result,0,0);
    $HcomPk = 0 + = mysqli_result($result,0,0);
}

# if we have one .. then update 
if ($HcomPk == 0)
{
    $sql = "insert into hgfa_ladder.tblCompetition (comName,comLocation,comDateFrom,comDateTo,comMeetDirName,sanValue) values ('$cname','$cloc','$cfrom','$cto','$cdirname','$csanction')";
//    $result = mysql_query($sql, $link) or die("can't insert new competition: " . mysql_error() . "\n");
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' cannot insert new competition: ' . mysqli_connect_error());
//    $HcomPk = mysql_insert_id();
    $HcomPk = mysqli_insert_id($link);
}
else
{
    $sql = "update hgfa_ladder.tblCompetition set comLocation='$cloc', comDateTo='$cto',comMeetDirName='$cdirname',sanValue='$csanction' where comPk=$HcomPk";
//    $result = mysql_query($sql, $link) or die("can't update competition" . mysql_error() . "\n");
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' cannot update competition' . mysqli_connect_error());
}

if ($HcomPk == 0)
{
    exit(1);
}

# Formula?
$sql = "select * from xcdb.tblFormula where forPk=$forPk";
//$result = mysql_query($sql,$link) or die("Unable to find formula: " . mysql_error() . "\n");
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to find formula: ' . mysqli_connect_error());
//$row = mysql_fetch_array($result, MYSQL_ASSOC);
$row = mysqli_fetch_assoc($result);
$fgoal = $row['forNomGoal'];
$fmdist = $row['forMinDistance'];
$fndist = $row['forNomDistance'];
$fntime = $row['forNomTime'];

$sql = "select forPk from hgfa_ladder.tblFormulaCompetition where
    forNomGoal=$fgoal and forMinDistance=$fmdist and forNomDistance=$fndist and forNomTime=$fntime";
//$result = mysql_query($sql,$link) or die("Unable to select formula: " . mysql_error() . "\n");
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to select formula: ' . mysqli_connect_error());
//if (mysql_num_rows($result) > 0)
if (mysqli_num_rows($result) > 0)
{
//    $HforPk=mysql_result($result,0,0);
    $HforPk = mysqli_result($result,0,0);
}
else
{
    $hntime = $fntime / 60;
    $fparam = "ÿþ $fmdist; $fndist; $fgoal; $hntime; 1; 2000; 1";
    $sql = "insert into hgfa_ladder.tblFormulaCompetition (forParameter,forNomGoal,forMinDistance,forNomDistance,forNomTime) values ('$fparam',$fgoal, $fmdist, $fndist, $fntime)";
//    $result = mysql_query($sql,$link) or die("Unable to insert formula: " . mysql_error() . "\n");
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to insert formula: ' . mysqli_connect_error());
//    $HforPk = mysql_insert_id();
    $HforPk = mysqli_insert_id($link);
}

$sql = "update hgfa_ladder.tblCompetition set comFormulaID=$HforPk where comPk=$HcomPk";
//$result = mysql_query($sql,$link) or die("Unable to update comp formula: " . mysql_error() . "\n");
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to update comp formula: ' . mysqli_connect_error());


# make pilPk map 
if ($ctype == 'Team-RACE')
{
    print "<br>Com-type=$ctype<br>";
    $sql ="SELECT P.pilPk, P.pilHGFA, P.pilFirstName as fname, P.pilLastName as lname, P.pilSex as sex,HP.pilPk as HpilPk,HP.pilLastName,HP.pilFirstName,HP.pilIDGlobal from tblTeamResult TR, tblTeam TM, tblTeamPilot TP, tblTask T, tblPilot P left outer join hgfa_ladder.tblPilot HP on HP.pilIDGlobal=P.pilHGFA where TM.comPk=$comPk and TP.teaPk=TM.teaPk and P.pilPk=TP.pilPk and T.tasPk=TR.tasPk and T.comPk=$comPk group by P.pilPk";
}
else
{
    $sql ="SELECT P.pilPk, P.pilHGFA, P.pilNationCode, P.pilFirstName as fname, P.pilLastName as lname, P.pilSex as sex,HP.pilPk as HpilPk,HP.pilLastName,HP.pilFirstName,HP.pilIDGlobal from tblTaskResult TR, tblTrack TL, tblTask T, tblPilot P left outer join hgfa_ladder.tblPilot HP on HP.pilIDGlobal=P.pilHGFA where TL.traPk=TR.traPk and P.pilPk=TL.pilPk and T.tasPk=TR.tasPk and T.comPk=$comPk group by P.pilPk";
}
//$result = mysql_query($sql,$link) or die("Unable to find pilots: " . mysql_error() . "\n");
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to find pilots: ' . mysqli_connect_error());
$pilmap = [];
//while($row = mysql_fetch_array($result, MYSQL_ASSOC))
while ($row = mysqli_fetch_assoc($result))
{
    #echo "pilmap: " . $row['pilPk'] . " => " . $row['HpilPk'] . "<br>";
    $pilmap[$row['pilPk']] = $row;
}

# insert missing pilots
foreach ($pilmap as $pilPk => $row)
{
    if ($row['HpilPk'] == 0)
    {
        $fname = $row['fname'];
        $lname = $row['lname'];
        print "add missing pilot $fname $lname\n";
        $fai = $row['pilHGFA'];
        $natcode = $row['pilNationCode'];
        $oriPk = 2;
        if ($natcode != '')
        {
            $sql = "select O.* from tblOrigin O, tblNation N where O.natPk=N.natPk and N.natCode3='$natcode' order by oriPk limit 1";
//            $row = mysql_fetch_array($result, MYSQL_ASSOC);
            $row = mysqli_fetch_assoc($result);
            $oriPk = 0 + $row['oriPk'];
            if ($oriPk == 0)
            {
                $oriPk = 2;
            }
        }

        if ($row['sex'] == 'F')
        {
            $sex = 0;
        }
        else
        {
            $sex = 1;
        }

        $sql = "insert into hgfa_ladder.tblPilot (pilIDGlobal, pilFirstName, pilLastName, pilSex, oriPk, gliPk) values ('$fai', '$fname', '$lname', $sex, $oriPk, 267)";
//        $result = mysql_query($sql,$link) or die("Unable to insert pilot: " . mysql_error() . "\n");
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to insert pilot: ' . mysqli_connect_error());
//        $HpilPk = mysql_insert_id();
        $HpilPk = mysqli_insert_id($link);
        $pilmap[$pilPk]['HpilPk'] = $HpilPk;
    }
}

# insert new tasks / make tasPk map 
$taskmap = [];
$sql = "select comPk, tasPk, tasDate, tasName, tasResultsType, (tasDistance/1000) as tasDistance, tasSSDistance, tasSSOpen, tasSSClose, tasESClose, (tasTotalDistanceFlown/1000) as tasTotalDistanceFlown, tasQuality, tasPilotsLaunched, tasPilotsTotal, (tasMaxDistance/1000) as tasMaxDistance, tasFastestTime from xcdb.tblTask where comPk=$comPk";
//$result = mysql_query($sql,$link) or die("Unable to select tasks: " . mysql_error() . "\n");
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to select tasks: ' . mysqli_connect_error());
//while($row = mysql_fetch_array($result, MYSQL_ASSOC))
while ($row = mysqli_fetch_assoc($result))
{
    // make a tasPk map ..
    $taskmap[$row['tasPk']] = $row;
}


# delete all existing tasks related to this competition?
$sql = "delete from hgfa_ladder.tblTask where comPk=$HcomPk";
//$result = mysql_query($sql,$link) or die("Unable to delete old tasks: " . mysql_error() . "\n");
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to delete old tasks: ' . mysqli_connect_error());


$rowmap = array(
    'tasMaxDistance' => 'tasTopDistance',
    'tasFastestTime' => '-',
    'comPk' => $HcomPk,
    'tasPk' => '-'
    );

foreach ($taskmap as $tasPk => $row)
{
    $row['tasStartType'] = 'AIR';
    $row['tasResultsType'] = 'COMPUTE';
    if (0 + $row['tasFastestTime'] > 0)
    {
        $row['tasTopSpeed'] = $row['tasDistance'] * 3600 / $row['tasFastestTime'];
    }
    else
    {
        $row['tasTopSpeed'] = 0;
    }

    # topscore?
    $sql = "select max(tarScore) as maxScore from tblTaskResult where tasPk=$tasPk";
//    $result = mysql_query($sql,$link) or die("Unable to get max score " . mysql_error() . "\n");
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to get max score: ' . mysqli_connect_error());
//    $maxscore = mysql_result($result,0,0);
    $maxscore = mysqli_result($result,0,0);

    $row['tasTopScore'] = $maxscore;
    $row['tasTopOzScore'] = $maxscore;

    $sql = insert_map("hgfa_ladder.tblTask", $rowmap, $row);

//    $result = mysql_query($sql,$link) or die("Unable to insert tasks " . mysql_error() . "\n");
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to insert tasks: ' . mysqli_connect_error());
//    $HtasPk = mysql_insert_id();
    $HtasPk = mysqli_insert_id($link);

    $taskmap[$tasPk]['HtasPk'] = $HtasPk;
}


# TaskWaypoints / hgfa_ladder.tblTurnpoint
#CREATE TABLE tblTaskTurnpoint
#    ttpPk               Integer not null PRIMARY KEY auto_increment,
#    tasPk               Integer not null,
#    trnPk               Integer not null,
#    ttpNr               Integer not null,
#    ttpNrText           varchar(8),
#    ttpTimeGateType     Text,
#    ttpDistanceDiff     Double,
#    ttpDistanceTotal    Double,
#    ttpAngle            Double,
#    ttpCircle           Double
#CREATE TABLE tblTurnpoint
#    trnPk                           Integer not null PRIMARY KEY auto_increment,
#    trnID                           varchar(12),
#    trnName                         varchar(100),
#    trnAbbr                         varchar(40),
#    trnPositionType                 varchar(6),
#    trnPositionLatitudeDecimal      Double,
#    trnPositionLatitudeDirection    varchar(2),
#    trnPositionLatitudeDegree       Double,
#    trnPositionLatitudeMinute       Double,
#    trnPositionLatitudeSecond       Double,
#    trnPositionLongitudeDecimal     Double,
#    trnPositionLongitudeDirection   varchar(2),
#    trnPositionLongitudeDegree      Double,
#    trnPositionLongitudeMinute      Double,
#    trnPositionLongitudeSecond      Double,
#    trnPositionEastings             Double,
#    trnPositionNorthings            Double,
#    trnPositionAltitude             Double,
#    trnPositionMapZone              Integer,
#    geoPk                           Integer,
#    oriPk                           Integer

$taskkeys = array_keys($taskmap);
$taskvals = implode(",", $taskkeys);

$sql = "select * from tblTaskWaypoint T, tblRegionWaypoint R where T.rwpPk=R.rwpPk and T.tasPk in ($taskvals)";
//$result = mysql_query($sql,$link) or die("Unable to fetch waypoints: " . mysql_error() . "\n");
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to fetch waypoints: ' . mysqli_connect_error());
//while($row = mysql_fetch_array($result, MYSQL_ASSOC))
while ($row = mysqli_fetch_assoc($result))
{
    $taskpoints = $row;
}

# FIX this up.
#foreach ($taskpoints as $resPk => $row)
#{
#}

# delete all existing tasks related to this competition?
$sql = "delete from hgfa_ladder.tblResult where comPk=$HcomPk";
//$result = mysql_query($sql,$link) or die("Unable to delete old results: " . mysql_error() . "\n");
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to delete old results: ' . mysqli_connect_error());

# Actual results ..
if ($ctype == 'Team-RACE')
{
    $sql = "select TP.pilPk,T.tasPk,T.terResultType as tarResultType,T.terTurnpoints as tarTurnpoints,TIMESTAMPADD(SECOND,T.terSS,TK.tasDate) as tarSS,TIMESTAMPADD(SECOND,T.terES,TK.tasDate) as tarES,T.terPenalty as tarPenalty,T.terComment as tarComment,round(T.terScore) as tarScore,T.terPlace as tarPlace,T.terSpeed as tarSpeed,(T.terDistance/1000) as tarDistance,T.terArrival as tarArrival,T.terDeparture as tarDeparture,T.terSpeedScore as tarSpeedScore,T.terDistanceScore as tarDistanceScore,T.terLeadingCoeff as tarLeadingCoeff from xcdb.tblTeamResult T, xcdb.tblTeam TM, xcdb.tblTeamPilot TP, xcdb.tblTask TK where T.teaPk=TM.teaPk and TM.comPk=$comPk and TP.teaPk=TM.teaPk and TK.tasPk=T.tasPk and T.tasPk in (select tasPk from xcdb.tblComTaskTrack where comPk=$comPk)";
}
else
{
    $sql = "select TL.pilPk,T.tasPk,T.tarResultType,T.tarTurnpoints,TIMESTAMPADD(SECOND,T.tarSS,TK.tasDate) as tarSS,TIMESTAMPADD(SECOND,T.tarES,TK.tasDate) as tarES,T.tarPenalty,T.tarComment,round(T.tarScore) as tarScore,T.tarPlace,T.tarSpeed,(T.tarDistance/1000) as tarDistance,T.tarArrival,T.tarDeparture,T.tarSpeedScore,T.tarDistanceScore,T.tarLeadingCoeff from xcdb.tblTaskResult T, xcdb.tblTrack TL, xcdb.tblTask TK where TL.traPk=T.traPk and TK.tasPk=T.tasPk and T.tasPk in (select tasPk from xcdb.tblComTaskTrack where comPk=$comPk)";
}
//$result = mysql_query($sql,$link) or die("Unable query task results: " . mysql_error() . "\n");
$result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable query task results: ' . mysqli_connect_error());
$taskresult = [];
$count = 1;
//while($row = mysql_fetch_array($result, MYSQL_ASSOC))
while ($row = mysqli_fetch_assoc($result))
{
    $taskresult[$count++] = $row;
}

$rowmap = array(
    'tarPk' => '-',
    'tarTurnpoints' => 'resTurnpointsReached',
    'tarPenalty' => 'resPenaltyValue',
    'tarComment' => 'resComment',
    'tarSS' => 'resSSTime',
    'tarES' => 'resESTime',
    'tarSpeed' => 'resSpeed',
    'tarDistance' => 'resDistance',
    'tarArrival' => 'resArrivalScore',
    'tarDeparture' => 'resDepartureScore',
    'tarSpeedScore' => 'resSpeedScore',
    'tarDistanceScore' => 'resDistanceScore',
    'tarScore' => 'resScore',
    'tarPlace' => 'resPlace',
    'tarResultType' => 'resStatus',
    'tarLeadingCoeff' => 'resLeadingCoeff'
);
#print_r($taskmap);
foreach ($taskresult as $resPk => $row)
{
    echo "add result for: " . $row['pilPk'] . "<br>";
    $row['pilPk'] = $pilmap[$row['pilPk']]['HpilPk'];
    $row['tasPk'] = $taskmap[$row['tasPk']]['HtasPk'];
    $row['comPk'] = $HcomPk;
    if (0 + $row['tarGoal'] > 0)
    {
        $row['resReachedES'] = 1;
    }
    else
    {
        $row['resReachedES'] = 0;
    }
    // Need to convert tasPks & pilPks
    $sql = insert_map("hgfa_ladder.tblResult", $rowmap, $row);

    print $sql . "\n";
//    $result = mysql_query($sql,$link) or die("Unable to insert result " . mysql_error() . "\n");
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Unable to insert result: ' . mysqli_connect_error());
}

?>

