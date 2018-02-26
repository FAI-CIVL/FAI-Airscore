<?php
require 'authorisation.php';
require 'hc.php';
require 'format.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

function piltracktable($link, $sort, $order, $start, $pilot)
{
    //<div id=\"comments\"><ol>";

    $count = $start+1;
    $long = array();
//    $sql = "select T.*, P.*, CTT.*, L.* from tblTrack T, tblPilot P, tblComTaskTrack CTT, tblWaypoint W, tblLaunchSite L where W.wptPosition=0 and (abs(W.wptLatDecimal-L.lauLatDecimal)+abs(W.wptLongDecimal-L.lauLongDecimal)) < 1.0 and T.traPk=W.traPk and CTT.traPk=T.traPk and T.pilPk=P.pilPk $order";
    $sql = "select T.*, P.*, CTT.*, L.* from tblTrack T, tblPilot P, tblComTaskTrack CTT, tblWaypoint W left outer join tblLaunchSite L on (abs(W.wptLatDecimal-L.lauLatDecimal)+abs(W.wptLongDecimal-L.lauLongDecimal)) < 0.2 where W.wptPosition=0 and T.traPk=W.traPk and CTT.traPk=T.traPk and T.pilPk=P.pilPk $sort group by T.traPk $order";
//    $result = mysql_query($sql,$link) or die("Invalid track table " . mysql_error());
    $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Invalid track table ' . mysqli_connect_error());
//    $num = mysql_num_rows($result);
    $num = mysqli_num_rows($result);
//    while ($row = mysql_fetch_array($result))
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $id = $row['traPk'];
        $dist = round($row['traLength']/1000,2);
        $comPk = $row['comPk'];
        $pilPk = $row['pilPk'];
        $ghour = floor($row['traDuration'] / 3600);
        $gmin = floor($row['traDuration'] / 60) - $ghour*60;
        if ($pilot > 0)
        {
            $name = $row['lauLaunch'] . ', ' . $row['lauRegion'];
            #$long[] = array ("$count.", "<a href=\"tracklog_map.php?trackid=$id&comPk=$comPk\">$dist kms</a>", substr($row['traStart'],0,10), sprintf("%02d:%02d",$ghour,$gmin), "<a href=\"index.php?pil=$pilPk\">$name<a>");
            $long[] = array (substr($row['traStart'],0,10), "<a href=\"tracklog_map.php?trackid=$id&comPk=$comPk\">$dist kms</a>", 
                    sprintf("%02d:%02dh",$ghour,$gmin), "<i>".$row['traGlider']."</i>", $name);
        } 
        $count++;
    }
    echo ftable($long, 'cellspacing="3" alternate-colours="yes"', '', '');
    return $num;
}

$link = db_connect();
$order = reqsval('order');
if (!($order == 'long' || $order == 'recent' || $order == 'best'
        || $order == 'rlong' || $order == 'rrecent' || $order == 'rbest'))
{
    $order = 'recent';
}
$pilot = reqival('pil');
$comp = reqival('comPk');
$start = reqival('start');
if ($start < 0)
{
    $start = 0;
}
$comstr = '';
$comclause = '';

$title = 'highcloud.net';
if ($comp > 0)
{
    $sql = "select * from tblCompetition C where comPk=$comp";
//    $result = mysql_query($sql,$link);
    $result = mysqli_query($link, $sql);
//    if ($row = mysql_fetch_array($result))
    if ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $title = $row['comName'];
    }
    $comstr = "and CTT.comPk=$comp ";
    $comclause = "comPk=$comp&";
}

$piln = '';
if ($pilot > 0)
{
    $sql = "select P.pilFirstName, P.pilLastName from tblPilot P where P.pilPk=$pilot";
//    $result = mysql_query($sql,$link);
    $result = mysqli_query($link, $sql);
//    if ($row = mysql_fetch_array($result))
    if ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $name = $row['pilFirstName'] . ' ' . $row['pilLastName'];
        $title = "$name @ $title";
    }
    $pilstr = "and P.pilPk=$pilot ";
    $piln = "pil=$pilot&";
}
else
{
    $pilstr = '';
}
hcheader($title, 0, "");
echo "<div id=\"content\">";
echo "<div id=\"text\">";

$lhead = "Recent";
$clause = "by T.traStart desc";
if ($order == 'long')
{
    $lhead = "Longest";
    $clause = "by T.traLength desc";
}
elseif ($order == 'best')
{
    $lhead = "Best";
    $clause = "by T.traScore desc";
}
elseif ($order == 'rrecent')
{
    $lhead = "Date";
    $clause = "by T.traStart";
}
elseif ($order == 'rlong')
{
    $lhead = "Longest";
    $clause = "by T.traLength";
}
elseif ($order == 'rbest')
{
    $lhead = "Best";
    $clause = "by T.traScore";
}
$num = 25;
$sort = "${comstr}${pilstr}";
$order = "order $clause limit $start,$num";
echo "<h1><span>$lhead " . ($start+1) . "-" . ($start+$num) . "</span></h1>\n";
$numout = piltracktable($link, $sort, $order, $start, $pilot); 
if ($start > 1)
{
    echo "<b class=\"left\"><a href=\"pilot.php?${comclause}${piln}order=$order&start=" . ($start-$num) . "\">Prev $num</a></b>\n";
}
if ($numout == $num)
{
    echo "<b class=\"right\"><a href=\"pilot.php?${comclause}${piln}order=$order&start=" . ($start+$num) . "\">Next $num</a></b>\n";
}

echo "</div>";
//echo "<div id=\"image\"><img src=\"images/pilots.jpg\" alt=\"Pilots Flying\"/></div>";
echo "<div id=\"sideBar\">";
hcregion($link);
hcopencomps($link);
hcclosedcomps($link);
echo "</div>";
hcimage($link,$comp);
hcfooter();
?>
  </div>
</body>
</html>
