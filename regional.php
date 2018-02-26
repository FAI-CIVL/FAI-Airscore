<?php
    require 'authorisation.php';
    require 'hc.php';
    require 'format.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

    function tracktable($link, $lat, $lon, $order, $start)
    {
        //<div id=\"comments\"><ol>";

        $count = $start+1;
        $long = [];
        $sql = "select T.*, P.*, CTT.* from tblTrack T, tblPilot P, tblComTaskTrack CTT, tblWaypoint W where W.wptPosition=0 and (abs(W.wptLatDecimal-$lat)+abs(W.wptLongDecimal-$lon)) < 1.0 and T.traPk=W.traPk and CTT.traPk=T.traPk and T.pilPk=P.pilPk $order";
//        $result = mysql_query($sql,$link) or die("Invalid track table " . mysql_error());
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Invalid track table ' . mysqli_connect_error());
//        $num = mysql_num_rows($result);
        $num = mysqli_num_rows($result);
//        while($row = mysql_fetch_array($result))
        while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
        {
            $id = $row['traPk'];
            $dist = round($row['traLength']/1000,2);
            $name = $row['pilFirstName'] . ' ' . $row['pilLastName'];
            $comPk = $row['comPk'];
            $pilPk = $row['pilPk'];
            $long[] = array ("$count.", "<a href=\"tracklog_map.php?trackid=$id&comPk=$comPk\">$dist kms</a>", substr($row['traStart'], 0, 10), "<a href=\"index.php?pil=$pilPk\">$name</a>");
            $count++;
        }
        echo ftable($long, '', '', '');
        return $num;
    }


    $link = db_connect();
    $regPk = reqival('regPk');
    $order = reqsval('order');
    $start = reqival('start');
    $pilot = reqival('pil');
    $sql = "select RW.*,R.* from tblRegionWaypoint RW, tblRegion R where R.regPk=$regPk and RW.rwpPk=R.regCentre";
//    $result = mysql_query($sql,$link);
    $result = mysqli_query($link, $sql);
//    if ($row = mysql_fetch_array($result))
    if ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $lat = $row['rwpLatDecimal'];
        $lon = $row['rwpLongDecimal'];
        $title = $row['regDescription'];
    }
    if ($pilot > 0)
    {
        $sql = "select P.pilFirstName, P.pilLastName from tblPilot P where P.pilPk=$pilot";
//        $result = mysql_query($sql,$link);
        $result = mysqli_query($link, $sql);
//        if ($row = mysql_fetch_array($result))
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

    if ($order == 'long')
    {
        $num = 25;
        $sort = "${pilstr}order by T.traLength desc limit $start,$num";
        echo "<h1><span>Longest " . ($start+1) . "-" . ($start+$num) . "</span></h1>\n";
        if (tracktable($link, $lat, $lon, $sort, $start) == $num)
        {
            echo "<b class=\"right\"><a href=\"regional.php?regPk=$regPk&order=$order&start=" . ($start+$num) . "\">Next 25</a></b>\n";
        }
    }
    elseif ($order == 'recent')
    {
        $num = 25;
        $sort = "${pilstr}order by T.traStart desc limit $start,$num";
        echo "<h1><span>Recent " . ($start+1) . "-" . ($start+$num) . "</span></h1>\n";
        if (tracktable($link, $lat, $lon, $sort, $start) == $num)
        {
            echo "<b class=\"right\"><a href=\"regional.php?regPk=$regPk&order=$order&start=" . ($start+$num) . "\">Next 25</a></b>\n";
        }
    }
    else
    {
        $num = 10;
        $sort = "${pilstr}order by T.traLength desc limit $num";
        echo "<h1><span>Longest 10</span></h1>\n";
        if (tracktable($link, $lat, $lon, $sort, $start) == $num)
        {
            echo "<b class=\"right\"><a href=\"regional.php?regPk=$regPk&order=long&start=" . ($start+$num) . "\">Next 25</a></b>\n";
        }

        $sort = "${pilstr}order by T.traStart desc limit $num";
        echo "<h1><span>Recent 10</span></h1>\n";
        if (tracktable($link, $lat, $lon, $sort, $start) == $num)
        {
            echo "<b class=\"right\"><a href=\"regional.php?regPk=$regPk&order=recent&start=" . ($start+$num) . "\">Next 25</a></b>\n";
        }
    }

    //echo "<img src=\"images/comment_bg.gif\" alt=\"comment bottom\"/>\n";
    //  </div>

    echo "</div>\n";

    echo "<div id=\"sideBar\">";
    hcregion($link);
    hcopencomps($link);
    hcclosedcomps($link);

    echo "</div>";
    echo "<div id=\"image\"><img src=\"images/pilots.jpg\" alt=\"Pilots Flying\"/></div>";
?>

<?php
    hcfooter();
?>
  </div>
</body>
</html>
