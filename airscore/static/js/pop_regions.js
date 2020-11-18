function populate_regions ( regions, args ){
    $('#regions').dataTable({
        data: regions,
        paging: false,
        searching: true,
        saveState: true,
        info: false,
        dom: '<"#search"f>rt<"bottom"lip><"clear">',
        columns: [
            {data: 'reg_id', title: 'ID', defaultContent: '', visible: false},
            {data: 'name', title: 'Name', width: 300, defaultContent: '', render: function ( data, type, row ) { return create_link(data, row.reg_id, args )}},
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

function create_link( data, regid, args ) {
    if ( args == null ) {return '<a href="/region_map/'+regid+'">'+data+'</a>'}
    else {return '<a href="/region_map/'+regid+'?'+args+'">'+data+'</a>'}
}

$(document).ready(function() {
    populate_regions(regions, link_args);
});
