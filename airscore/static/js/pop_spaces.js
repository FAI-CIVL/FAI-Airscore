function populate_spaces(regid, airspace){
    console.log('regid='+regid+' airspace='+airspace);
    update_spaces(airspace);
}

function update_spaces(airspace) {
    var spaces_num = airspace.length;
    $('#airspace').DataTable({
        data: airspace,
        paging: false,
        saveState: true,
        searching: true,
        filter: true,
        info: false,
        "dom": '<"#search"f>rt<"bottom"lip><"clear">',
        destroy: true,
        columns: [
            {data: 'id', title: 'ID', defaultContent: '', visible: false},
            {data: 'name', title: 'Name', defaultContent: ''},
            {data: 'class', title: 'Class', defaultContent: ''},
            {data: null, title: 'Floor', defaultContent: '', render: function ( row ) { return row.floor_description+' ('+row.floor+' '+row.floor_unit+'.)'}},
            {data: null, title: 'Ceiling', defaultContent: '', render: function ( row ) { return row.ceiling_description+' ('+row.ceiling+' '+row.ceiling_unit+'.)'}}
        ],
        orderFixed: [[2, 'asc'], [1, 'asc']],
        rowGroup: {
            startRender: function ( rows, group ) { return 'Class '+group },
            dataSrc: 'class'
        },
        initComplete: function(settings, json) {
            $('#spaces_no').text('Restricted Zones: ' + spaces_num);
        }
   });
}