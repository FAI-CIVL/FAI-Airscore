<?php
require_once 'authorisation.php';

//
// All mysql_ are deprecated, need to change all to mysqli_ functions. I leave all here than we will clean up
//

function printhd($title)
{
echo "
<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\" \"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">
<html xmlns=\"http://www.w3.org/1999/xhtml\">
<head>
  <title>$title</title>
  <meta http-equiv=\"content-type\" content=\"application/xhtml+xml; charset=UTF-8\" />
  <meta name=\"author\" content=\"highcloud.net\" />
  <meta name=\"description\" content=\"Printable highcloud web page\" />
  <link rel=\"stylesheet\" type=\"text/css\" href=\"printer.css\" media=\"screen\" />
  <link rel=\"stylesheet\" type=\"text/css\" href=\"printer.css\" media=\"print\" />
</head>
<body>
";
}
function hcheader($title,$active,$titler,$css="green800.css")
{
echo "
<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\" \"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">
<html xmlns=\"http://www.w3.org/1999/xhtml\">
<!--
 ____________________________________________________________
|                                                            |
|    DESIGN + Pat Heard { http://fullahead.org }             |
|      DATE + 2005.11.30                                     |
| COPYRIGHT + Free use if this notice is left in place       |
|____________________________________________________________|
-->
<head>
  <title>$title</title>
  <meta http-equiv=\"content-type\" content=\"application/xhtml+xml; charset=UTF-8\" />
  <meta name=\"author\" content=\"fullahead.org\" />
  <meta name=\"keywords\" content=\"Open Web Design, OWD, Free Web Template, Greenery, Fullahead\" />
  <meta name=\"description\" content=\"A free web template designed by Fullahead.org and hosted on OpenWebDesign.org\" />
  <meta name=\"robots\" content=\"index, follow, noarchive\" />
  <meta name=\"googlebot\" content=\"noarchive\" />
  <link rel=\"stylesheet\" type=\"text/css\" href=\"$css\" media=\"screen\" />
  <link rel=\"stylesheet\" type=\"text/css\" href=\"printer.css\" media=\"print\" />
</head>
<body>
";
    hcheadbar($title,$active,$titler);
}
function hcheadbar($title,$active,$titler)
{
echo "
  <div id=\"header\">
    <div id=\"menu\">
      <ul>\n
";
    $clarr = array     
    (
        '', '', '', '', '', '', '', ''
    );
    $clarr[$active] = ' class="active"';
    $comPk=reqival('comPk');
    echo "<li><a href=\"index.php?comPk=$comPk\" title=\"About\"" . $clarr[0]. ">About</a></li>\n";
    if (!$comPk)
    {
        echo "<li><a href=\"ladder.php\" title=\"Ladders\"" . $clarr[1] . ">Ladders</a></li>\n";
        $comPk = 1;
    }
    echo "<li><a href=\"submit_track.php?comPk=$comPk\" title=\"Submit\"" . $clarr[1] . ">Submit</a></li>\n";
    echo "<li><a href=\"comp_result.php?comPk=$comPk\" title=\"Results\"" . $clarr[2] . ">Results</a></li>\n";
    $regPk=reqival('regPk');
    if ($regPk > 0)
    {
    echo "<li><a href=\"http://highcloud.net/xc/waypoint_map.php?regPk=$regPk\" title=\"Waypoints\"" . $clarr[3] . ">Waypoints</a></li>\n";
    }
    //echo "<li><a href=\"comp_result.php?comPk=$comPk&tmsc=1\" title=\"Teams\"" . $clarr[4] . ">Teams</a></li>\n";
    //echo "<li><a href=\"track.php\" title=\"submit tracks\"" . $clarr[4] . ">Tracks</a></li>";
echo "</ul>\n
      <div id=\"title\">
        <h1>$title</h1>
      </div>
      <div id=\"titler\">
        <h1>$titler</h1>
      </div>
    </div>
  </div>";
}
function hcimage($link,$comPk)
{
    $image = "images/pilots.jpg";
    if (0+$comPk > 0)
    {
        $sql = "select comClass from tblCompetition where comPk=$comPk";
//        $result = mysql_query($sql,$link);
        $result = mysqli_query($link, $sql);
//        if ($row = mysql_fetch_array($result))
        if ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
        {
            $comClass = $row['comClass'];
            if ($comClass != 'PG')
            {
                $image = "images/pilots_$comClass.jpg";
            }
        }
    }
    echo "<div id=\"image\"><img src=\"$image\" alt=\"Pilots Flying\"/></div>";
}
function hcsidebar($link)
{
echo "
    <div id=\"image\"><img src=\"images/pilots.jpg\" alt=\"Pilots Flying\"/></div>
    <div id=\"sideBar\">
      <h1><span>Longest 10</span></h1>
      <div id=\"comments\"><ol>";
$count = 1;
$sql = "SELECT T.*, P.* FROM tblTrack T, tblPilot P, tblComTaskTrack CTT where T.pilPk=P.pilPk and CTT.traPk=T.traPk order by T.traLength desc limit 10";
//$result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql);
//while($row = mysql_fetch_array($result))
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $id = $row['traPk'];
    $dist = round($row['traLength']/1000,2);
    $name = $row['pilFirstName'];
    echo "<span class=\"author\"><a href=\"tracklog_map.php?trackid=$id&comPk=5\"><li> $dist kms ($name)</a></span>\n";

    $count++;
}
echo "</ol>";
echo "
        <img src=\"images/comment_bg.gif\" alt=\"comment bottom\"/>
      </div>
      <h1><span>Recent 10</span></h1><ol>";
$count = 1;
$sql = "SELECT T.*, P.* FROM tblTrack T, tblPilot P, tblComTaskTrack CTT where T.pilPk=P.pilPk and CTT.traPk=T.traPk order by T.traDate desc limit 10";
//$result = mysql_query($sql,$link);
$result = mysqli_query($link, $sql);
//while($row = mysql_fetch_array($result))
while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
{
    $id = $row['traPk'];
    $dist = round($row['traLength']/1000,2);
    $date = $row['traDate'];
    $name = $row['pilFirstName'];
    echo "<a href=\"tracklog_map.php?trackid=$id&comPk=5\"><li> $dist kms ($name)</a><br>\n";

    $count++;
}

echo "</ol>";
echo "<img src=\"images/comment_bg.gif\" alt=\"comment bottom\"/>
    </div>\n";
}
function hcregion($link)
{
    echo "<h1><span>Tracks by Region</span></h1>\n";
    $sql = "select R.*, RW.* from tblCompetition C, tblTask T, tblRegion R, tblRegionWaypoint RW where T.comPk=C.comPk and T.regPk=R.regPk and C.comDateTo > date_sub(now(), interval 1 year) and R.regCentre=RW.rwpPk and R.regDescription not like '%test%' and R.regDescription not like '' group by R.regPk order by R.regDescription";
//    $result = mysql_query($sql,$link);
    $result = mysqli_query($link, $sql);
    $regions = [];
//    while($row = mysql_fetch_array($result))
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        $regPk=$row['regPk'];
        #$regions[] = "<a href=\"regional.php?${piln}regPk=$regPk\">" . $row['regDescription'] . "</a>";
        $regions[] = "<a href=\"regional.php?regPk=$regPk\">" . $row['regDescription'] . "</a>";
    }
    echo fnl($regions);
    //echo "<img src=\"images/comment_bg.gif\" alt=\"comment bottom\"/></div>\n";
}
function hcopencomps($link)
{
    echo "<h1><span>Open Competitions</span></h1>";
    $sql = "select * from tblCompetition where comName not like '%test%' and comDateTo > date_sub(now(), interval 1 day) order by comDateTo";
//    $result = mysql_query($sql,$link);
    $result = mysqli_query($link, $sql);
    $comps = [];
//    while($row = mysql_fetch_array($result))
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        // FIX: if not finished & no tracks then submit_track page ..
        // FIX: if finished no tracks don't list!
        $cpk = $row['comPk'];
        $comps[] = "<a href=\"comp_result.php?comPk=$cpk\">" . $row['comName'] . "</a>";
    }
    echo fnl($comps);
}
function hcclosedcomps($link, $like = '')
{
    echo "<h1><span>Closed Competitions</span></h1>";

    if ($like != '')
    {
        $arr = explode (" ", $like);
        $first = $arr[0];
        $sql = "select * from tblCompetition where comName not like '%test%' and comName like '%$first%' and comDateTo < date_sub(now(), interval 1 day) order by comDateTo desc limit 15";
    }
    else
    {
        $sql = "select * from tblCompetition where comName not like '%test%' and comDateTo < date_sub(now(), interval 1 day) order by comDateTo desc limit 15";
    }
//    $result = mysql_query($sql,$link);
    $result = mysqli_query($link, $sql);
    $comps = [];
//    while ($row = mysql_fetch_array($result))
    while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
    {
        // FIX: if not finished & no tracks then submit_track page ..
        // FIX: if finished no tracks don't list!
        $cpk = $row['comPk'];
        if ($row['comType'] == 'Route')
        {
            $comps[] = "<a href=\"compview.php?comPk=$cpk\">" . $row['comName'] . "</a>";
        }
        else
        {
            $comps[] = "<a href=\"comp_result.php?comPk=$cpk\">" . $row['comName'] . "</a>";
        }
    }
    echo fnl($comps);
}
function hcfooter()
{
    echo "<div id=\"footer\">
      <a href=\"http://openwebdesign.org\" title=\"designed by fullahead.org\">Open Web Design</a></div>
  </div>\n";
}
?>
