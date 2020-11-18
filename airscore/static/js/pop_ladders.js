function populate_ladders() {
    $('#competitions').dataTable({
        ajax: '/_get_ladders',
        paging: false,
        searching: true,
        saveState: true,
        info: false,
        dom: '<"#search"f>rt<"bottom"lip><"clear">',
        columns: [
            {data: 'ladder_name', title: 'Name'},
            {data: 'nat', title: 'Nat', defaultContent: ''},
            {data: 'ladder_class', title: 'Class', defaultContent: ''},
            {data: 'season', title: 'Season', defaultContent: ''},
            {data: 'status', title: 'Status'},
        ],
        rowId: function(data) {
            return 'id_' + data.ladder_id;
        },
        createdRow: function( row, data, dataIndex ) {
            if (today() < data.date_from) {
                $(row).addClass('text-warning');
            }
            else if (today() <= data.date_to) {
                $(row).addClass('text-info');
            }
        },
        "columnDefs": [
            {
                targets: [ ],
                visible: false
            },
            {
                targets: [ 2 ],
                width: 40
            }
        ],
        "initComplete": function(settings, json) {
            var table = $('#competitions');
            var rows = $("tr", table).length-1;
            // Get number of all columns
            var numCols = table.DataTable().columns().nodes().length;
            console.log('numCols='+numCols);

            // season picker
            populate_season_picker(json.seasons, selected);
        }
    });
}
$(document).ready(function() {
    populate_ladders();
});
