
$(document).ready(function() {

    $('#competitions').dataTable({
        ajax: '/get_all_comps',
        paging: true,
        order: [[ 5, 'desc' ]],
        lengthMenu: [ 15, 30, 60, 1000 ],
        searching: true,
        info: false,
        //"dom": '<"search"f><"top"l>rt<"bottom"ip><"clear">',
        "dom": '<"#search"f>rt<"bottom"lip><"clear">',
        "createdRow": function( row, data, index )
        {
            if (today() < data[4])
            {
                $(row).addClass('text-warning');
            }
            else if (today() < data[5])
            {
                $(row).addClass('text-info');
            }
        }
    });
});
