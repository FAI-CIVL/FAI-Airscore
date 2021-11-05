function populate_live(taskid){
    $(document).ready(function() {
        $('#comp_name').text('Loading Results ...');
        $.ajax({
            type: "POST",
            url: '/_get_livetracking/'+taskid,
            contentType:"application/json",
            dataType: "json",
            success: function (json) {
                let columns = [];
                let compid = json.info.comp_id;
                $('#comp_link').attr("href", "/competition/"+compid);
                columns.push({data: 'rank', title:'#'});
                columns.push({data: 'id', title:'ID', defaultContent: ''});
                columns.push({data: 'name', title:'Name'});
                columns.push({data: 'sex', title:'Sex', defaultContent: '', visible: false});
                columns.push({data: 'result', title:'Result', defaultContent: ''});
                columns.push({data: 'status', title:'Status', defaultContent: ''});
                columns.push({data: 'comment', title:'Comment', defaultContent: ''});
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
                            });
                            if (empty) {
                                table.DataTable().column( i ).visible( false );
                            }
                            const titles = ['#', 'ID']
                            if (titles.includes((table.DataTable().column( i ).title))) {

                            }
                        }
                        // comp info
                        text = json.info.comp_name + " " + json.info.task_name;
                        $('#comp_name').text(text);
                        $('#task_date').text(json.headers.main);
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
                        let row = tbl.insertRow();
                        let cell1 = row.insertCell();
                        cell1.className="times-list";
                        cell1.innerHTML = '<b>Updated: </b>';
                        let cell2 = row.insertCell();
                        cell2.className="times-list";
                        cell2.innerHTML = '<b>' + json.file_stats.updated + '</b>'
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
                    }
                });
            }
        });
        setTimeout(function(){
           window.location.reload(1);
        }, 120000);
    });
}
