// V2.0 - Google Maps V3.

function ELabel(map, position, html, classname, pixelOffset, percentOpacity, overlap) 
{
    // Mandatory parameters
    this.position = position;
    this.html = html;
        
    // Optional parameters
    this.classname = classname||"";
    this.pixelOffset = pixelOffset||new google.maps.Size(0,0);
    if (percentOpacity) 
    {
        if (percentOpacity<0) {percentOpacity=0;}
        if (percentOpacity>100) {percentOpacity=100;}
    }        
    this.percentOpacity = percentOpacity;
    this.overlap=overlap||false;
    this.hidden = false;
    this.map_ = map;
    //this.canvas_ = document.getElementById("map");
    this.mouseX = 0;
    this.mouseY = 0;
    this.div_ = document.createElement("div");
    this.setMap(map);
} 
      
ELabel.prototype = new google.maps.OverlayView();

ELabel.prototype.onAdd = function() 
{
    var div = this.div_;
    var panes = this.getPanes();
    var overlay = this;
    div.style.position = "absolute";
    div.innerHTML = '<div class="' + this.classname + '">' + this.html + '</div>' ;
    this.div_ = div;
    if (this.percentOpacity) 
    {
        if (typeof(div.style.filter)=='string')
            {div.style.filter='alpha(opacity:'+this.percentOpacity+')';}
        if (typeof(div.style.KHTMLOpacity)=='string')
            {div.style.KHTMLOpacity=this.percentOpacity/100;}
        if (typeof(div.style.MozOpacity)=='string')
            {div.style.MozOpacity=this.percentOpacity/100;}
        if (typeof(div.style.opacity)=='string')
            {div.style.opacity=this.percentOpacity/100;}
    }

    panes.overlayMouseTarget.appendChild(div);

    if (this.overlap) 
    {
        var z = google.maps.Overlay.getZIndex(this.position.lat());
        this.div_.style.zIndex = z;
    }

    if (this.hidden) 
    {
        this.hide();
    }

}

ELabel.prototype.onRemove = function() 
{
    this.div_.parentNode.removeChild(this.div_);
    this.div_ = null;
}

ELabel.prototype.copy = function() 
{
    return new ELabel(this.map_, this.position, this.html, this.classname, this.pixelOffset, this.percentOpacity, this.overlap);
}

ELabel.prototype.draw = function(force) 
{
    var p = this.getProjection().fromLatLngToDivPixel(this.position);
    var h = parseInt(this.div_.clientHeight);
    this.div_.style.left = (p.x + this.pixelOffset.width) + "px";
    this.div_.style.top = ((p.y - h) + this.pixelOffset.height) + "px";
        //this.div_.style.left = p.x + "px";
        //this.div_.style.top = (p.y - h) + "px";

//        this.dragZoom_ = this.map_.getZoom();
//        this.dragObject = new google.maps.DraggableObject(this.div_);
//        this.dragObject.parent = this;
}

ELabel.prototype.show = function() 
{
    this.div_.style.visibility="visible";
    this.hidden = false;
}
      
ELabel.prototype.hide = function() 
{
    this.div_.style.visibility="hidden";
    this.hidden = true;
}
      
ELabel.prototype.supportsHide = function() 
{
    return true;
}

ELabel.prototype.isHidden = function() 
{
    return (this.div_.style.visibility == "hidden");
}

ELabel.prototype.toggle = function() 
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
      
ELabel.prototype.toggleDOM = function() 
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

ELabel.prototype.setContents = function(html) 
{
    this.html = html;
    this.div_.innerHTML = '<div class="' + this.classname + '">' + this.html + '</div>' ;
    this.draw(true);
}
      
ELabel.prototype.setPosition = function(point) 
{
    this.position = point;
    if (this.overlap) 
    {
          var z = google.maps.Overlay.getZIndex(this.position.lat());
          this.div_.style.zIndex = z;
    }
    this.draw(true);
}

ELabel.prototype.makeDraggable = function() 
{
    var div = this.div_;
    if (!this.mmlistener_)
    {
        var that = this;

        this.mdlistener_ = google.maps.event.addDomListener(div, "click", function(ev) 
        {
            var d=ev||event;
            that.point = that.getProjection().fromLatLngToContainerPixel(that.getPosition()); 
            that.mouseX = d.pageX - that.point.x;
            that.mouseY = d.pageY - that.point.y;
            //alert('mouseX='+that.mouseX+" mouseY="+that.mouseY+" pointX="+that.point.x+" pointY="+that.point.y);
            this.mmlistener_ = google.maps.event.addDomListener(window, "mousemove", function(evi)
            {
                var e=evi||event;
                var pos;

                //var point = this.map_.getProjection().fromLatLngToPoint(mEvent.latLng); 
                pos = that.getProjection().fromContainerPixelToLatLng(new google.maps.Point(e.pageX-that.mouseX, e.pageY-that.mouseY));
                // e.clientX e.clientY
                //alert('mousedown e.clientX' + e.client + 'pageX=' + e.pageX);
                //that.hide();
                //pos = that.getProjection().fromDivPixelToLatLng(new google.maps.Point(div.offsetLeft+e.layerX,div.offsetTop+e.layerY));
                //pos = that.getProjection().fromDivPixelToLatLng(new google.maps.Point(e.pageX-div.offsetLeft,e.pageY-div.offsetTop));
                //pos = that.getProjection().fromDivPixelToLatLng(new google.maps.Point(e.clientX+map.div_.offsetLeft,e.clientY+map.div_.offsetTop));
                that.setPosition(pos);
                //that.mouseX = e.pageX;
                //that.mouseY = e.pageY;
                //that.show();
            }, true);

            this.mulistener_ = google.maps.event.addDomListenerOnce(window, "click", function(ev) 
            {
                var e=ev||event;

                if (that.firstdown_ == 1)
                {
                    that.firstdown_ = 0;
                    google.maps.event.trigger(that, "dragend",  that.getPosition());
                    google.maps.event.clearListeners(window, "mousemove");
                    that.mmlistener_ = 0;
                    google.maps.event.removeListener(that.mulistener_);
                    that.mulistener_ = null;
                }
                else
                {
                    that.firstdown_ = 1;
                }
            });    
        });

    }
}

ELabel.prototype.setOpacity = function(percentOpacity) 
{
    if (percentOpacity) 
    {
          if(percentOpacity<0){percentOpacity=0;}
          if(percentOpacity>100){percentOpacity=100;}
    }        
    this.percentOpacity = percentOpacity;
    if (this.percentOpacity) 
    {
        if(typeof(this.div_.style.filter)=='string')
            {this.div_.style.filter='alpha(opacity:'+this.percentOpacity+')';}
        if(typeof(this.div_.style.KHTMLOpacity)=='string')
            {this.div_.style.KHTMLOpacity=this.percentOpacity/100;}
        if(typeof(this.div_.style.MozOpacity)=='string')
            {this.div_.style.MozOpacity=this.percentOpacity/100;}
        if(typeof(this.div_.style.opacity)=='string')
            {this.div_.style.opacity=this.percentOpacity/100;}
    }
}

ELabel.prototype.getPosition = function() 
{
    return this.position;
}
