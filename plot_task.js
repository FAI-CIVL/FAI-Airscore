var pbounds;
function add_award_task(tasPk, trackid)
{
    // FIX: should show already awarded ones ...
    microAjax("get_track_progress.php?tasPk="+tasPk+"&trackid="+trackid,
    function(data) {
    var task;
    var tps;
    var track;
    var incpk;
    var ovlay;
    var ovhtml;
    var cnt;
    var end = 0;

    var task = JSON.parse(data);
    ovhtml = "<div class=\"htmlControl\"><b>Award Points</b><br><form name=\"trackdown\" method=\"post\">\n";
    track = task["task"];
    tps = 0 + task["turnpoints"];
    incpk = task["merge"];
    cnt = 0;
    // fix to show awarded points - unclick to unaward ..
    for (row in track)
    {
        cnt = cnt + 1;
        if (cnt > tps)
        {
            name = track[row]['rwpName'];
            tawtype = track[row]['tawType'];
            tawPk = track[row]['tawPk'];
            if ((end == 0) && (tawtype == 'endspeed' || tawtype == 'goal'))
            {
                ovhtml = ovhtml +  cnt + ". <input onblur=\"x_award_waypoint(" + tasPk + "," + tawPk + "," + trackid + ",this.value,done)\" type=\"text\" name=\"goaltime\" size=5>&nbsp;" + name + "<br>";
                end = 1;
            }
            else if (tawtype == 'speed')
            {
                ovhtml = ovhtml +  cnt + ". <input onblur=\"x_award_waypoint(" + tasPk + "," + tawPk + "," + trackid + ",this.value,done)\" type=\"text\" name=\"goaltime\" size=5>&nbsp;" + name + "<br>";
            }
            else
            {
                ovhtml = ovhtml +  cnt + ". <input type=\"checkbox\" name=\"turnpoint\" onclick=\"x_award_waypoint(" + tasPk + "," + tawPk + "," + trackid + "," + cnt + ",done)\">&nbsp;" + name + "<br>";
            }
        }
    }
    // add in a 'merge with' option?
    if (incpk > 0)
    {
        ovhtml = ovhtml + "<br><center><input type=\"button\" name=\"domerge\" value=\"Merge "+incpk+"\" onclick=\"merge_tracks("+tasPk+","+trackid+","+incpk+");\"></center>";
    }
    ovhtml = ovhtml + "</form></div>";
    ovlay = document.createElement('DIV');
    ovlay.innerHTML = ovhtml;
    //ovlay = new HtmlControl(ovhtml, { visible:false, selectable:true, printable:true } );
    //ovlay = new HtmlControl('Hello World!', { visible:false, selectable:true, printable:true } );
    //map.addControl(ovlay, new google.maps.ControlPosition(G_ANCHOR_BOTTOM_RIGHT, new GSize(128, 256)));
    map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(ovlay);
    //map.addControl(ovlay, new google.maps.ControlPosition(G_ANCHOR_BOTTOM_RIGHT, new google.maps.Size(10, 10)));
    //ovlay.setVisible(true);
    });
}
function plot_pilots_lo(tasPk)
{
    microAjax("get_pilots_lo.php?tasPk="+tasPk,
	  function(data) {
          var pilots;
          var pos;
        
    
          // Got a good response, create the map objects
          pilots = RJSON.unpack(JSON.parse(data));
          //pbounds = new google.maps.LatLngBounds();

          for (row in pilots)
          {
              var overlay;
              lat = pilots[row]["trlLatDecimal"];
              lon = pilots[row]["trlLongDecimal"];
              name = pilots[row]["name"];

              //alert("name="+name+" lat="+lat+" lon="+lon);
              pos = new google.maps.LatLng(lat,lon);
              pbounds.extend(pos);
              overlay = new ELabel(map, pos, name, "pilot", new google.maps.Size(0,0), 60);
      
          }
        
          map.fitBounds(pbounds);
    });
}
function plot_task(tasPk, pplo, trackid)
{
    microAjax("get_short.php?tasPk="+tasPk, 
    function (data) {
      var task, track, row;
      var line, sline, polyline;
      var prevslat, prevslon, gll, count, color;
      var pos, sz;
      var ihtml, ovlay;
    

      // Got a good response, create the map objects
      //alert("complete: " + data);

      var ssr = JSON.parse(data);

      line = Array();
      sline = Array();
      pbounds = new google.maps.LatLngBounds();

      count = 1;
      ihtml = "<div class=\"trackInfo\"><table>";
      for (row in ssr)
      {
          var overlay;
          var circle;
          lasLat = ssr[row]["rwpLatDecimal"];
          lasLon = ssr[row]["rwpLongDecimal"];
          sLat = ssr[row]["ssrLatDecimal"];
          sLon = ssr[row]["ssrLongDecimal"];
          cname = "" + count + "*" + ssr[row]["rwpName"];
          crad = ssr[row]["tawRadius"];
          shape = ssr[row]["tawShape"];

          ihtml = ihtml + "<tr><td><b>" + ssr[row]["rwpName"] + "<b></td><td>" + ssr[row]["tawType"] + "</td><td>" + ssr[row]["tawRadius"] + "m</td><td>" + ssr[row]["tawHow"] + "</td><td>" + sprintf("%0.2f", ssr[row]["ssrCumulativeDist"]/1000) + "km</td></tr>";
  
          //alert("lasLat="+lasLat+" lasLon="+lasLon);
          gll = new google.maps.LatLng(lasLat, lasLon);
          line.push(gll);
          pbounds.extend(gll);

          gll = new google.maps.LatLng(sLat, sLon);
          sline.push(gll);
      
          count = count + 1;    
  
          pos = new google.maps.LatLng(lasLat,lasLon);
          overlay = new ELabel(map, pos, cname, "waypoint", new google.maps.Size(0,0), 60);
  
          if (shape == "line")
          {
              //sz = GSizeFromMeters(map, pos, crad*2,crad*2);
              //overlay = new EInsert(map, pos, "circle.png", sz, map.getZoom());
              var alpha, beta;
              var lat1, lat2, lon1, lon2;
              var x, y, diflon, brng, perp;

              lat1 = prevslat * Math.PI / 180;
              lon1 = prevslon * Math.PI / 180;
              lat2 = lasLat * Math.PI / 180;
              lon2 = lasLon * Math.PI / 180;
              
              diflon = lon2 - lon1;
              y = Math.sin(diflon) * Math.cos(lat2);
              x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(diflon);
              brng = Math.atan2(y,x);
              alpha = brng - Math.PI / 2;
              beta = brng + Math.PI / 2;
              //alert("brng="+(brng*180/Math.PI) + " alpha="+(alpha*180/Math.PI) + " beta="+(beta*180/Math.PI));
              wline = make_wedge([ 0, lasLat, lasLon ], alpha, beta, crad, "arc+");
              wline.push(wline[0]);
              polyline = new google.maps.Polyline({   
                      path: wline, 
                      strokeColor: "#ff0000",
                      strokeWeight: 2, 
                      strokeOpacity: 1
                  });
              polyline.setMap(map);

          }
          else
          {
              circle = new google.maps.Circle({
                center:pos,
                radius:parseInt(crad),
                strokeColor:"#ff0000",
                strokeOpacity:1.0,
                strokeWeight:1.0,
                fillColor:"#ff0000",
                fillOpacity:0.15,
                map:map
              });
          }
          prevslat = sLat;
          prevslon = sLon;
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

      map.fitBounds(pbounds);

      ihtml = ihtml + "</table></div>";
      ovlay = document.createElement('DIV');
      ovlay.style.padding = "5px";
      ovlay.innerHTML = ihtml;
      map.controls[google.maps.ControlPosition.LEFT_TOP].push(ovlay);
      if (pplo)
      {
        plot_pilots_lo(tasPk);
      }
      if (trackid > 0)
      {
        add_award_task(tasPk, trackid);
      }
    });
}
