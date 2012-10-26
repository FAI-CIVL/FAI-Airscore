<?php
require_once 'authorisation.php';
require_once 'Sajax.php';
function get_track($trackid,$interval)
{
    $link = db_connect();

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
    }
    
    $body = array();
    $ret = array();
    
    $result = mysql_query($sql,$link);
    while($row = mysql_fetch_array($result))
    {
    
        $bucTime = 0 + $row['bucTime'];
        $lasLat = 0.0 + $row['trlLatDecimal'];
        $lasLon = 0.0 + $row['trlLongDecimal'];
        $lasAlt = 0 + $row['trlAltitude'];
        $ret[] = array( $bucTime, $lasLat, $lasLon, $lasAlt );
    }
    $body['track'] = $ret;

    // track info ..
    $sql = "SELECT T.*, P.*, TR.*, TK.* FROM tblPilot P, tblTrack T 
            left outer join tblTaskResult TR on TR.traPk=T.traPk 
            left outer join tblTask TK on TK.tasPk=TR.tasPk 
            where T.pilPk=P.pilPk and T.traPk=$trackid limit 1";
    $result = mysql_query($sql,$link) or die('Track info query failed: ' . mysql_error());
    if ($row = mysql_fetch_array($result))
    {
        $name = $row['pilFirstName'] . " " . $row['pilLastName'];
        $date = $row['traDate'];
        $glider = $row['traGlider'];
        $tasPk = $row['tasPk'];
        $tasname = $row['tasName'];
        $comment = $row['tarComment'];
        if ($tasPk > 0)
        {
            $date = $row['tasDate'];
        }
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
        }
        $ghour = floor($gtime / 3600);
        $gmin = floor($gtime / 60) - $ghour*60;
        $gsec = $gtime % 60;

        $body['name'] = $name;
        $body['date'] = $date;
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
    }

    
    $jret = json_encode($body);
    return $jret;
}
function get_task($tasPk, $trackid)
{
    $link = db_connect();

    // task info ..
    $sql = "SELECT T.*,W.* FROM tblTaskWaypoint T, tblRegionWaypoint W where T.tasPk=$tasPk and W.rwpPk=T.rwpPk order by T.tawNumber";
    $ret = array();
    $result = mysql_query($sql,$link) or die('Task info query failed: ' . mysql_error());
    while ($row = mysql_fetch_array($result))
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
    if ($trackid > 0)
    {
        $sql = "select tarTurnpoints from tblTaskResult where traPk=$trackid";
        $result = mysql_query($sql,$link) or die('Task turnpoints failed: ' . mysql_error());
        $turnpoints = mysql_result($result, 0, 0);
    }

    $res = array();
    $res['task'] = $ret;
    $res['turnpoints']= $turnpoints;
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
        $result = mysql_query($sql,$link) or die('Track query failed: ' . mysql_error());
        $row = mysql_fetch_array($result);
    
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
    $result = mysql_query($sql,$link) or die('Region waypoint query failed: ' . mysql_error());
    $ret = array();
    while ($row = mysql_fetch_array($result))
    {
    
        $lasLat = 0.0 + $row['rwpLatDecimal'];
        $lasLon = 0.0 + $row['rwpLongDecimal'];
        $cname = $row["rwpName"];
        $ret[] = array( $lasLat, $lasLon, $cname, $crad, '', 0 );
    }

    $res = array();
    $res['region'] = $ret;
    $jret = json_encode($res);
    return $jret;
}
function award_waypoint($tawPk, $trackid, $wptime)
{
    // Did we award from turnpoints?
    // FIX: check auth?
    $link = db_connect();
    $usePk = 0; //check_auth('system');
    $comPk = intval($_REQUEST['comPk']);
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
    $result = mysql_query($sql,$link) or die('Award waypoint failed: ' . mysql_error());
    $sql = "select tasPk from tblComTaskTrack where traPk=$trackid";
    $result = mysql_query($sql,$link) or die('Selec task failed: ' . mysql_error());
    $tasPk = mysql_result($result, 0, 0);

    # Re-verify with new awarded waypoint(s)
    $out = '';
    $retv = 0; 
    exec( BINDIR . "track_verify.pl $trackid $tasPk", $out, $retv);
    return 0;
}
function get_track_wp($trackid)
{
    $link = db_connect();

    $sql = "SELECT * FROM tblWaypoint where traPk=$trackid order by wptTime";
    $ret = array();
    $result = mysql_query($sql,$link) or die('Task info query failed: ' . mysql_error());
    while ($row = mysql_fetch_array($result))
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
sajax_export("get_region");
sajax_export("get_track_wp");
sajax_export("award_waypoint");
sajax_handle_client_request();
?>

