<?php
require 'authorisation.php';
require 'hc.php';
require 'format.php';

    function tracktable($link, $order, $start, $pilot)
    {
        //<div id=\"comments\"><ol>";

        $count = $start+1;
        $long = [];
        if ($pilot > 0)
        {
            $sql = "select T.*, P.*, CTT.*, L.* from tblTrack T, tblPilot P, tblComTaskTrack CTT, tblWaypoint W, tblLaunchSite L where W.wptPosition=0 and (abs(W.wptLatDecimal-L.lauLatDecimal)+abs(W.wptLongDecimal-L.lauLongDecimal)) < 1.0 and T.traPk=W.traPk and CTT.traPk=T.traPk and T.pilPk=P.pilPk $order";
            $sql = "select T.*, P.*, CTT.*, L.* from tblTrack T, tblPilot P, tblComTaskTrack CTT, tblWaypoint W left outer join tblLaunchSite L on (abs(W.wptLatDecimal-L.lauLatDecimal)+abs(W.wptLongDecimal-L.lauLongDecimal)) < 1.0 where W.wptPosition=0 and T.traPk=W.traPk and CTT.traPk=T.traPk and T.pilPk=P.pilPk $order";
        }
        else
        {
            $sql = "select T.*, P.*, CTT.* from tblTrack T, tblPilot P, tblComTaskTrack CTT where CTT.traPk=T.traPk and T.traLength > 0 and T.pilPk=P.pilPk $order";
        }
        $result = mysql_query($sql,$link) or die("Invalid track table " . mysql_error());
        $num = mysql_num_rows($result);
        while($row = mysql_fetch_array($result))
        {
            $id = $row['traPk'];
            $dist = round($row['traLength']/1000,2);
            $comPk = $row['comPk'];
            $pilPk = $row['pilPk'];
            if ($pilot > 0)
            {
                $name = $row['lauLaunch'] . ', ' . $row['lauRegion'];
                $long[] = array ("$count.", "<a href=\"tracklog_map.php?trackid=$id&comPk=$comPk\">$dist kms</a>", substr($row['traStart'],0,10), "<a href=\"index.php?pil=$pilPk\">$name<a>");
            } 
            else
            {
                $name = $row['pilFirstName'] . ' ' . $row['pilLastName'];
                $long[] = array ("$count.", "<a href=\"tracklog_map.php?trackid=$id&comPk=$comPk\">$dist kms</a>", substr($row['traStart'],0,10), "<a href=\"index.php?pil=$pilPk\">$name<a>");
            }
            $count++;
        }
        echo ftable($long, '', '', '');
        return $num;
    }

    $link = db_connect();
    $order = reqsval('order');
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
        $result = mysql_query($sql,$link);
        if ($row = mysql_fetch_array($result))
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
        $result = mysql_query($sql,$link);
        if ($row = mysql_fetch_array($result))
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

    if ($order == 'long' || $order == 'recent')
    {
        $lhead = "Recent";
        $clause = "by T.traStart desc";
        if ($order == 'long')
        {
            $lhead = "Longest";
            $clause = "by T.traLength desc";
        }
        $num = 25;
        $sort = "${comstr}${pilstr}order $clause limit $start,$num";
        echo "<h1><span>$lhead " . ($start+1) . "-" . ($start+$num) . "</span></h1>\n";
        $numout = tracktable($link, $sort, $start, $pilot); 
        if ($start > 1)
        {
            echo "<b class=\"left\"><a href=\"index.php?${comclause}${piln}order=$order&start=" . ($start-$num) . "\">Prev 25</a></b>\n";
        }
        if ($numout == $num)
        {
            echo "<b class=\"right\"><a href=\"index.php?${comclause}${piln}order=$order&start=" . ($start+$num) . "\">Next 25</a></b>\n";
        }
    }
    else
    {
        $num = 10;
        $sort = "${comstr}${pilstr}order by T.traLength desc limit $num";
        echo "<h1><span>Longest 10</span></h1>\n";
        if (tracktable($link, $sort, $start, $pilot) == $num)
        {
            echo "<b class=\"right\"><a href=\"index.php?${comclause}${piln}order=long&start=" . ($start+$num) . "\">Next 25</a></b>\n";
        }

        $sort = "${comstr}${pilstr}order by T.traStart desc limit $num";
        echo "<h1><span>Recent 10</span></h1>\n";
        if (tracktable($link, $sort, $start, $pilot) == $num)
        {
            echo "<b class=\"right\"><a href=\"index.php?${comclause}${piln}order=recent&start=" . ($start+$num) . "\">Next 25</a></b>\n";
        }
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
