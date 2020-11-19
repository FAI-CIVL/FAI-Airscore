
$.fn.dataTable.ext.search.push(
    function( settings, data, dataIndex, row, counter ) {
        var year = $('#season').val();

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

function populate_season_picker( seasons, selected ) {
    // Remove all <option> child tags.
    $("#season option").remove();
    // Add today's year is seasons is empty
    if ( jQuery.isEmptyObject(seasons) ) { seasons.push(selected) };

    $.each(seasons, function(index, item) {
        $("#season").append($('<option>', {
                                value: item,
                                text: item
                            }));
        if ( item == selected ) { $('#season').val(item); };
    });
    // check season is selected
    if ( !$('#season').val() ) {
        $('#season').val($("#season option:first").val());
    }
    $('#season').trigger('change');
}