
var all_enums = {
	comType          : [ 'unknown', 'OLC', 'Free', 'RACE', 'Route', 'Team-RACE', 'RACE-handicap' ],
	comEntryRestrict : [ 'open', 'registered' ],
	comOverallScore  : [ 'all', 'ftv', 'round' ],
	comTeamScoring   : [ 'aggregate', 'team-gap', 'handicap' ],
	comTeamOver      : [ 'best', 'selected' ],
    comClass         : [ 'PG','HG','mixed' ],
    forClass         : [ 'gap', 'ozgap', 'pwc', 'sahpa', 'nzl', 'ggap', 'nogap', 'jtgap', 'rtgap', 'timegap' ],
    forArrival       : [ 'none', 'place', 'timed' ],
    forDeparture     : [ 'none', 'departure', 'leadout', 'kmbonus' ],
    forDistMeasure   : [ 'average', 'median' ],
    forDiffRamp      : [ 'fixed', 'flexible' ],
    forDiffCalc      : [ 'all', 'lo' ],
    forStoppedElapsedCalc : [ 'atstopped', 'shortesttime' ],
    forWeightDist    : [ 'pre2014', 'post2014' ],
    tasTaskType      : [ 'free', 'speedrun', 'race', 'olc', 'free-bearing', 'speedrun-interval', 'airgain', 'aat', 'free-pin' ],
    tasDeparture     : [  'off', 'on', 'leadout', 'kmbonus'  ],
    tasArrival       : [  'off', 'on'  ],
    tasHeightBonus   : [  'off', 'on'  ],
    tawType          : [ 'waypoint', 'start', 'speed', 'endspeed', 'goal' ],
    tawHow           : [ 'entry', 'exit' ],
    tawShape         : [ 'circle', 'semicircle', 'line' ]
};

function is_selectable(name)
{
    return all_enums.hasOwnProperty(name);
}

function selectable(name, value)
{
    if (all_enums.hasOwnProperty(name))
    {
        var nc;
        var res = '<select id="' + name +'" class="form-control form-control-sm" placeholder=".form-control-sm" onblur="td_blur(event);">';
        for (nc = 0; nc < all_enums[name].length; nc++)
        {
            if (value == all_enums[name][nc])
            {
                res += '<option value="' + all_enums[name][nc] + '" selected>' + all_enums[name][nc] + '</option>';
            }
            else
            {
                res += '<option value="' + all_enums[name][nc] + '">' + all_enums[name][nc] + '</option>';
            }
        }
        res += '</select>';

        return res;
    }
    else
    {
        return undefined;
    }
}
function td_edit(event,item)
{
    var sel = selectable(item);
    var val = event.srcElement.innerText;
    event.srcElement.innerHTML = sel;
}
function td_blur(event)
{
    var src = event.srcElement;
    var val = src.options[src.selectedIndex].text;
    src.parentElement.innerHTML = val;
}
function add_td(div, key, val)
{
    if (is_selectable(key))
    {
        div.append('<tr><td><b>'+key.substr(3)+"</b></td><td onclick=\"td_edit(event,'"+key+"');\">"+val+'</td></tr>');
    }
    else
    {
        div.append('<tr><td><b>'+key.substr(3)+'</b></td><td contenteditable="true">'+val+'</td></tr>');
    }
}
function create_td(key, val)
{
    if (is_selectable(key))
    {
        return "<td onclick=\"td_edit('"+key+"');\">"+val+'</td>';
    }
    else
    {
        return '<td contenteditable="true">'+val+'</td>';
    }
}

function update_classes(com_class)
{
    if (com_class == 'PG')
    {
        var pg = { Novice: 'A', Fun: 'B', Sports: 'C', Serial: 'D', Competition: 'CCC' };
        $('#dhv option').remove();
        $('#dhv').append("<option value=\"\" selectd>Open</option>");
        $.each(pg, function (key, val) {
            $('#dhv').append("<option value=\""+val+"\">" + key + "</option>");
        });
        $('#dhv').val('');
    }
    else if (com_class == 'HG')
    {
        var hg = { Floater: 'A', Kingpost: 'B', Rigid: 'C' };
        $('#dhv option').remove();
        $('#dhv').append("<option value=\"\" selectd>Open</option>");
        $.each(hg, function (key, val) {
            $('#dhv').append("<option value=\""+val+"\">" + key + "</option>");
        });
        $('#dhv').val('');
    }
}

