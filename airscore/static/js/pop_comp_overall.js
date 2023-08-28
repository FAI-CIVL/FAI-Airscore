function populate_comp_overall(json){
    $('#comp_name').text('Loading Results ...');
    var taskNum = json.stats.valid_tasks
    console.log('taskNum='+taskNum);
    var columns = [];
    // rankings
    json.rankings.forEach( function(item, index) {
      columns.push({data: 'rankings.'+item.rank_id.toString(), title: '#', name: item.rank_id.toString(), className: "text-right", defaultContent: '', visible: (index === 0) ? true : false});
    });
    columns.push({data: 'ID', title:'ID', className: "text-right", defaultContent: ''});
    columns.push({data: 'fai_id', title:'FAI', className: "text-right", defaultContent: '', visible: false});
    columns.push({data: 'civl_id', title:'CIVL', className: "text-right", defaultContent: '', visible: false});
    columns.push({data: 'name', title:'Name'});
    columns.push({data: 'nat', title:'NAT', name:'NAT', defaultContent: ''});
    columns.push({data: 'sex', title:'Sex', defaultContent: '', visible: false});
    columns.push({data: 'glider', title:'Equip', defaultContent: ''});
    columns.push({data: 'glider_cert', title:'Class', defaultContent: '', visible: false});
    columns.push({data: 'sponsor', title:'Sponsor', defaultContent: ''});
    columns.push({data: 'score', title:'Total', className: "text-right"});
    json.tasks.forEach( function(item, index) {
        var code = item.task_code
        columns.push({data: 'results.'+code+'.score', title: code, className: "text-right", defaultContent: ''});
    });
    $('#results_table').DataTable( {
        data: json.results,
        paging: false,
        searching: true,
        saveState: true,
        info: false,
        dom: 'lrtip',
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

            // comp info
            $('#comp_name').text(json.info.comp_name);
            $('#comp_date').text(json.info.date_from + ' - ' + json.info.date_to);
            if (json.info.comp_class != "PG") {
                update_classes(json.info.comp_class);
            }
            // tasks
            if (json.tasks.length > 0) {
                let tbl = document.createElement('table');
                tbl.className="tasks-list";
                let thead = tbl.createTHead();
                let row = thead.insertRow();
                console.log('validity='+json.formula.overall_validity);
                if (json.formula.overall_validity == 'FTV') {
                    header = [ 'Task', 'Date', 'Distance', 'FTV Validity' ];
                    keys = [ 'link', 'date', 'opt_dist', 'ftv_validity' ]
                }
                else {
                    header = [ 'Task', 'Date', 'Distance' ];
                    keys = [ 'link', 'date', 'opt_dist' ]
                }
                header.forEach(el => {
                    let th = document.createElement("th");
                    th.className="tasks-list";
                    th.innerHTML = '<b>'+el+'</b>';
                    row.appendChild(th);
                });
                json.tasks.forEach(task => {
                    if ( task.training == "1" ) return true;
                    let row = tbl.insertRow();
                    keys.forEach(el => {
                        let cell = row.insertCell();
                        cell.className="tasks-list";
                        cell.innerHTML = task[el];
                    });
                });
                $('#comp_header').append(tbl);
            }
            else {
                let text = document.createTextNode('No task have been scored yet.');
                $('#comp_header').append(text);
            }
            // some GAP parameters
            $('#formula tbody').append(
                        "<tr><td>Director</td><td>" + json.info.MD_name + '</td></tr>' +
                        "<tr><td>Location</td><td>" + json.info.comp_site + '</td></tr>' +
                        "<tr><td>Formula</td><td>" + json.formula.formula_name + '</td></tr>' +
                        "<tr><td>Overall Scoring</td><td>" + json.formula.overall_validity + ' (' + json.formula.validity_param + ')</td></tr>');
            if (json.formula.overall_validity == 'ftv') {
                $('#formula tbody').append(
                        "<tr><td>Total Validity</td><td>" + json.stats.total_validity + '</td></tr>');
            }
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