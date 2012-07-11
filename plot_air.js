var onscreen = Array();
var trackid;

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
        trackid = document.getElementById("trackid").value;
    }
    else
    {   
        trackid = x;
    }
    x_get_airspace(trackid, plot_air);
}
function done(x)
{
    // do nothing
}
function plot_air(jstr)
{
    var track;
    var row;
    var line;
    var trklog;
    var polyline;
    var gll;
    var count;
    var color;
    var pos;
    var sz;
    var label;
    var circle;

    count = 1;
    track = JSON.parse(jstr)
    line = Array();
    segments = Array();
    trklog = Array();
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

        onscreen[trackid] = track;
        return track;
    }

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

        if (connect == "arc")
        {
            continue;
        }
    
        gll = new google.maps.LatLng(lasLat, lasLon);
        line.push(gll);
        bounds.extend(gll);
        trklog.push(track[row]);
    
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

        pos = new google.maps.LatLng(lasLat,lasLon);
        label  = new ELabel(map, pos, cname, "waypoint", new google.maps.Size(0,0), 60);
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

    onscreen[trackid] = track;
    return track;
}

