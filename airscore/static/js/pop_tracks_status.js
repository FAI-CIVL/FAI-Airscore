function populate_tracks(task_id){
    $.ajax({
        url: '/_get_tracks_status/'+task_id,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(offset),
        success: function(response){
            update_results(response.data);
            //update time updated
            let timestamp = response.timestamp;
            console.log('timestamp='+timestamp);
            $('#updated').html('<b>' + timestamp + '</b>');
        }
    });
}

function update_results(data){
    $('#results_table').DataTable({
        destroy: true,
        data: data,
        paging: false,
        order: [[ 0, 'asc' ]],
        searching: true,
        info: false,
        columns: [
            {data: 'ID', title: 'ID', name: 'ID', className: "text-right", defaultContent: ''},
            {data: 'sex', title: 'Sex', name: 'sex', defaultContent: '', visible: false},
            {data: 'name', title: 'Name', name: 'name', render: function ( data, type, row ) { let span = '<span>'; if (row.sex == 'F'){span='<span class="sex-F">'}; return span + data + '</span>'}},
            {data: 'Result', title: 'Result', name: 'result', defaultContent: ''},
            {data: 'comment', title: 'Notes', name: 'notes', defaultContent: ''}
        ],
        rowId: function(data) {
                return 'id_' + data.par_id;
        },
        columnDefs:[],
        initComplete: function() {
            let table = $('#results_table').DataTable();
            let empty = true;
            table.column( 'notes:name' ).data().each( val => {
                if (val != "") {
                    empty = false;
                    return false;
                }
            });
            if (empty) {
                table.column( 'notes:name' ).visible( false );
            }
        }
    });
}

function task_info(info, route) {
    // times
    var tbl = document.createElement('table');
    tbl.className="times-list";
    if (info.startgates.length > 1) {
        info.startgates.forEach((el, i) => {
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
        cell2.innerHTML = '<b>' + info.start_time + '</b>';
    }
    if (info.stopped_time) {
        let row = tbl.insertRow();
        let cell1 = row.insertCell();
        cell1.className="times-list red";
        cell1.innerHTML = '<b>Stopped:</b>';
        let cell2 = row.insertCell();
        cell2.className="times-list red";
        cell2.innerHTML = '<b>' + info.stopped_time + '</b>';
    }
    else {
        let row = tbl.insertRow();
        let cell1 = row.insertCell();
        cell1.className="times-list";
        cell1.innerHTML = '<b>Task Deadline: </b>';
        let cell2 = row.insertCell();
        cell2.className="times-list";
        cell2.innerHTML = '<b>' + info.task_deadline + '</b>'
    }
    let row = tbl.insertRow();
    let cell1 = row.insertCell();
    cell1.className="times-list";
    cell1.innerHTML = '<b>Updated: </b>';
    let cell2 = row.insertCell();
    cell2.className="times-list";
    cell2.id='updated';
//    cell2.innerHTML = '<b>' + json.file_stats.updated + '</b>'
    $('#comp_header').append(tbl);
    // waypoints
    var tbl = document.getElementById('waypoints');
    tbl.classList.add('wpt-list');
    var body = tbl.getElementsByTagName('tbody')[0];
    route.forEach(wpt => {
        let row = body.insertRow();
        let list = [ wpt.name, (wpt.type + ' ' + wpt.shape), wpt.radius, wpt.cumulative_dist, wpt.description];
        list.forEach(el => {
            let cell = row.insertCell();
            cell.classList.add('wpt-list');
            cell.innerHTML = el;
        });
    });
}

$(document).ready(function(){
    console.log('startgates: '+info.startgates)
    task_info(info, route);
    populate_tracks(taskid);
});
