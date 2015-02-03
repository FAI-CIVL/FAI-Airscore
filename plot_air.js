var onscreen = Array();
var airspaceid;

String.prototype.format = function()
{
    var pattern = /\{\d+\}/g;
    var args = arguments;
    return this.replace(pattern, function(capture){ return args[capture.match(/\d+/)]; });
}
function do_add_air(x) 
{
    if (!x || x == 0)
    {   
        airspaceid = document.getElementById("airspaceid").value;
    }
    else
    {   
        airspaceid = x;
    }
    x_get_airspace(airspaceid, plot_air);
}
function done(x)
{
    // do nothing
}
function dist(p1, p2)
{
    var earth = 6378137.0;
    var p1lat = p1[1] * Math.PI / 180;
    var p1lon = p1[2] * Math.PI / 180;
    var p2lat = p2[1] * Math.PI / 180;
    var p2lon = p2[2] * Math.PI / 180;
    var dlat = (p2lat - p1lat);
    var dlon = (p2lon - p1lon);


    var a = Math.sin(dlat/2) * Math.sin(dlat/2) + Math.cos(p1lat) * Math.cos(p2lat) * Math.sin(dlon/2) * Math.sin(dlon/2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return earth * c;
}
function make_wedge(center, alpha, beta, radius, dirn)
{
    var points = 16;
    var earth = 6378137.0;
    var delta;
    var Cpoints = [];
    var nlat,nlon;
    var nbrg;

    // to radians
    var Clat = center[1] * Math.PI / 180;
    var Clng = center[2] * Math.PI / 180;

    if (dirn == "arc-")
    {
        // anti
        delta = alpha - beta;
    }
    else
    {
        // clock
        delta = beta - alpha;
    }

    if (delta < 0) 
    {
        delta = delta + Math.PI * 2;
    }

    delta = delta / points;

    if (dirn == "arc-")
    {
        delta = -delta;
    }

    nbrg = alpha;
    for (var i=0; i < points+1; i++) 
    {
        nlat = Math.asin(Math.sin(Clat)*Math.cos(radius/earth) + 
                Math.cos(Clat)*Math.sin(radius/earth)*Math.cos(nbrg) );

        nlon = Clng + Math.atan2(Math.sin(nbrg)*Math.sin(radius/earth)*Math.cos(Clat),
                Math.cos(radius/earth)-Math.sin(Clat)*Math.sin(nlat));

        // back to degrees ..
        nlat = nlat * 180 / Math.PI;
        nlon = nlon * 180 / Math.PI;

        Cpoints.push(new google.maps.LatLng(nlat,nlon));
        
        nbrg = nbrg + delta;
    }

    return Cpoints;
}
function plot_air(jstr)
{
    var track;
    var row;
    var line;
    //var trklog;
    var polyline;
    var gll;
    var count;
    var color;
    var pos;
    var sz;
    var label;
    var circle;
    var center;

    count = 1;
    track = JSON.parse(jstr)
    line = Array();
    segments = Array();
    //trklog = Array();
    bounds = new google.maps.LatLngBounds();

    shape = track[0][5];
    if (shape == "circle")
    {
        lasLat = track[0][1];
        lasLon = track[0][2];
        cname =  track[0][3];
        crad = parseInt(track[0][6]);

        pos = new google.maps.LatLng(lasLat,lasLon);

        circle = new google.maps.Circle({
                center:pos, 
                radius:crad, 
                strokeColor:"#0000ff", 
                strokeOpacity:1.0,
                strokeWeight:1.0,
                fillColor:"#0000ff", 
                fillOpacity:0.4,
                map:map
            });

        if (onscreen.length == 0 && count == 1)
        {
            map.setCenter(pos, 13);
        }

        //sz = GSizeFromMeters(map, pos, crad*2,crad*2);
        //map.addOverlay(new EInsert(pos, "bluecircle.png", sz, map.getZoom()));
        
        // Fix - should place on 4(?) points of circle NSEW perhaps
        label = new ELabel(map, pos, cname, "waypoint", new google.maps.Size(0,0), 60);
        bounds.extend(pos);

        onscreen[airspaceid] = track;
        return track;
    }

    //if (shape == "wedge")
    //{
    //    center = track[0];
    //    track.shift();
    //}

    // otherwise polygon (wedge not handled properly)
    for (row in track)
    {
        lasLat = track[row][1];
        lasLon = track[row][2];
        cname =  track[row][3];
        shape = track[row][5];
        connect = track[row][7];

        if (onscreen.length == 0 && count == 1)
        {
            map.setCenter(new google.maps.LatLng(lasLat, lasLon), 9);
        }

        //alert("connect="+connect);
        if (connect == "arc+" || connect == "arc-")
        {
            // add an arc of polylines
            var radius = dist(track[row], track[row-1]);

            wline = make_wedge(track[row], parseFloat(track[row][8]), parseFloat(track[row][9]), radius, connect);
            for (pt in wline)
            {
                line.push(wline[pt]);
                bounds.extend(wline[pt]);
            }
            gll = wline[pt];
        }
        else
        {
            gll = new google.maps.LatLng(lasLat, lasLon);
            line.push(gll);
            bounds.extend(gll);
            //trklog.push(track[row]);
        }
    
        if (count % 10 == 0)
        {
            polyline = new google.maps.Polyline({
                path: line, 
                strokeColor: "#0000ff", 
                strokeWeight: 2, 
                strokeOpacity: 1,
                map:map} );
            segments.push(polyline);
            line = Array();
            line.push(gll);
        }
        count = count + 1;    

        if (!(connect == "arc+" || connect == "arc-"))
        {
            pos = new google.maps.LatLng(lasLat,lasLon);
            label  = new ELabel(map, pos, row, "waypoint", new google.maps.Size(0,0), 60);
        }
        map.fitBounds(bounds);

        //sz = GSizeFromMeters(map, pos, crad*2,crad*2);
        //map.addOverlay(new EInsert(pos, "circle.png", sz, 13));
    }

    if (line.length > 0)
    {
        polyline = new google.maps.Polyline({
            path: line, 
            strokeColor: "#0000ff", 
            strokeWeight: 2, 
            strokeOpacity: 1, 
            map:map });
        segments.push(polyline);
    }

    onscreen[airspaceid] = track;
    return track;
}

