function populate_waypoints(regid){
    $('#waypoints').dataTable({
        ajax: '/users/_get_wpts/'+regid,
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
                   "columnDefs": [
            {
                "targets": [0],
                "visible": false
            },
                    ],
  "initComplete": function(settings, json) {
           $('#region_wpt_no').text('Waypoints : ' + json.data.length);
  }

   });

}