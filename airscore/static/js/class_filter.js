
$.fn.dataTable.ext.search.push(
    function( settings, data, dataIndex, row, counter ) {
        var flyclass = $('#dhv option:selected').val();

        if (flyclass == '' || flyclass == 'CCC' || flyclass == 'Open') return true;
        if (flyclass == 'D')
        {
            if (data[4] == 'CCC') return false;
            return true;
        }

        if (data[4] <= flyclass)
        {
            return true;
        }
        return false;
    }
);

$(document).ready(function() {
    // Event listener to the two range filtering inputs to redraw on input
    $('#dhv').change( function() {
        var table = $('#task_result').DataTable();
        var flyclass = $('#dhv option:selected').val();
        console.log('flyclass='+flyclass);
        table.search('').draw();
    } );
} );
