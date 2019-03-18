/*	Google Maps API HtmlControl v1.1.2
	based on code posted on Google Maps API discussion group
	last updated/modified by Martin Pearman 20th August 2008
	
	http://googlemapsapi.martinpearman.co.uk/htmlcontrol
	
	This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

	This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

	You should have received a copy of the GNU General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

function HtmlControl(html, options){
	this.html=html;
	this.isVisible=true;
	this.isPrintable=false;	
	this.isSelectable=false;
	if(options){
		this.isVisible=(options.visible===false)?false:true;
		this.isPrintable=(options.printable===true)?true:false;
		this.isSelectable=(options.selectable===true)?true:false;
	}
}
HtmlControl.prototype=new GControl();
HtmlControl.prototype.initialize=function(map){
	this.div=document.createElement('div');
	this.div.innerHTML=this.html;
	this.setVisible(this.isVisible);
	map.getContainer().appendChild(this.div);
	return this.div;
};
HtmlControl.prototype.getDefaultPosition=function(){
	return new GControlPosition(G_ANCHOR_TOP_LEFT, new GSize(7,7));
};
HtmlControl.prototype.selectable=function(){
	return this.isSelectable;
};
HtmlControl.prototype.printable=function(){
	return this.isPrintable;
};
HtmlControl.prototype.setVisible=function(bool){
	this.div.style.display=bool ? '':'none';
	this.isVisible=bool;
};
HtmlControl.prototype.visible=function(){
	return this.isVisible;
}
