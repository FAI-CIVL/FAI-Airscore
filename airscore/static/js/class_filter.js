
$.fn.dataTable.ext.search.push(
  function( settings, data, dataIndex, row, counter ) {
    let idx = $('#dhv option:selected').index();
    let rank_id = $('#dhv option:selected').val();
    let name = $('#dhv option:selected').text();
    console.log(idx+', '+name+', '+rank_id);

    if ( data[idx] ) return true;
    return false;
  }
);

$(document).ready(function() {
    // Event listener to the two range filtering inputs to redraw on input
    $('#dhv').change( function() {
        var table = $('#results_table').DataTable();
        var flyclass = $('#dhv option:selected').val();
        var idx = $('#dhv option:selected').index();
        var classes = $('#dhv option').length - 1
        for ( var i=0; i<=classes; i++ ) {
            var v = false;
            if ( i == idx ) {
                v = true;
            }
            table.column(i).visible( v );
        }
//        console.log('flyclass='+flyclass);
        table.search('').draw();
    } );
} );
