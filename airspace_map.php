<?php
require 'authorisation.php';
require 'format.php';
require 'hc2v3.php';
require 'plot_air.php';

echo "<html xmlns=\"http://www.w3.org/1999/xhtml\" xmlns:v=\"urn:schemas-microsoft-com:vml\">";
echo "<head>";
echo "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\"
    \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">";
echo '<meta http-equiv="content-type" content="text/html; charset=utf-8"/>';
echo "<title>Airspace Map</title>";
hccss();
hcmapjs();
hcscripts(array('json2.js', 'sprintf.js', 'plot_air.js'));
echo '<script type="text/javascript">';
sajax_show_javascript();
echo '</script>';
?>
<script type="text/javascript">
var map;

//<![CDATA[

function initialise() 
{
    var moptions =
        {
            zoom: 11,
            center: new google.maps.LatLng(-37, 143.644),
            mapTypeId: google.maps.MapTypeId.TERRAIN,
            mapTypeControl: true,
            mapTypeControlOptions: {
                style: google.maps.MapTypeControlStyle.DROPDOWN_MENU
            },
            zoomControl: true,
            zoomControlOptions: {
                style: google.maps.ZoomControlStyle.SMALL
            },
            panControl: true,
            zoomControl: true,
            scaleControl: true
        };
    map = new google.maps.Map(document.getElementById("map"), moptions);

<?php
$link = db_connect();
$airPk = intval($_REQUEST['airPk']);
$interval = intval($_REQUEST['int']);
$action = addslashes($_REQUEST['action']);
$extra = 0;

$comName='Highcloud OLC';
$tasName='';

if ($airPk > 0) 
{
    echo "do_add_air($airPk);\n";
}
?>
}
google.maps.event.addDomListener(window, 'load', initialise);

    //]]>
</script>
</head>
<body>
<div id="container">
<?php
hcheadbar("Airspace Map",2);
echo "<div id=\"content\">";
echo "<div id=\"map\" style=\"width: 100%; height: 600px\"></div>";

$sql = "select A.* from tblAirspace A";
$result = mysql_query($sql,$link) or die('Airspace selection failed: ' . mysql_error());
$addable = Array();
while ($row = mysql_fetch_array($result))
{   
    $addable[$row['airName']] = $row['airPk'];
}
echo fselect('trackid', '', $addable);
//echo "<input type=\"text\" name=\"trackid\" id=\"trackid\" size=\"8\"\">";
echo "<input type=\"button\" name=\"check\" value=\"Add Track\" onclick=\"do_add_air(0); return false;\">";
echo "<br><input type=\"text\" name=\"foo\" id=\"foo\" size=\"8\"\">";
echo "</div>\n";
mysql_close($link);
?>
</body>
</html>

