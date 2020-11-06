
function populate_ladder(ladderid, season){
    $(document).ready(function() {
        $('#comp_name').text('Loading Results ...');
        $.ajax({
            type: "POST",
            url: '/_get_ladder_result/'+ladderid+'/'+season,
            contentType:"application/json",
            dataType: "json",
            success: function (json) {
                var taskNum = json.stats.valid_tasks
                console.log('taskNum='+taskNum);
                var columns = [];
                json.classes.forEach( function(item, index){
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
                columns.push({data: 'nat', title:'NAT', defaultContent: '', visible: false});
                columns.push({data: 'sex', title:'Sex', defaultContent: '', visible: false});
                columns.push({data: 'score', title:'Total'});
                for (var i=0; i<taskNum; i++ ) {
                    var col = (i+1)
                    columns.push({data: 'results.'+i.toString(), title: col.toString(), defaultContent: ''});
                }
                $('#results_table').DataTable( {
                    data: json.data,
                    paging: false,
                    searching: true,
                    saveState: true,
                    info: false,
                    "dom": 'lrtip',
                    columns: columns,
                    rowId: function(data) {
                            return 'id_' + data.par_id;
                    },
                    initComplete: function(settings) {
                        var table = $('#results_table');
                        var rows = $("tr", table).length-1;
                        // Get number of all columns
                        var numCols = table.DataTable().columns().nodes().length;
                        console.log('numCols='+numCols);
                        // ladder info
                        $('#comp_name').text(json.info.ladder_name);
                        $('#comp_date').text(json.info.season);
                        if (json.info.ladder_class != "PG") {
                            update_classes(json.info.ladder_class);
                        }
                        // comps list
                        if (json.comps.length > 0) {
                            let tbl = document.createElement('table');
                            tbl.className="tasks-list";
                            let thead = tbl.createTHead();
                            let row = thead.insertRow();
                            header = [ 'Event', 'Tasks' ];
                            header.forEach(el => {
                                let th = document.createElement("th");
                                th.className="tasks-list";
                                th.innerHTML = '<b>'+el+'</b>';
                                row.appendChild(th);
                            });
                            json.comps.forEach(comp => {
                                let row = tbl.insertRow();
                                [ comp.link, comp.tasks ].forEach(el => {
                                    let cell = row.insertCell();
                                    cell.className="tasks-list";
                                    cell.innerHTML = el;
                                });
                            });
                            $('#comp_header').append(tbl);
                        }
                        else {
                            let text = document.createTextNode('No task have been scored yet.');
                            $('#comp_header').append(text);
                        }
                        // some parameters
                        $('#formula tbody').append(
                                    "<tr><td>Overall Scoring</td><td>" + json.formula.overall_validity + ' (' + json.formula.validity_param + ')</td></tr>');
                        if (json.formula.overall_validity == 'ftv') {
                            $('#formula tbody').append(
                                    "<tr><td>Total Validity</td><td>" + json.stats.total_validity + '</td></tr>');
                        }
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
                        // created date
                        let created_date = document.createTextNode('Results created: ' + json.file_stats.timestamp + ' UTC');
                        $('#created').append(created_date);
                        console.log('date=' + json.file_stats.timestamp)
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
