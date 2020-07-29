
function populate_task(taskid){
    $(document).ready(function() {
        $('#comp_name').text('Calculating Results ...');
        $.ajax({
            type: "POST",
            url: '/_get_task_result/'+taskid,
            contentType:"application/json",
            dataType: "json",
            success: function (json) {
                var columns = [];
                json.classes.forEach( function(item, index) {
                    if (index == 0) {
                        columns.push({data: 'ranks.rank', title:'#'});
                    }
                    else {
                        columns.push({data: 'ranks.class'+index.toString(), title:'#', defaultContent: '', visible: false});
                    }
                });
                columns.push({data: 'fai_id', title:'FAI', defaultContent: '', visible: false});
                columns.push({data: 'civl_id', title:'CIVL', defaultContent: '', visible: false});
                columns.push({data: 'name', title:'Name'});
                columns.push({data: 'nat', title:'NAT', defaultContent: ''});
                columns.push({data: 'sex', title:'Sex', defaultContent: '', visible: false});
                columns.push({data: 'glider', title:'Glider', defaultContent: ''});
                columns.push({data: 'glider_cert', title:'Class', defaultContent: '', visible: false});
                columns.push({data: 'sponsor', title:'Sponsor', defaultContent: ''});
                //hide SS ES for Race
                if(json.info.task_type=='RACE' && json.info.SS_interval==0){
                    columns.push({data: 'SSS_time', title:'SS', defaultContent: '', visible: false});
                    columns.push({data: 'ESS_time', title:'ES', defaultContent: '', visible: false});
                }
                else {
                    columns.push({data: 'SSS_time', title:'SS', defaultContent: ''});
                    columns.push({data: 'ESS_time', title:'ES', defaultContent: ''});
                }
                columns.push({data: 'ss_time', title:'Time', defaultContent: ''});
                columns.push({data: 'speed', title:'Kph', defaultContent: ''});
                columns.push({data: 'distance', title:'Dist', defaultContent: ''});
                columns.push({data: 'time_score', title:'TimeP', defaultContent: ''});
                columns.push({data: 'departure_score', title:'LoP', defaultContent: ''});
                //add Arrival only when used
                if(json.formula.formula_arrival!='off'){
                    columns.push({data: 'arrival_score', title:'ArrP', defaultContent: ''});
                }
                columns.push({data: 'distance_score', title:'DstP', defaultContent: ''});
                columns.push({data: 'penalty', title:'PenP', defaultContent: ''});
                columns.push({data: 'score', title:'Score', defaultContent: ''});
                $('#results_table').DataTable( {
                    data: json.data,
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
                        // remove empty cols
                        for ( var i=1; i<numCols; i++ ) {
                            var empty = true;
                            table.DataTable().column(i).data().each( function (e, i) {
                                if (e != "") {
                                    empty = false;
                                    return false;
                                }
                            } );
                            if (empty) {
                                table.DataTable().column( i ).visible( false );
                            }
                        }
                        // comp info
                        $('#comp_name').text(json.info.comp_name + " - " + json.info.task_name);
                        $('#task_date').text(json.info.date + ' ' + json.info.task_type);
                        // times
                        var tbl = document.createElement('table');
                        var tbdy = document.createElement('tbody');
                        if (json.info.startgates.length > 1) {
                            for (var i=0; i < json.info.startgates.length; i++) {
                                var tr = document.createElement('tr');
                                var td = document.createElement('td');
                                if (i==0) {
                                    td.innerHTML = '<b>Startgates:</b>'
                                }
                                else {
                                    td.appendChild(document.createTextNode('\u0020'))
                                }
                                tr.appendChild(td)
                                var td = document.createElement('td');
                                td.style.textAlign = "right";
                                td.innerHTML = (i+1) + '. <b>' + json.info.startgates[i] + '</b>'
                                tr.appendChild(td);
                                tbdy.appendChild(tr);
                            }
                        }
                        else {
                            var tr = document.createElement('tr');
                            var td = document.createElement('td');
                            td.innerHTML = '<b>Startgate:</b>'
                            tr.appendChild(td);
                            var td = document.createElement('td');
                            td.style.textAlign = "right";
                            td.innerHTML = '<b>' + json.info.start_time + '</b>'
                            tr.appendChild(td);
                            tbdy.appendChild(tr);
                        }
                        if (json.info.stopped_time) {
                            var tr = document.createElement('tr');
                            var td = document.createElement('td');
                            td.innerHTML = '<b>Stopped: </b>'
                            tr.appendChild(td);
                            var td = document.createElement('td');
                            td.style.textAlign = "right";
                            td.innerHTML = '<b>' + json.info.stopped_time + '</b>'
                            tr.appendChild(td)
                        }
                        else {
                            var tr = document.createElement('tr');
                            var td = document.createElement('td');
                            td.innerHTML = '<b>Task Deadline: </b>'
                            tr.appendChild(td);
                            var td = document.createElement('td');
                            td.style.textAlign = "right";
                            td.innerHTML = '<b>' + json.info.task_deadline + '</b>'
                            tr.appendChild(td);
                        }
                        tbdy.appendChild(tr);
                        tbl.appendChild(tbdy);
                        $('#comp_header').append(tbl);
                        // waypoints
                        for (var c=0; c < json.route.length; c++) {
                            var tr = document.createElement('tr');
                            // name
                            var td = document.createElement('td');
                            td.innerHTML = json.route[c].name
                            tr.appendChild(td);
                            // type
                            var td = document.createElement('td');
                            td.innerHTML = json.route[c].type + ' ' + json.route[c].shape
                            tr.appendChild(td);
                            // radius
                            var td = document.createElement('td');
                            td.style.textAlign = "right";
                            td.innerHTML = json.route[c].radius;
                            tr.appendChild(td);
                            // cumulative distance
                            var td = document.createElement('td');
                            td.style.textAlign = "right";
                            td.innerHTML = json.route[c].cumulative_dist;
                            tr.appendChild(td);
                            // description
                            var td = document.createElement('td');
                            td.innerHTML = json.route[c].description;
                            tr.appendChild(td);
                            $('#waypoints tbody').append(tr);
                        }
                        // comments
                        if (json.results.some(e => e.penalty != 0)) {
                            var tbl = document.createElement('table');
                            tbl.classList.add('comment_table');
                            var tbdy = document.createElement('tbody');
                            var filtered = json.results.filter(e => e.penalty != 0);
                            filtered.forEach(pilot => {
                                var tr = document.createElement('tr');
                                var td = document.createElement('td');
                                td.classList.add('comment_name');
                                td.innerHTML = '<b>' + pilot.name + ': </b>';
                                tr.appendChild(td);
                                var td = document.createElement('td');
                                td.classList.add('comment_text');
                                td.style.paddingLeft = "5px";
                                td.innerHTML = pilot.comment;
                                tr.appendChild(td);
                                tbdy.appendChild(tr);
                            });
                            tbl.appendChild(tbdy);
                            $('#comments').append(tbl);
                        }
                        // task info
                        var half = Object.keys(json.formula).length / 2;
                        var count = 0;
                        $.each( json.formula, function( key, value ) {
                            if (count < half)
                            {
                                $('#formula1 tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
                            }
                            else
                            {
                                $('#formula2 tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
                            }
                            count++;
                        });
                        $.each( json.stats, function( key, value ) {
                            $('#taskinfo tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
                        });
                        // class picker
                        $("#dhv option").remove(); // Remove all <option> child tags.
                        // at the moment we provide the highest EN rating for a class and the overall_class_filter.js uses this.
                        // if we want to be more specific and pass a list of all EN ratings inside a class we can do something like this: https://stackoverflow.com/questions/15759863/get-array-values-from-an-option-select-with-javascript-to-populate-text-fields
                        $.each(json.classes, function(index, item) {
                            $("#dhv").append(
                                $("<option></option>")
                                    .text(item.name)
                                    .val(item.limit)
                            );
                        });
                    }
                });
            }
        });
    });
}





//function populate_task(tasPk){
//$(document).ready(function() {
//    $('#results_table').dataTable({
//        ajax: '/_get_task_result/'+tasPk,
//        paging: false,
//        searching: true,
//        saveState: true,
//        info: false,
//        "dom": 'lrtip',
//        columns: [
//            {data: 'ranks.rank', title:'#'},
//            {data: 'ranks.class1', title:'#', defaultContent: ''},
//            {data: 'ranks.class2', title:'#', defaultContent: ''},
//            {data: 'ranks.class3', title:'#', defaultContent: ''},
//            {data: 'ranks.class4', title:'#', defaultContent: ''},
//            {data: 'fai_id', title:'FAI'},
//            {data: 'civl_id', title:'CIVL'},
//            {data: 'name', title:'Name'},
//            {data: 'nat', title:'NAT'},
//            {data: 'sex', title:'Sex'},
//            {data: 'glider', title:'Glider'},
//            {data: 'glider_cert', title:'EN'},
//            {data: 'sponsor', title:'Sponsor'},
//            {data: 'SSS_time', title:'SS', defaultContent: ''},
//            {data: 'ESS_time', title:'ES', defaultContent: ''},
//            {data: 'ss_time', title:'Time', defaultContent: ''},
//            {data: 'speed', title:'Kph', defaultContent: ''},
//            {data: 'distance', title:'Dist', defaultContent: ''},
//            {data: 'time_score', title:'TimeP', defaultContent: ''},
//            {data: 'departure_score', title:'LoP', defaultContent: ''},
//            {data: 'arrival_score', title:'ArrP', defaultContent: ''},
//            {data: 'distance_score', title:'DstP', defaultContent: ''},
//            {data: 'penalty', title:'PenP', defaultContent: ''},
//            {data: 'score', title:'Score', defaultContent: ''}
//        ],
//        rowId: function(data) {
//            return 'id_' + data.par_id;
//        },
//        "columnDefs": [
//            {
//                "targets": [ 1, 2, 3, 4, 5, 6, 9, 11 ],
////                    "targets": [ 5, 7 ],
//                "visible": false
//            },
//            //{ "type" : "numeric", "targets": [ 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 ] }
//        ],
//
//        "initComplete": function(settings, json) {
//            var table = $('#results_table');
//            var rows = $("tr", table).length-1;
////            var numCols = $("th", table).length;
//            // Get number of all columns
//            var numCols = $('#results_table').DataTable().columns().nodes().length;
//            console.log('numCols='+numCols);
//
//            //hide SS ES for Race
//            if(json.info.task_type=='RACE' && json.info.SS_interval==0){
//                $('#results_table').DataTable().column(13).visible( false );
//                $('#results_table').DataTable().column(14).visible( false );
//            }
//            //hide Arrival when not used
//            if(json.formula.formula_arrival=='off'){
//                $('#results_table').DataTable().column(20).visible( false );
//            }
//
//            // remove empty cols
//            for ( var i=1; i<numCols; i++ ) {
//                var empty = true;
//                table.DataTable().column(i).data().each( function (e, i) {
//                    if (e != "") {
//                        empty = false;
//                        return false;
//                    }
//                } );
//
//                if (empty) {
//                    table.DataTable().column( i ).visible( false );
//                }
//            }
//
//            // comp info
//            $('#comp_name').text(json.info.comp_name + " - " + json.info.task_name);
//            $('#task_date').text(json.info.date + ' ' + json.info.task_type);
//
//            // times
//            var tbl = document.createElement('table');
//            var tbdy = document.createElement('tbody');
//            if (json.info.startgates.length > 1)
//            {
//                for (var i=0; i < json.info.startgates.length; i++)
//                {
//                    var tr = document.createElement('tr');
//                    var td = document.createElement('td');
//                    if (i==0)
//                    {
//                        td.innerHTML = '<b>Startgates:</b>'
//                    }
//                    else
//                    {
//                        td.appendChild(document.createTextNode('\u0020'))
//                    }
//                    tr.appendChild(td)
//                    var td = document.createElement('td');
//                    td.style.textAlign = "right";
//                    td.innerHTML = (i+1) + '. <b>' + json.info.startgates[i] + '</b>'
//                    tr.appendChild(td);
//                    tbdy.appendChild(tr);
//                }
//            }
//            else
//            {
//                var tr = document.createElement('tr');
//                var td = document.createElement('td');
//                td.innerHTML = '<b>Startgate:</b>'
//                tr.appendChild(td);
//                var td = document.createElement('td');
//                td.style.textAlign = "right";
//                td.innerHTML = '<b>' + json.info.start_time + '</b>'
//                tr.appendChild(td);
//                tbdy.appendChild(tr);
//            }
//            if (json.info.stopped_time)
//            {
//                var tr = document.createElement('tr');
//                var td = document.createElement('td');
//                td.innerHTML = '<b>Stopped: </b>'
//                tr.appendChild(td);
//                var td = document.createElement('td');
//                td.style.textAlign = "right";
//                td.innerHTML = '<b>' + json.info.stopped_time + '</b>'
//                tr.appendChild(td)
//            }
//            else
//            {
//                var tr = document.createElement('tr');
//                var td = document.createElement('td');
//                td.innerHTML = '<b>Task Deadline: </b>'
//                tr.appendChild(td);
//                var td = document.createElement('td');
//                td.style.textAlign = "right";
//                td.innerHTML = '<b>' + json.info.task_deadline + '</b>'
//                tr.appendChild(td);
//            }
//            tbdy.appendChild(tr);
//            tbl.appendChild(tbdy);
//            $('#comp_header').append(tbl);
//
//            // waypoints
//            for (var c=0; c < json.route.length; c++)
//            {
//                var tr = document.createElement('tr');
//                // name
//                var td = document.createElement('td');
//                td.innerHTML = json.route[c].name
//                tr.appendChild(td);
//                // type
//                var td = document.createElement('td');
//                td.innerHTML = json.route[c].type + ' ' + json.route[c].shape
//                tr.appendChild(td);
//                // radius
//                var td = document.createElement('td');
//                td.style.textAlign = "right";
//                td.innerHTML = json.route[c].radius;
//                tr.appendChild(td);
//                // cumulative distance
//                var td = document.createElement('td');
//                td.style.textAlign = "right";
//                td.innerHTML = json.route[c].cumulative_dist;
//                tr.appendChild(td);
//                // description
//                var td = document.createElement('td');
//                td.innerHTML = json.route[c].description;
//                tr.appendChild(td);
//                $('#waypoints tbody').append(tr);
//            }
//
//            // comments
//            if (json.results.some(e => e.penalty != 0)) {
//                var tbl = document.createElement('table');
//                tbl.classList.add('comment_table');
//                var tbdy = document.createElement('tbody');
//                var filtered = json.results.filter(e => e.penalty != 0);
//                filtered.forEach(pilot => {
//                    var tr = document.createElement('tr');
//                    var td = document.createElement('td');
//                    td.classList.add('comment_name');
//                    td.innerHTML = '<b>' + pilot.name + ': </b>';
//                    tr.appendChild(td);
//                    var td = document.createElement('td');
//                    td.classList.add('comment_text');
//                    td.style.paddingLeft = "5px";
//                    td.innerHTML = pilot.comment;
//                    tr.appendChild(td);
//                    tbdy.appendChild(tr);
//                });
//                tbl.appendChild(tbdy);
//                $('#comments').append(tbl);
//            }
//
//            // task info
//            var half = Object.keys(json.formula).length / 2;
//            var count = 0;
//            $.each( json.formula, function( key, value ) {
//                if (count < half)
//                {
//                    $('#formula1 tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
//                }
//                else
//                {
//                    $('#formula2 tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
//                }
//                count++;
//            });
//
//            $.each( json.stats, function( key, value ) {
//                $('#taskinfo tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
//            });
//
//            // class picker
//            $("#dhv option").remove(); // Remove all <option> child tags.
//            // at the moment we provide the highest EN rating for a class and the overall_class_filter.js uses this.
//            // if we want to be more specific and pass a list of all EN ratings inside a class we can do something like this: https://stackoverflow.com/questions/15759863/get-array-values-from-an-option-select-with-javascript-to-populate-text-fields
//            $.each(json.classes, function(index, item) {
//                $("#dhv").append(
//                    $("<option></option>")
//                        .text(item.name)
//                        .val(item.limit)
//                      );
//      });
//        }
//    });
//});
//}