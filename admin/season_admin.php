<?php
require 'admin_startup.php';

# You can chose here wich date changes the season,
# then for every season you can check in out the ladders
# and the areas as well makes sense that are selected here on a season base.


//fselect('category', $comclass, array('PG', 'HG', 'mixed'), " onchange=\"document.getElementById('ladadmin').submit();\"")



auth('system');
$link = db_connect();
$usePk = auth('system');
$comPk = reqival('comPk');
$delreg = reqsval('del');
$file = __FILE__;
$message = '';

$season = reqival('season') == 0 ? getseason() : reqival('season');

//initializing template header
//tpadmin($link,$file);

echo "<h3>Season Administration</h3>\n";
if ( $message !== '')
{
	echo "<h4> <span style='color:red'>$message</span> </h4>";
}

echo fselect('season', $season, season_array($link), " onchange=\"document.getElementById('seasonadmin').submit();\"");

echo "<hr />";
echo "<i> We have " . $count . " defined flying areas</i>";
echo "<hr />";
echo "<form enctype=\"multipart/form-data\" action=\"area_admin.php\" name=\"area\" method=\"post\">";
echo ftable($rtable,'class=areatable', '', '');
echo "</form>";
echo "<br />";
echo "<hr />";

echo "<form enctype=\"multipart/form-data\" action=\"area_admin.php\" name=\"area\" method=\"post\">";
echo "New Region: " . fin('region', '', 10);
echo fis('create', 'Create', 10);
echo "</form>";

//tpfooter($file);

?>