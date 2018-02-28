<?php
    require 'authorisation.php';
    require 'hc.php';
    require 'format.php';

function tracktable($link, $order, $start)
    {
        //<div id=\"comments\"><ol>";

        $count = $start+1;
        $long = [];
        $sql = "select T.*, P.*, CTT.* from tblTrack T, tblPilot P, tblComTaskTrack CTT, tblWaypoint W, (select traPk,min(wptTime) as minTime from tblWaypoint group by traPk) as MW where W.wptTime=MW.minTime and W.traPk=MW.traPk and T.traPk=W.traPk and CTT.traPk=T.traPk and T.pilPk=P.pilPk $order";
        $result = mysqli_query($link, $sql) or die('Error ' . mysqli_errno($link) . ' Invalid track table ' . mysqli_connect_error());
        $num = mysqli_num_rows($result);
        while ($row = mysqli_fetch_array($result, MYSQLI_BOTH))
        {
            $id = $row['traPk'];
            $dist = round($row['traLength']/1000,2);
            $name = $row['pilFirstName'] . ' ' . $row['pilLastName'];
            $comPk = $row['comPk'];
            $pilPk = $row['pilPk'];
            $long[] = [ "$count.", "<a href=\"tracklog_map.php?trackid=$id&comPk=$comPk\">$dist kms</a>", $row['traDate'], "<a href=\"index.php?pil=$pilPk\">$name<a>" ];
            $count++;
        }
        echo ftable($long, '', '', '');
        return $num;
    }
    
// Main Code Begins HERE //

$link = db_connect();
$order = addslashes($_REQUEST['order']);
$start = intval($_REQUEST['start']);
$pilot = intval($_REQUEST['pil']);
$comp = intval($_REQUEST['comPk']);

$title = 'highcloud.net';
if ($comp > 0)
{
	$sql = "SELECT T.*,F.* FROM tblCompetition T left outer join tblFormula F on F.comPk=T.comPk where T.comPk=$comp";
	$result = mysqli_query($link, $sql);
	$row = mysqli_fetch_array($result, MYSQLI_BOTH);
	if ($row)
	{
		$cname = $row['comName'];
		$title = $row['comName'];
		$cdfrom = substr($row['comDateFrom'],0,10);
		$cdto = substr($row['comDateTo'],0,10);
		$cdirector = $row['comMeetDirName'];
		$clocation = $row['comLocation'];
		$cformula = $row['forClass'] . ' ' . $row['forVersion'];
		$csanction = $row['comSanction'];
		$coverall = $row['comOverallScore'];
		$ccode = $row['comCode'];
		$ctype = $row['comType'];
		$comstr = "and CTT.comPk=$comp ";
	}
}

if ($pilot > 0)
{
	$sql = "select P.pilFirstName, P.pilLastName from tblPilot P where P.pilPk=$pilot";
	$result = mysqli_query($link, $sql);
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

$ordern = '';
if ($order != '')
{
	$ordern="order=$order&";
}
hcheader($title, 0, "$cdfrom - $cdto");

echo "<div id=\"content\">";
echo "<div id=\"text\">";

echo "<h1><span>Details</span></h1>\n";
$detarr = [
	 [ "Location:", "<i>$clocation</i>", "Director:", "<i>$cdirector</i>" ],
	 [ "From:", "<i>$cdfrom</i>", "To:", "<i>$cdto</i>" ],
	 [ "Type:", "<i>$ctype ($cformula)</i>", "Overall Score:","<i>$coverall</i>" ]
	];
echo ftable($detarr, '', '', '');

$num = 20;
$sort = "${comstr}${pilstr}order by T.traDate desc limit $start,$num";
echo "<h1><span>Recent " . ($start+1) . "-" . ($start+$num) . "</span></h1>\n";
if (tracktable($link, $sort, $start) == $num)
{
	echo "<b class=\"right\"><a href=\"cv.php?${piln}&comPk=$comp&${ordern}start=" . ($start+$num) . "\">Next 25</a></b>\n";
}

echo "</div>";
hcimage($link,$comp);
echo "<div id=\"sideBar\">";
hcregion($link);
hcopencomps($link);
hcclosedcomps($link);
echo "</div>";

hcfooter();

?>
