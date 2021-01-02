function populate_competitions() {
  $('#competitions').dataTable({
    ajax: '/_get_all_comps',
    order: [[ 4, 'desc' ]],
    paging: false,
    searching: true,
    saveState: true,
    info: false,
    dom: '<"#search"f>rt<"bottom"lip><"clear">',
    columns: [
      {data: 'comp_name', title:'Competition'},
      {data: 'comp_site', title:'Location', defaultContent: ''},
      {data: 'comp_class', title:'Class', defaultContent: ''},
      {data: 'comp_type', title:'Type', defaultContent: ''},
      {data: 'date_from', title:'From', defaultContent: ''},
      {data: 'date_to', title:'To', defaultContent: ''},
      {data: 'tasks', title:'Tasks'},
      {data: 'status', title:'Status'},
    ],
    rowId: function(data) {
      return 'id_' + data.comp_id;
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
  populate_competitions();
});
