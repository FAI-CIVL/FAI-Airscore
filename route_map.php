<?php
require 'authorisation.php';
require 'format.php';
require 'hc2v3.php';
//require 'plot_track.php';
hchead();
echo "<title>Task Map</title>\n";
hccss();
hcmapjs();
hcscripts(array('json2.js', 'sprintf.js', 'plot_trackv3.js', 'microajax.minified.js'));
?>
<script type="text/javascript">
var map;
//<![CDATA[
function plot_task(tasPk)
{
    microAjax("get_short.php?tasPk="+tasPk,
	  function(data) {
          var task, track, row;
          var line, sline, polyline;
          var gll, count, color;
          var pos, sz;
          var ihtml, ovlay;
        
    
          // Got a good response, create the map objects
          //alert("complete: " + data);
    
          var ssr = JSON.parse(data);
    
          line = Array();
          sline = Array();
          bounds = new google.maps.LatLngBounds();

          count = 1;
          ihtml = "<div class=\"trackInfo\"><table>";
          for (row in ssr)
          {
              var overlay;
              lasLat = ssr[row]["rwpLatDecimal"];
              lasLon = ssr[row]["rwpLongDecimal"];
              sLat = ssr[row]["ssrLatDecimal"];
              sLon = ssr[row]["ssrLongDecimal"];
              cname = "" + count + "*" + ssr[row]["rwpName"];
              crad = ssr[row]["tawRadius"];

              ihtml = ihtml + "<tr><td><b>" + ssr[row]["rwpName"] + "<b></td><td>" + ssr[row]["tawType"] + "</td><td>" + ssr[row]["tawRadius"] + "m</td><td>" + ssr[row]["tawHow"] + "</td><td>" + sprintf("%0.2f", ssr[row]["ssrCumulativeDist"]/1000) + "km</td></tr>";
      
              //alert("lasLat="+lasLat+" lasLon="+lasLon);
              gll = new google.maps.LatLng(lasLat, lasLon);
              line.push(gll);
              bounds.extend(gll);

              gll = new google.maps.LatLng(sLat, sLon);
              sline.push(gll);
          
              count = count + 1;    
      
              pos = new google.maps.LatLng(lasLat,lasLon);
              overlay = new ELabel(map, pos, cname, "waypoint", new google.maps.Size(0,0), 60);
      
              sz = GSizeFromMeters(map, pos, crad*2,crad*2);
              overlay = new EInsert(map, pos, "circle.png", sz, map.getZoom());
          }
        
          polyline = new google.maps.Polyline({   
                    path: line, 
                    strokeColor: "#ff0000",
                    strokeWeight: 2, 
                    strokeOpacity: 1
                });
          polyline.setMap(map);

          polyline = new google.maps.Polyline({   
                    path: sline, 
                    strokeColor: "#0000ff",
                    strokeWeight: 2, 
                    strokeOpacity: 1
                });
          polyline.setMap(map);
          map.fitBounds(bounds);

          ihtml = ihtml + "</table></div>";
          ovlay = document.createElement('DIV');
          ovlay.style.padding = "5px";
          ovlay.innerHTML = ihtml;
          map.controls[google.maps.ControlPosition.RIGHT_TOP].push(ovlay);
    });
}

function initialize() 
{
    var moptions =
        {
            zoom: 12,
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
    //map.setMapTypeId(google.maps.MapTypeId.TERRAIN);

<?php
//echo "map.addControl(new GSmallMapControl());\n";
//echo "map.addControl(new GMapTypeControl());\n";
//echo "map.addControl(new GScaleControl());\n";

$usePk = check_auth('system');
$link = db_connect();
$trackid = reqival('trackid');
$comPk = reqival('comPk');
$tasPk = reqival('tasPk');
$trackok = reqsval('ok');
$isadmin = is_admin('admin',$usePk,$comPk);
$interval = reqival('int');
$action = reqsval('action');
$extra = 0;

$comName='Highcloud OLC';
$tasName='';
$offset = 0;
if ($tasPk > 0 || $trackid > 0)
{
    if ($tasPk > 0)
    {
        $sql = "SELECT C.*, T.*,T.regPk as tregPk FROM tblCompetition C, tblTask T where T.tasPk=$tasPk and C.comPk=T.comPk";
    }
    else
    {
        $sql = "SELECT CTT.tasPk as ctask,C.*,CTT.*,T.*,T.regPk as tregPk FROM tblCompetition C, tblComTaskTrack CTT left outer join tblTask T on T.tasPk=CTT.tasPk where C.comPk=CTT.comPk and CTT.traPk=$trackid";
    }

    $result = mysql_query($sql,$link) or die('Query failed: ' . mysql_error());
    if ($row = mysql_fetch_array($result))
    {
        if ($tasPk == 0)
        {
            $tasPk = $row['ctask'];
        }
        if ($comPk == 0)
        {
            $comPk = $row['comPk'];
        }
        $comName = $row['comName'];
        $tasName = $row['tasName'];
        $tasDate = $row['tasDate'];
        $tasType = $row['tasTaskType'];
        $regPk = $row['tregPk'];
        $offset = $row['comTimeOffset'];
        if ($tasName)
        {
            $comName = $comName . ' - ' . $tasName;
        }
        else
        {
            $tasName = '';
        }
    }
}

if ($tasPk > 0)
{
    echo "plot_task($tasPk);\n";
    // task header ..
}

?>
}
google.maps.event.addDomListener(window, 'load', initialize);

    //]]>
</script>
</head>
<body>
<div id="container">
<?php
hcheadbar($comName,2);
echo "<div id=\"content\">";
echo "<div id=\"map\" style=\"width: 100%; height: 600px\"></div>";
echo "</div>\n";
mysql_close($link);
?>
</body>
</html>

