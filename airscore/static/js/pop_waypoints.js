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
    $('#waypoints').dataTable({
        data: waypoints,
        paging: false,
        saveState: true,
        searching: true,
        filter: true,
        info: false,
        "dom": '<"#search"f>rt<"bottom"lip><"clear">',
        destroy: true,
        columns: [
            {data: 'Class', title:'Class'},
            {data: 'name', title:'Name'},
            {data: 'description', title:'Description'},
            {data: 'altitude', title:'Alt'},
            {data: 'lat', title:'Lat'},
            {data: 'lon', title:'Lon'},
        ],
        orderFixed: [[0, 'asc'],[1, 'asc']],
        rowGroup: {
            dataSrc: ['Class']
        },
        columnDefs: [
            {
                "targets": [0],
                "visible": false
            },
        ],
        initComplete: function(settings, json) {
           $('#region_wpt_no').text('Waypoints : ' + wpts_num);
        }
   });
}