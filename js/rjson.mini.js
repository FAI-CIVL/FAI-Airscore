var RJSON=(function(){'use strict';var hasOwnProperty=Object.prototype.hasOwnProperty,toString=Object.prototype.toString,getKeys=Object.keys||_keys,isArray=Array.isArray||_isArray;function pack(data){var schemas={},maxSchemaIndex=0;function encode(value){var encoded,i,j,k,v,current,last,len,schema,schemaKeys,schemaIndex;if(typeof value!=='object'||!value){return value;}
if(isArray(value)){len=value.length;if(len===0){return[];}
encoded=[];if(typeof value[0]==='number'){encoded.push(0);}
for(i=0;i<len;i++){v=value[i];current=encode(v);last=encoded[encoded.length-1];if(isEncodedObject(current)&&isArray(last)&&current[0]===last[0]){encoded[encoded.length-1]=last.concat(current.slice(1));}else{encoded.push(current);}}}else{schemaKeys=getKeys(value).sort();if(schemaKeys.length===0){return{};}
schema=schemaKeys.length+':'+schemaKeys.join('|');schemaIndex=schemas[schema];if(schemaIndex){encoded=[schemaIndex];for(i=0,k;k=schemaKeys[i++];){encoded[i]=encode(value[k]);}}else{schemas[schema]=++maxSchemaIndex;encoded={};for(i=0,k;k=schemaKeys[i++];){encoded[k]=encode(value[k]);}}}
return encoded;}
return encode(data);}
function unpack(data){var schemas={},maxSchemaIndex=0;function decode(value){var decoded,i,j,k,v,obj,schemaKeys,schemaLen,total,len;if(typeof value!=='object'||!value){return value;}
if(isArray(value)){len=value.length;if(len===0){decoded=[];}else if(value[0]===0||typeof value[0]!=='number'){decoded=[];for(i=(value[0]===0?1:0);i<len;i++){v=value[i];obj=decode(v);if(isEncodedObject(v)&&isArray(obj)){decoded=decoded.concat(obj);}else{decoded.push(obj);}}}else{schemaKeys=schemas[value[0]];schemaLen=schemaKeys.length;total=(value.length-1)/schemaLen;if(total>1){decoded=[];for(i=0;i<total;i++){obj={};for(j=0;k=schemaKeys[j++];){obj[k]=decode(value[i*schemaLen+j]);}
decoded.push(obj);}}else{decoded={};for(j=0,k;k=schemaKeys[j++];){decoded[k]=decode(value[j]);}}}}else{schemaKeys=getKeys(value).sort();if(schemaKeys.length===0){return{};}
schemas[++maxSchemaIndex]=schemaKeys;decoded={};for(i=0,k;k=schemaKeys[i++];){decoded[k]=decode(value[k]);}}
return decoded;}
return decode(data);}
function isEncodedObject(value){return isArray(value)&&typeof value[0]==='number'&&value[0]!==0;}
function _keys(obj){var keys=[],k;for(k in obj){if(hasOwnProperty.call(obj,k)){keys.push(k);}}
return keys;}
function _isArray(obj){return toString.apply(obj)==='[object Array]';}
return{pack:pack,unpack:unpack};}());if(typeof module!='undefined'&&module.exports){module.exports=RJSON;}