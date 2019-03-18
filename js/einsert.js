// Version 0.0 Experimental Version - no transparent PNG support in IE
// Version 0.1 Initial release version - AlphaImageLoader for IE added
// Version 0.2 Wasn't positioning to the centre of the insert correctly
// Version 0.3 Add zindex parameter
// Version 1.0 Add .makeDraggable() [requires API v2.59]
// Version 1.1 18/10/2006 use pane 1 instead of G_MAP_MAP_PANE so as to be above GTileLayerOverlay()s
// Version 1.2 02/04/2007 work with MarkerManager
// Version 1.3 16/05/2007 Add isHidden(), supportsHide(), setImage(), setZindex(), setSize() and setPoint()
// Version 1.4 17/09/2007 Remove direct reference to the "map" variable (thanks to Philippe Matet)

      function EInsert(point, image, size, basezoom, zindex) {
        this.point = point;
        this.image = image;
        this.size = size;
        this.basezoom = basezoom;
        this.zindex=zindex||0;
        // Is this IE, if so we need to use AlphaImageLoader
        var agent = navigator.userAgent.toLowerCase();
        
        if ((agent.indexOf("msie") > -1) && (agent.indexOf("opera") < 1)){this.ie = true} else {this.ie = false}
        this.hidden = false;
      } 
      
      EInsert.prototype = new GOverlay();

      EInsert.prototype.initialize = function(map) {
        var div = document.createElement("div");
        div.style.position = "absolute";
        div.style.zIndex=this.zindex;
        if (this.zindex < 0) {
           map.getPane(G_MAP_MAP_PANE).appendChild(div);
        } else {
           map.getPane(1).appendChild(div);
        }
        this.map_ = map;
        this.div_ = div;
      }
      
      EInsert.prototype.makeDraggable = function() {
        this.dragZoom_ = this.map_.getZoom();
        this.dragObject = new GDraggableObject(this.div_);
        
        this.dragObject.parent = this;
        
        GEvent.addListener(this.dragObject, "dragstart", function() {
          this.parent.left=this.left;
          this.parent.top=this.top;
        });

      
        GEvent.addListener(this.dragObject, "dragend", function() {
          var pixels = this.parent.map_.fromLatLngToDivPixel(this.parent.point);
          var newpixels = new GPoint(pixels.x + this.left - this.parent.left, pixels.y +this.top -this.parent.top);
          this.parent.point = this.parent.map_.fromDivPixelToLatLng(newpixels);
          this.parent.redraw(true);
          GEvent.trigger(this.parent, "dragend", this.parent.point);
        });    
      }

      EInsert.prototype.remove = function() {
        this.div_.parentNode.removeChild(this.div_);
      }

      EInsert.prototype.copy = function() {
        return new EInsert(this.point, this.image, this.size, this.basezoom);
      }

      EInsert.prototype.redraw = function(force) {
       if (force) {
        var p = this.map_.fromLatLngToDivPixel(this.point);
        var z = this.map_.getZoom();
        var scale = Math.pow(2,(z - this.basezoom));
        var h=this.size.height * scale;
        var w=this.size.width * scale;

        this.div_.style.left = (p.x - w/2) + "px";
        this.div_.style.top = (p.y - h/2) + "px";

        if (this.ie) {
          var loader = "filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src='"+this.image+"', sizingMethod='scale');";
          this.div_.innerHTML = '<div style="height:' +h+ 'px; width:'+w+'px; ' +loader+ '" ></div>';
        } else {
          this.div_.innerHTML = '<img src="' +this.image+ '"  width='+w+' height='+h+' >';
        }
        
        // Only draggable if current zoom = the initial zoom
        if (this.dragObject) {
          if (z != this.dragZoom_) {this.dragObject.disable();}
        }
        
       } 
      }

      EInsert.prototype.show = function() {
        this.div_.style.display="";
        this.hidden = false;
      }
      
      EInsert.prototype.hide = function() {
        this.div_.style.display="none";
        this.hidden = true;
      }
      
      EInsert.prototype.getPoint = function() {
        return this.point;
      }

      EInsert.prototype.supportsHide = function() {
        return true;
      }

      EInsert.prototype.isHidden = function() {
        return this.hidden;
      }
      
      EInsert.prototype.setPoint = function(a) {
        this.point = a;
        this.redraw(true);
      }

      EInsert.prototype.setImage = function(a) {
        this.image = a;
        this.redraw(true);
      }
      
      EInsert.prototype.setZindex = function(a) {
        this.div_.style.zIndex=a;
      }

      EInsert.prototype.setSize = function(a) {
        this.size = a;
        this.redraw(true);
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
    var latConv = P.distanceFrom(new GLatLng(P.lat()+0.1, P.lng())) * 10;
    var lonConv = P.distanceFrom(new GLatLng(P.lat(), P.lng()+0.1)) * 10;

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
    return new GSize(lonpixels, latpixels);
}

