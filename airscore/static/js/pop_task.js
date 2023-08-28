function populate_task(json){
    $('#comp_name').text('Loading Results ...');
    var columns = [];
    let other_types = ['abs', 'nyp', 'dnf'];
    let data = json.results.filter( el => !other_types.includes(el.result_type) );
    // Rankings
    json.rankings.forEach( function(item, index) {
      columns.push({data: 'rankings.'+item.rank_id.toString(), title: '#', name: item.rank_id.toString(), className: "text-right", defaultContent: '', visible: (index === 0) ? true : false});
    });
    columns.push({data: 'ID', title: 'ID', className: "text-right", defaultContent: ''});
    columns.push({data: 'fai_id', title: 'FAI', className: "text-right", defaultContent: '', visible: false});
    columns.push({data: 'civl_id', title: 'CIVL', className: "text-right", defaultContent: '', visible: false});
    columns.push({data: 'name', title: 'Name'});
    columns.push({data: 'nat', title: 'NAT', name:'NAT', defaultContent: ''});
    columns.push({data: 'sex', title: 'Sex', defaultContent: '', visible: false});
    columns.push({data: 'glider', title:' Equip', defaultContent: ''});
    columns.push({data: 'glider_cert', title: 'Class', defaultContent: '', visible: false});
    columns.push({data: 'sponsor', title:' Sponsor', defaultContent: ''});
    //hide SS ES for Race
    if(json.info.task_type=='race' && json.info.SS_interval==0){
        columns.push({data: 'SSS_time', title: 'SS', defaultContent: '', visible: false});
        columns.push({data: 'ESS_time', title: 'ES', defaultContent: '', visible: false});
    }
    else {
        columns.push({data: 'SSS_time', title: 'SS', defaultContent: ''});
        columns.push({data: 'ESS_time', title: 'ES', defaultContent: ''});
    }
    columns.push({data: 'ss_time', title:' Time', defaultContent: ''});
    columns.push({data: 'speed', title: 'Kph', className: "text-right", defaultContent: ''});
    //altitude column if task is stopped
    if(json.info.stopped_time) {
      columns.push({data: 'stopped_altitude', title: 'Alt', className: "text-right", defaultContent: ''});
    }
    columns.push({data: 'distance', title: 'Dist', className: "text-right", defaultContent: ''});
    columns.push({data: 'time_score', title: 'TimeP', className: "text-right", defaultContent: ''});
    columns.push({data: 'departure_score', title: 'LoP', className: "text-right", defaultContent: ''});
    //add Arrival only when used
    if(json.formula.formula_arrival!='off'){
        columns.push({data: 'arrival_score', title: 'ArrP', className: "text-right", defaultContent: ''});
    }
    columns.push({data: 'distance_score', title: 'DstP', className: "text-right", defaultContent: ''});
    columns.push({data: 'penalty', title: 'PenP', className: "text-right", defaultContent: ''});
    columns.push({data: 'score', title: 'Score', className: "text-right", defaultContent: ''});
    $('#results_table').DataTable( {
        data: data,
        paging: false,
        searching: true,
        saveState: true,
        info: false,
        dom: 'lrtip',
        columns: columns,
        rowId: function(data) {
            return 'id_' + data.par_id;
        },
        "initComplete": function(settings) {
            var table = $('#results_table');
            var rows = $("tr", table).length-1;
            // Get number of all columns
            var numCols = $('#results_table').DataTable().columns().nodes().length;
            console.log('numCols='+numCols);
            // remove empty cols and NAT if all pilots are from a single country
            var natId = table.DataTable().column('NAT:name').index();
            var natRef = table.DataTable().column(natId).data()[0];
            for ( var col=1; col<numCols; col++ ) {
                var empty = true;
                table.DataTable().column(col).data().each( val => {
                    if (col == natId) {
                        if (val != natRef) {
                            empty = false;
                        }
                    }
                    else {
                        if (val != "") {
                            empty = false;
                        }
                    }
                    if (!empty) {
                        return false;
                    }
                } );

                if (empty) {
                    table.DataTable().column( col ).visible( false );
                }
            }
            // comp info
            $('#comp_name').text(json.info.comp_name + " - " + json.info.task_name);
            $('#task_date').text(json.info.date + ' ' + json.info.task_type);
            $('#status').text(json.file_stats.status);
            // times
            var tbl = document.createElement('table');
            tbl.className="times-list";
            if (json.info.startgates.length > 1) {
                json.info.startgates.forEach((el, i) => {
                    let row = tbl.insertRow();
                    let cell1 = row.insertCell();
                    if (i==0) {
                        cell1.className="times-list";
                        cell1.innerHTML = '<b>Startgates:</b>';
                    }
                    else {
                        cell1.appendChild(document.createTextNode('\u0020'));
                    }
                    let cell2 = row.insertCell();
                    cell2.className="times-list";
                    cell2.innerHTML = (i+1) + '. <b>' + el + '</b>';
                });
            }
            else {
                let row = tbl.insertRow();
                let cell1 = row.insertCell();
                cell1.className="times-list";
                cell1.innerHTML = '<b>Startgate:</b>';
                let cell2 = row.insertCell();
                cell2.className="times-list";
                cell2.innerHTML = '<b>' + json.info.start_time + '</b>';
            }
            if (json.info.stopped_time) {
                let row = tbl.insertRow();
                let cell1 = row.insertCell();
                cell1.className="times-list red";
                cell1.innerHTML = '<b>Stopped:</b>';
                let cell2 = row.insertCell();
                cell2.className="times-list red";
                cell2.innerHTML = '<b>' + json.info.stopped_time + '</b>';
            }
            else {
                let row = tbl.insertRow();
                let cell1 = row.insertCell();
                cell1.className="times-list";
                cell1.innerHTML = '<b>Task Deadline: </b>';
                let cell2 = row.insertCell();
                cell2.className="times-list";
                cell2.innerHTML = '<b>' + json.info.task_deadline + '</b>'
            }
            $('#comp_header').append(tbl);
            // waypoints
            var tbl = document.getElementById('waypoints');
            tbl.classList.add('wpt-list');
            var body = tbl.getElementsByTagName('tbody')[0];
            json.route.forEach(wpt => {
                let row = body.insertRow();
                let list = [ wpt.name, (wpt.type + ' ' + wpt.shape), wpt.radius, wpt.cumulative_dist, wpt.description];
                list.forEach(el => {
                    let cell = row.insertCell();
                    cell.classList.add('wpt-list');
                    cell.innerHTML = el;
                });
            });
            // comments
            if (json.results.some(e => e.penalty != 0)) {
                $('#comments').append('<a class="badge badge-info mb-2" href="/task_airspace/'+json.info.id+'">Parameters</a>');
                let tbl = document.createElement('table');
                tbl.classList.add('comment_list');
                let filtered = json.results.filter(e => e.penalty != 0);
                filtered.forEach(pilot => {
                    let row = tbl.insertRow();
                    [ pilot.name + ': ', pilot.comment ].forEach(el => {
                        let cell = row.insertCell();
                        cell.classList.add('comment_list');
                        cell.innerHTML = el;
                    });
                });
                $('#comments').append(tbl);
            }
            else {
              $('#comments').addClass('hidden');
            }
            // other pilots
            if (json.results.some(e => other_types.includes(e.result_type))) {
                let tbl = document.createElement('table');
                tbl.classList.add('other_pilots_list');
                let filtered = json.results.filter(e => other_types.includes(e.result_type));
                filtered.forEach(pilot => {
                    let row = tbl.insertRow();
                    [ pilot.name, pilot.result_type ].forEach(el => {
                        let cell = row.insertCell();
                        cell.classList.add('other_pilots_list');
                        cell.innerHTML = el;
                    });
                });
                $('#other_pilots').append(tbl);
            }
            else {
              $('#other_pilots').addClass('hidden');
            }
            // task info
            var half = Object.keys(json.formula).length / 2;
            var count = 0;
            $.each( json.formula, function( key, value ) {
                if (count < half)
                {
                    $('#formula_left tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
                }
                else
                {
                    $('#formula_right tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
                }
                count++;
            });
            // adding SS_distance info as it changes based on scoring system (2023)
            $.each( json.info, function( key, value ) {
                if ( key == 'SS_distance' )
                {
                    $('#taskinfo tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
                }
            });
            $.each( json.stats, function( key, value ) {
                $('#taskinfo tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
            });
            // created date
            let created_date = document.createTextNode('Results created: ' + json.file_stats.timestamp + ' (Local Time)');
            $('#created').append(created_date);
            // class picker
            $("#dhv option").remove(); // Remove all <option> child tags.
            // at the moment we provide the highest EN rating for a class and the overall_class_filter.js uses this.
            // if we want to be more specific and pass a list of all EN ratings inside a class we can do something like this: https://stackoverflow.com/questions/15759863/get-array-values-from-an-option-select-with-javascript-to-populate-text-fields
            $.each(json.rankings, function(index, item) {
                $("#dhv").append(
                    $("<option></option>")
                        .text(item.rank_name)
                        .val(item.rank_id)
                );
            });
        }
    });
}
