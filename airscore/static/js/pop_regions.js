function populate_regions ( regions ){
    $('#regions').dataTable({
        data: regions,
        paging: false,
        searching: true,
        saveState: true,
        info: false,
        dom: '<"#search"f>rt<"bottom"lip><"clear">',
        columns: [
            {data: 'reg_id', title: 'ID', defaultContent: '', visible: false},
            {data: 'name', title: 'Name', width: 300, defaultContent: '', render: function ( data, type, row ) { return '<a href="/region_map/'+row.reg_id+'?back_link=regions">'+data+'</a>'}},
            {data: 'filename', title: 'Waypoints', defaultContent: '', render: function ( data ) { return '<a class="btn btn-primary" href="/download/waypoints/'+data+'">Download</a>'}},
            {data: 'openair', title: 'Openair', defaultContent: '', render: function ( data ) { if ( data ) {return '<a class="btn btn-primary" href="/download/airspace/'+data+'">Download</a>'}}}
        ],
        rowId: function(data) {
            return 'id_' + data.reg_id;
        },
        orderFixed: [1, 'asc'],
        initComplete: function(settings, json) {
            var table = $('#regions');
            var rows = $("tr", table).length-1;
            // Get number of all columns
            var numCols = table.DataTable().columns().nodes().length;
            console.log('numCols='+numCols);
        }
    });
}

$(document).ready(function() {
    populate_regions(regions)
});
