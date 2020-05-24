function url_parameter(sParam)
{
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++) 
    {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == sParam) 
        {
            return sParameterName[1];
        }
    }
    return 0;
}
/**
 * JavaScript printf/sprintf functions.
 *
 * This code is unrestricted: you are free to use it however you like.
 * @version 2007.04.27
 * @author Ash Searle
 */
function sprintf() {
    function pad(str, len, chr, leftJustify) {
    var padding = (str.length >= len) ? '' : Array(1 + len - str.length >>> 0).join(chr);
    return leftJustify ? str + padding : padding + str;

    }

    function justify(value, prefix, leftJustify, minWidth, zeroPad) {
    var diff = minWidth - value.length;
    if (diff > 0) {
        if (leftJustify || !zeroPad) {
        value = pad(value, minWidth, ' ', leftJustify);
        } else {
        value = value.slice(0, prefix.length) + pad('', diff, '0', true) + value.slice(prefix.length);
        }
    }
    return value;
    }

    function formatBaseX(value, base, prefix, leftJustify, minWidth, precision, zeroPad) {
    // Note: casts negative numbers to positive ones
    var number = value >>> 0;
    prefix = prefix && number && {'2': '0b', '8': '0', '16': '0x'}[base] || '';
    value = prefix + pad(number.toString(base), precision || 0, '0', false);
    return justify(value, prefix, leftJustify, minWidth, zeroPad);
    }

    function formatString(value, leftJustify, minWidth, precision, zeroPad) {
    if (precision != null) {
        value = value.slice(0, precision);
    }
    return justify(value, '', leftJustify, minWidth, zeroPad);
    }

    var a = arguments, i = 0, format = a[i++];
    return format.replace(sprintf.regex, function(substring, valueIndex, flags, minWidth, _, precision, type) {
        if (substring == '%%') return '%';

        // parse flags
        var leftJustify = false, positivePrefix = '', zeroPad = false, prefixBaseX = false;
        for (var j = 0; flags && j < flags.length; j++) switch (flags.charAt(j)) {
        case ' ': positivePrefix = ' '; break;
        case '+': positivePrefix = '+'; break;
        case '-': leftJustify = true; break;
        case '0': zeroPad = true; break;
        case '#': prefixBaseX = true; break;
        }

        // parameters may be null, undefined, empty-string or real valued
        // we want to ignore null, undefined and empty-string values

        if (!minWidth) {
        minWidth = 0;
        } else if (minWidth == '*') {
        minWidth = +a[i++];
        } else if (minWidth.charAt(0) == '*') {
        minWidth = +a[minWidth.slice(1, -1)];
        } else {
        minWidth = +minWidth;
        }

        // Note: undocumented perl feature:
        if (minWidth < 0) {
        minWidth = -minWidth;
        leftJustify = true;
        }

        if (!isFinite(minWidth)) {
        throw new Error('sprintf: (minimum-)width must be finite');
        }

        if (!precision) {
        precision = 'fFeE'.indexOf(type) > -1 ? 6 : (type == 'd') ? 0 : void(0);
        } else if (precision == '*') {
        precision = +a[i++];
        } else if (precision.charAt(0) == '*') {
        precision = +a[precision.slice(1, -1)];
        } else {
        precision = +precision;
        }

        // grab value using valueIndex if required?
        var value = valueIndex ? a[valueIndex.slice(0, -1)] : a[i++];

        switch (type) {
        case 's': return formatString(String(value), leftJustify, minWidth, precision, zeroPad);
        case 'c': return formatString(String.fromCharCode(+value), leftJustify, minWidth, precision, zeroPad);
        case 'b': return formatBaseX(value, 2, prefixBaseX, leftJustify, minWidth, precision, zeroPad);
        case 'o': return formatBaseX(value, 8, prefixBaseX, leftJustify, minWidth, precision, zeroPad);
        case 'x': return formatBaseX(value, 16, prefixBaseX, leftJustify, minWidth, precision, zeroPad);
        case 'X': return formatBaseX(value, 16, prefixBaseX, leftJustify, minWidth, precision, zeroPad).toUpperCase();
        case 'u': return formatBaseX(value, 10, prefixBaseX, leftJustify, minWidth, precision, zeroPad);
        case 'i':
        case 'd': {
                  var number = parseInt(+value);
                  var prefix = number < 0 ? '-' : positivePrefix;
                  value = prefix + pad(String(Math.abs(number)), precision, '0', false);
                  return justify(value, prefix, leftJustify, minWidth, zeroPad);
              }
        case 'e':
        case 'E':
        case 'f':
        case 'F':
        case 'g':
        case 'G':
                  {
                  var number = +value;
                  var prefix = number < 0 ? '-' : positivePrefix;
                  var method = ['toExponential', 'toFixed', 'toPrecision']['efg'.indexOf(type.toLowerCase())];
                  var textTransform = ['toString', 'toUpperCase']['eEfFgG'.indexOf(type) % 2];
                  value = prefix + Math.abs(number)[method](precision);
                  return justify(value, prefix, leftJustify, minWidth, zeroPad)[textTransform]();
              }
        default: return substring;
        }
            });
}
sprintf.regex = /%%|%(\d+\$)?([-+#0 ]*)(\*\d+\$|\*|\d+)?(\.(\*\d+\$|\*|\d+))?([scboxXuidfegEG])/g;

/**
 * Trival printf implementation, probably only useful during page-load.
 * Note: you may as well use "document.write(sprintf(....))" directly
 */
function printf() {
    // delegate the work to sprintf in an IE5 friendly manner:
    var i = 0, a = arguments, args = Array(arguments.length);
    while (i < args.length) args[i] = 'a[' + (i++) + ']';
    document.write(eval('sprintf(' + args + ')'));
}
function post(path, params, method) {
    method = method || "post"; // Set method to post by default if not specified.

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", path);

    for (var key in params) {
        if(params.hasOwnProperty(key)) {
            var hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", key);
            hiddenField.setAttribute("value", params[key]);

            form.appendChild(hiddenField);
        }
    }

    document.body.appendChild(form);
    form.submit();
}
function format_seconds(tm)
{
    var h, m, s;

    if (tm < 0)
    {
        tm = tm + 86400;
    }
    h = (tm / 3600) % 24;
    m = (tm / 60) % 60;
    s = tm % 60;

    return sprintf("%02d:%02d:%02d", h, m, s);
}
function today()
{
    var today = new Date();
    var dd = today.getDate();
    var mm = today.getMonth()+1; //January is 0!
    var yyyy = today.getFullYear();
    if (dd<10) {
        dd = '0'+dd
    } 
    if (mm<10) {
        mm = '0'+mm
    } 
    today = yyyy + '-' + mm + '-' + dd;
    return today;
}
function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}
