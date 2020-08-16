
$.fn.dataTable.ext.search.push(
    function( settings, data, dataIndex, row, counter ) {
        var year = $('#season option:selected').val();

        if ( data[3].includes(year) || data[4].includes(year) ) return true;
        return false;
    }
);

$(document).ready(function() {
    // Event listener to the two range filtering inputs to redraw on input
    $('#season').change( function() {
        var table = $('#competitions').DataTable();
        var season = $('#season option:selected').val();
        var idx = $('#season option:selected').index();
        console.log('season='+season);
        table.search('').draw();
    } );
} );
