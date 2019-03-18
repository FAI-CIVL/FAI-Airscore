
function drawCircle(map, center, radius, numPoints, astart, aend)
{
    var poly = [] ; 
    var lat = center.lat() ;
    var lng = center.lng() ;
    var d2r = Math.PI/180 ;                // degrees to radians
    var r2d = 180/Math.PI ;                // radians to degrees
    var Clat = (radius/3963) * r2d ;      //  using 3963 as earth's radius
    var Clng = Clat/Math.cos(lat*d2r);
    
    // Add each point in the circle
    for (var i = 0 ; i < numPoints ; i++)
    {
        var theta = Math.PI * (i / (numPoints / 2)) ;
        Cx = lng + (Clng * Math.cos(theta)) ;
        Cy = lat + (Clat * Math.sin(theta)) ;
        poly.push(new GLatLng(Cy,Cx)) ;
    }
    
    //Add the first point to complete the circle
    poly.push(poly[0]) ;
    
    //Create a line with teh points from poly, red, 3 pixels wide, 80% opaque
    line = new GPolyline(poly,'#FF0000', 3, 0.8) ;
    
    map.addOverlay(line) ;
    return line;
}

