function populate_waypoints(regid, airspace){
    console.log('regid='+regid+' airspace='+airspace);
    let openair = { airspace: airspace }
    $.ajax({
        url: '/users/_get_wpts/'+regid,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(openair),
        success: function(response){
            console.log('map='+(response.map != null)+' airspace:'+response.airspace);
            if(response.map != null) {
                $('#map_container').html(response.map);
            }
            update_waypoints(response.waypoints);
        }
    });
}

function update_waypoints(waypoints) {
    var wpts_num = waypoints.length;
    $('#waypoints').DataTable({
        data: waypoints,
        paging: false,
        saveState: true,
        searching: true,
        filter: true,
        info: false,
        "dom": '<"#search"f>rt<"bottom"lip><"clear">',
        destroy: true,
        columns: [
            {data: 'name', title:'Name', defaultContent: ''},
            {data: 'description', title:'Description', defaultContent: ''},
            {data: 'altitude', title:'Alt', defaultContent: ''},
            {data: 'lat', title:'Lat', defaultContent: ''},
            {data: 'lon', title:'Lon', defaultContent: ''},
        ],
        orderFixed: [[0, 'asc'],[1, 'asc']],
        rowGroup: {
            dataSrc: function(row) {
                        return row.name.substr(0, 1);
                     }
        },
        initComplete: function(settings, json) {
           $('#region_wpt_no').text('Waypoints: ' + wpts_num);
        }
   });
}