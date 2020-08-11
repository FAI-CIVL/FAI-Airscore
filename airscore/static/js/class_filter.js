
$.fn.dataTable.ext.search.push(
    function( settings, data, dataIndex, row, counter ) {
        var idx = $('#dhv option:selected').index();

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
        for ( var i=0; i<=3; i++ ) {
            var v = false;
            if ( i == idx ) {
                v = true;
            }
            table.column(i).visible( v );
        }
        console.log('flyclass='+flyclass);
        table.search('').draw();
    } );
} );
