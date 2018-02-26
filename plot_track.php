<?php
require_once 'authorisation.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

function get_track_body($trackid,$interval)
{
    $link = db_connect();

    $body = [];
    $ret = [];
    
    // track info ..
    $offset = 0;
    $sql = "SELECT T.*, P.*, TR.*, TK.* FROM tblPilot P, tblTrack T 
            left outer join tblTaskResult TR on TR.traPk=T.traPk 
            left outer join tblTask TK on TK.tasPk=TR.tasPk 
            where T.pilPk=P.pilPk and T.traPk=$trackid limit 1";
//    $result = mysql_query($sql,$link) or die('Track info query failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Track info query failed: ' . mysqli_connect_error());
//    if ($row = mysql_fetch_array($result, MYSQL_ASSOC))
    if ($row = mysqli_fetch_assoc($result))
    {
        $name = $row['pilFirstName'] . " " . $row['pilLastName'];
        $date = $row['traDate'];
        $glider = $row['traGlider'];
        $tasPk = $row['tasPk'];
        $comPk = $row['comPk'];
        $tasname = $row['tasName'];
        $comment = $row['tarComment'];
        $turnpoints = $row['tarTurnpoints'];
        $gtime = 0;
        $ggoal = 0;
        if ($glider == '')
        {
            $glider = 'unknown glider';
        }
        $gtime = $row['traDuration'];
        $dist = round($row['traLength'] / 1000, 2);
        $date = $row['traStart'];
        if ($tasPk > 0)
        {
            if ($row['tarES'] > 0)
            {
                $ggoal = $row['tarES'] - $row['tarSS'];
                $gtime = $ggoal;
            }
            $dist = round($row['tarDistance'] / 1000, 2);
            $date = $row['tasDate'];

            $dt1 = new DateTime($row["traDate"]);
            $dt2 = new DateTime($row["tasDate"]);
            if ($dt1 < $dt2) 
            { 
                $offset = -86400; 
            }
        }
        $ghour = floor($gtime / 3600);
        $gmin = floor($gtime / 60) - $ghour*60;
        $gsec = $gtime % 60;

        $body['name'] = $name;
        $body['date'] = $date;
        $body['startdate'] = $row["traDate"];
        $body['dist'] = $dist;
        $body['tasPk'] = $tasPk;    # get task name ...
        if ($ggoal && ($gtime > 0))
        {
            $body['goal'] = sprintf("%d:%02d:%02d", $ghour,$gmin,$gsec);
        }
        else
        {
            $body['duration'] = sprintf("%02d:%02d:%02d", $ghour,$gmin,$gsec);
        }
        $body['glider'] = $glider;
        $body['comment'] = $comment;
        $body['initials'] = substr($row['pilFirstName'],0,1) . substr($row['pilLastName'],0,1);

        $sql = "select C.comClass from tblCompetition C, tblComTaskTrack T where C.comPk=T.comPk and T.traPk=$trackid";
//        $result = mysql_query($sql,$link) or die('Com class query failed: ' . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Com class query failed: ' . mysqli_connect_error());
//        $srow = mysql_fetch_array($result, MYSQL_ASSOC);
        $srow = mysqli_fetch_assoc($result);
        if ($srow['comClass'] == 'sail')
        {
            $body['class'] = 'sail';
        }
        else
        {
            $body['class'] = 'pger';
        }
    }

    if ($interval < 1)
    {
        $interval = 5;
    }
    if ($interval == 1)
    {
        $sql = "SELECT *, trlTime as bucTime FROM tblTrackLog where traPk=$trackid order by trlTime";
    }
    else
    {
        $sql = "SELECT *, trlTime div $interval as bucTime FROM tblTrackLog where traPk=$trackid group by trlTime div $interval order by trlTime";
        $offset = (int) ($offset / $interval);
    }
    
    // Get some track points
//    $result = mysql_query($sql,$link);
    $result = mysqli_query($link, $sql);
//    while($row = mysql_fetch_array($result, MYSQL_ASSOC))
    while ($row = mysqli_fetch_assoc($result))
    {
        $bucTime = $offset + $row['bucTime'];
        $lasLat = 0.0 + $row['trlLatDecimal'];
        $lasLon = 0.0 + $row['trlLongDecimal'];
        $lasAlt = 0 + $row['trlAltitude'];
        $ret[] = array( $bucTime, $lasLat, $lasLon, $lasAlt );
    }
    $body['track'] = $ret;

    return $body;
}
function get_track($trackid,$interval)
{
    $body = get_track_body($trackid, $interval);
    $jret = json_encode($body);
    return $jret;
}
function qckdist2($p1,$p2)
{
    # array( $bucTime, $lasLat, $lasLon, $lasAlt );
    $x = ($p2[1] - $p1[1]);
    $y = ($p2[2] - $p1[2]) * cos(($p1[1] + $p2[1])/2);

    $m = 6371009.0 * sqrt($x*$x + $y*$y);
    #print "qckdist2=$m (no sqrt=)",6371009.0*($x*$x+$y*$y), "\n";
    return $m;
}
function get_track_speed($trackid,$interval)
{
    $body = get_track_body($trackid, $interval);
    $track = $body['track'];
    $max = sizeof($track);
    $track[0][3] = 0;
    $nsp = 0;
    for ($i = 1; $i < $max; $i++)
    {
        $dst = qckdist2($track[$i], $track[$i-1]);
        $tm = ($track[$i][0] - $track[$i-1][0]) * $interval * 5;
        if ($tm > 0)
        {
            // knots ..
            $sp = ($dst / $tm) * 1.94384449;
            $nsp = ($sp * 0.50 + $nsp * 0.50);
        }
        $track[$i][3] = $nsp;
    }
    $body['track'] = $track;
    $jret = json_encode($body);
    return $jret;
}
function get_task($tasPk, $trackid)
{
    $link = db_connect();

    $res = [];

    // task info ..
    $sql = "SELECT T.*,W.* FROM tblTaskWaypoint T, tblRegionWaypoint W where T.tasPk=$tasPk and W.rwpPk=T.rwpPk order by T.tawNumber";
    $ret = [];
//    $result = mysql_query($sql,$link) or die('Task info query failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task info query failed: ' . mysqli_connect_error());
//    while ($row = mysql_fetch_array($result, MYSQL_ASSOC))
    while ($row = mysqli_fetch_assoc($result))
    {
    
        $lasLat = 0.0 + $row['rwpLatDecimal'];
        $lasLon = 0.0 + $row['rwpLongDecimal'];
        $cname = $row["rwpName"];
        $crad = $row["tawRadius"];
        $tawType = $row["tawType"];
        $tawPk = $row["tawPk"];
        $ret[] = array( $lasLat, $lasLon, $cname, $crad, $tawType, $tawPk );
    }

    $turnpoints = 0;
    $merge = 0;
    if ($trackid > 0)
    {
        // select * from tblTaskAward where traPk=$trackid
//        $sql = "SELECT T.*,W.* FROM tblTaskWaypoint T 
//                left join tblRegionWaypoint W on T.rwpPk=W.rwpPk
//                left outer join on tblTaskAward TA on TA.traPk=$trackid
//                where T.tasPk=$tasPk and W.rwpPk=T.rwpPk order by T.tawNumber";
//        $ret = [];
//        $result = mysql_query($sql,$link) or die('Task info query failed: ' . mysql_error());
//        while ($row = mysql_fetch_array($result, MYSQL_ASSOC))
//        {
//        
//            $lasLat = 0.0 + $row['rwpLatDecimal'];
//            $lasLon = 0.0 + $row['rwpLongDecimal'];
//            $cname = $row["rwpName"];
//            $crad = $row["tawRadius"];
//            $tawType = $row["tawType"];
//            $tawPk = $row["tawPk"];
//            $awarded = $row["tadPk"];
//            $awardtm = $row["tarTime"];
//            $ret[] = array( $lasLat, $lasLon, $cname, $crad, $tawType, $tawPk );
//        }

        $sql = "select tarTurnpoints from tblTaskResult where traPk=$trackid";
//        $result = mysql_query($sql,$link) or die('Task turnpoints failed: ' . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task turnpoints failed: ' . mysqli_connect_error());
//        $turnpoints = mysql_result($result, 0, 0);
        $turnpoints = mysqli_result($result, 0, 0);

        $sql = "select T2.traPk from tblTrack T1, tblTrack T2 where T2.pilPk=T1.pilPk and T2.traStart between date_sub(T1.traStart, interval 6 hour) and date_add(T1.traStart, interval 6 hour) and T1.traPk=$trackid and T2.traPk<>T1.traPk";
//        $result = mysql_query($sql,$link) or die('Duplicate track select failed: ' . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Duplicate track select failed: ' . mysqli_connect_error());
//        if (mysql_num_rows($result) > 0)
        if (mysqli_num_rows($result) > 0)
        {
//            $merge = mysql_result($result, 0, 0);
            $merge = mysqli_result($result, 0, 0);
        }
    }

    $res['tasPk'] = $tasPk;
    $res['task'] = $ret;
    $res['turnpoints']= $turnpoints;
    $res['merge']= $merge;
    $jret = json_encode($res);
    return $jret;
}
function get_region($regPk, $trackid)
{
    $link = db_connect();

    // task info ..
    if ($trackid > 0)
    {
        $sql = "SELECT max(T.trlLatDecimal) as maxLat, max(T.trlLongDecimal) as maxLong, min(T.trlLatDecimal) as minLat, min(T.trlLongDecimal) as minLong from tblTrackLog T where T.traPk=$trackid";
//        $result = mysql_query($sql,$link) or die('Track query failed: ' . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Track query failed: ' . mysqli_connect_error());
//        $row = mysql_fetch_array($result, MYSQL_ASSOC);
        $row = mysqli_fetch_assoc($result);
    
        $maxLat = $row['maxLat'] + 0.02;
        $maxLong = $row['maxLong'] + 0.02;
        $minLat = $row['minLat'] - 0.02;
        $minLong = $row['minLong'] - 0.02;
        $crad = 400;
    
        $sql = "SELECT W.* FROM tblRegionWaypoint W where W.regPk=$regPk and W.rwpLatDecimal between $minLat and $maxLat and W.rwpLongDecimal between $minLong and $maxLong";
    }
    else
    {
        $crad = 0;
        $sql = "SELECT W.* FROM tblRegionWaypoint W where W.regPk=$regPk";
    }
//    $result = mysql_query($sql,$link) or die('Region waypoint query failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Region waypoint query failed: ' . mysqli_connect_error());
    $ret = [];
//    while ($row = mysql_fetch_array($result, MYSQL_ASSOC))
    while ($row = mysqli_fetch_assoc($result))
    {
    
        $lasLat = 0.0 + $row['rwpLatDecimal'];
        $lasLon = 0.0 + $row['rwpLongDecimal'];
        $cname = $row["rwpName"];
        $ret[] = array( $lasLat, $lasLon, $cname, $crad, '', 0 );
    }

    $res = [];
    $res['region'] = $ret;
    $jret = json_encode($res);
    return $jret;
}
function award_waypoint($tasPk, $tawPk, $trackid, $wptime)
{
    // Did we award from turnpoints?
    // FIX: check auth?
    $usePk = check_auth('system');
    $link = db_connect();
    $comPk = reqival('comPk');
    $isadmin = is_admin('admin',$usePk,$comPk);
    if (!$isadmin) 
    {
        return 0;
    }

    $goaltime = 0;

    if (strchr($wptime, ":"))
    {
        $timarr = split(':', $wptime);
        $goaltime = $timarr[0] * 3600 + $timarr[1] * 60 + $timarr[2];
    }

    # Award the waypoint ..
    $sql = "insert into tblTaskAward (tawPk, traPk, tadTime) values ($tawPk, $trackid, $goaltime)";
//    $result = mysql_query($sql,$link) or die('Award waypoint failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Award waypoint failed: ' . mysqli_connect_error());
    $sql = "select tasPk from tblComTaskTrack where traPk=$trackid";
//    $result = mysql_query($sql,$link) or die('Selec task failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Selec task failed: ' . mysqli_connect_error());
//    $tasPk = mysql_result($result, 0, 0);
    $tasPk = mysqli_result($result, 0, 0);

    # Re-verify with new awarded waypoint(s)
    $out = '';
    $retv = 0; 
    exec(BINDIR . "track_verify_sr.pl $trackid $tasPk", $out, $retv);
    return 0;
}
function get_track_wp($trackid)
{
    $link = db_connect();

    $sql = "SELECT * FROM tblWaypoint where traPk=$trackid order by wptTime";
    $ret = [];
//    $result = mysql_query($sql,$link) or die('Task info query failed: ' . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Task info query failed: ' . mysqli_connect_error());
//    while ($row = mysql_fetch_array($result, MYSQL_ASSOC))
    while ($row = mysqli_fetch_assoc($result))
    {
    
        $lasLat = 0.0 + $row['wptLatDecimal'];
        $lasLon = 0.0 + $row['wptLongDecimal'];
        $ret[] = array( $lasLat, $lasLon );
    }

    // task info ..
    $jret = json_encode($ret);
    return $jret;
}

sajax_init();
sajax_export("get_task");
sajax_export("get_track");
sajax_export("get_track_speed");
sajax_export("get_region");
sajax_export("get_track_wp");
sajax_export("award_waypoint");
sajax_handle_client_request();
?>

