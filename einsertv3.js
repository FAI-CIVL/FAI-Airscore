// Version 2.0 - V3 modifications (gwong)

google.maps.LatLng.prototype.distanceFrom = function(newLatLng) 
{
   // setup our variables
   var lat1 = this.lat();
   var radianLat1 = lat1 * ( Math.PI  / 180 );
   var lng1 = this.lng();
   var radianLng1 = lng1 * ( Math.PI  / 180 );
   var lat2 = newLatLng.lat();
   var radianLat2 = lat2 * ( Math.PI  / 180 );
   var lng2 = newLatLng.lng();
   var radianLng2 = lng2 * ( Math.PI  / 180 );
   // sort out the radius, MILES or KM?
   var earth_radius = 6378100; // (km = 6378.1) OR (miles = 3959) - radius of the earth
 
   // sort our the differences
   var diffLat =  ( radianLat1 - radianLat2 );
   var diffLng =  ( radianLng1 - radianLng2 );
   // put on a wave (hey the earth is round after all)
   var sinLat = Math.sin( diffLat / 2  );
   var sinLng = Math.sin( diffLng / 2  ); 
 
   // maths - borrowed from http://www.opensourceconnections.com/wp-content/uploads/2009/02/clientsidehaversinecalculation.html
   var a = Math.pow(sinLat, 2.0) + Math.cos(radianLat1) * Math.cos(radianLat2) * Math.pow(sinLng, 2.0);
 
   // work out the distance
   var distance = earth_radius * 2 * Math.asin(Math.min(1, Math.sqrt(a)));
 
   // return the distance
   return distance;
}

function EInsert(map, point, image, size, basezoom, zindex) 
{
    this.point = point;
    this.image = image;
    this.size = size;
    this.basezoom = basezoom;
    this.zindex=zindex||0;
    this.map_ = map;
    // Is this IE, if so we need to use AlphaImageLoader
    var agent = navigator.userAgent.toLowerCase();
    
    if ((agent.indexOf("msie") > -1) && (agent.indexOf("opera") < 1))
    {
        this.ie = true
    } 
    else 
    {
        this.ie = false
    }
    this.hidden = false;
    this.setMap(map);
} 
      
EInsert.prototype = new google.maps.OverlayView();

EInsert.prototype.onAdd = function() 
{
    var div = document.createElement("div");
    var img = document.createElement("img");
    var panes = this.getPanes();

    img.src = this.image;
    img.style.width = "100%";
    img.style.height = "100%";
    div.appendChild(img);

    div.style.position = "absolute";
    div.style.zIndex=this.zindex;
    panes.mapPane.appendChild(div);
    //if (this.zindex < 0) {
    //   map.getPane(G_MAP_MAP_PANE).appendChild(div);
    //} else {
    //   map.getPane(1).appendChild(div);
    //}
    this.div_ = div;
}
      
EInsert.prototype.onRemove = function() 
{
    this.div_.parentNode.removeChild(this.div_);
    this.div_ = null;
}

EInsert.prototype.draw = function(force) 
{
    //if (force) 
    {
        //var overlayProjection = this.getProjection();
        //var sw = overlayProjection.fromLatLngToDivPixel(this.bounds_.getSouthWest());
        //var ne = overlayProjection.fromLatLngToDivPixel(this.bounds_.getNorthEast());

        var p = this.getProjection().fromLatLngToDivPixel(this.point);
        var z = this.map_.getZoom();
        var scale = Math.pow(2,(z - this.basezoom));
        var h=this.size.height * scale;
        var w=this.size.width * scale;

        this.div_.style.left = (p.x - w/2) + "px";
        this.div_.style.top = (p.y - h/2) + "px";
        //this.div_.style.left = sw.x + "px";
        //this.div_.style.top = ne.y + "px";
        this.div_.style.width = w + 'px';
        this.div_.style.height = h + 'px';


//        if (this.ie) 
//        {
//            var loader = "filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src='"+this.image+"', sizingMethod='scale');";
//            this.div_.innerHTML = '<div style="height:' +h+ 'px; width:'+w+'px; ' +loader+ '" ></div>';
//        } 
//        else 
//        {
//            this.div_.innerHTML = '<img src="' +this.image+ '"  width='+w+' height='+h+' >';
//            //this.div_.innerHTML = '<img src="' +this.image+ '">';
//        }
//        
//        // Only draggable if current zoom = the initial zoom
//        if (this.dragObject) 
//        {
//            if (z != this.dragZoom_) {this.dragObject.disable();}
//        }
//        
    } 
}

EInsert.prototype.copy = function() 
{
    return new EInsert(this.map, this.point, this.image, this.size, this.basezoom);
}


EInsert.prototype.show = function() 
{
    this.div_.style.visibility="visible";
    this.hidden = false;
}
      
EInsert.prototype.hide = function() 
{
    this.div_.style.visibility="hidden";
    this.hidden = true;
}
      
EInsert.prototype.supportsHide = function() 
{
    return true;
}

EInsert.prototype.isHidden = function() 
{
    return (this.div_.style.visibility == "hidden");
}

EInsert.prototype.toggle = function() 
{
    if (this.div_) 
    {
        if (this.div_.style.visibility == "hidden") 
        {
            this.show();
        } 
        else 
        {
            this.hide();
        }
    }
}


EInsert.prototype.toggleDOM = function() 
{
    if (this.getMap()) 
    {
        this.setMap(null);
    } 
    else 
    {
        this.setMap(this.map_);
    }
}

EInsert.prototype.getPoint = function() 
{
    return this.point;
}

      
EInsert.prototype.setPoint = function(a) 
{
    this.point = a;
    this.draw(true);
}

EInsert.prototype.setImage = function(a) 
{
    this.image = a;
    this.draw(true);
}
      
EInsert.prototype.setZindex = function(a) 
{
    this.div_.style.zIndex=a;
}

EInsert.prototype.setSize = function(a) 
{
        this.size = a;
        this.draw(true);
}
      
function GSizeFromMeters(M,P,X,Y)
{
    // get map zoom level 
    var zom = M.getZoom();

    // var earth_radius = 6378137;
    // equator resolution: (2 * Math.PI * $earth_radius) / (256 * Math.pow(2,zom))
    // var ntiles = Math.pow(2,zom); // tiles across earth 
    var npixels = Math.pow(2,zom+8); // 256 pixels per tile

    // pixel/degree
    var ppd = npixels / 360.0;

    // calculating metre/degree (0.1)
    var latConv = P.distanceFrom(new google.maps.LatLng(P.lat()+0.1, P.lng())) * 10;
    var lonConv = P.distanceFrom(new google.maps.LatLng(P.lat(), P.lng()+0.1)) * 10;

    // pixpermeterlat=(Math.pow(2, zom+8))  /
    //   (2*Math.PI*6378100*Math.cos(P.lat()*Math.PI/180)) 
    // degrees covered ..
    // 0.7716245;
    // 1/sqrt(2) = 0.707106781
    //var latpixels = Y * (ppd / latConv) / 0.707106781; 
    //var latpixels = Y * (ppd / latConv) / 0.7716245;
    var latpixels = Y * (Math.pow(2, zom+8)) / (2*Math.PI*6378100*Math.cos(P.lat()*Math.PI/180));
    var lonpixels = X * (ppd / lonConv);

    //document.getElementById("foo").value = lonpixels;
    return new google.maps.Size(lonpixels, latpixels);
}

