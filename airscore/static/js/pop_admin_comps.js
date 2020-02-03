var csrftoken = $('meta[name=csrf-token]').attr('content');

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        }
    }
})

function create_comp()
{
    var options = { };
    options.name = $('#compname').val();
    options.code = $('#compcode').val();
    options.location = $('#compsite').val();
    options.class =$('#compclass').val();
    options.dateto = $('#dateto').val();
    options.datefrom = $('#datefrom').val();
    $.ajax({
            url: '/create_comp',
            contentType:"application/json",
            dataType:"json",
            data: JSON.stringify(options),
            type: 'PUT',
            success:  function(response) {
            if (response.redirect){
                window.location.href = response.redirect;
                }
            },

            error: function(error) {
                console.log(error);
            }
        });
    console.log(options);
}
$(document).ready(function() {
//    var url = new URL('http://highcloud.net/xc/get_admin_comps.php');
    $('#competitions').dataTable({
        ajax: '/users/get_admin_comps',
        paging: true,
        order: [[ 4, 'desc' ]],
        lengthMenu: [ 15, 30, 60, 1000 ],
        searching: true,
        info: false,
        //"dom": '<"search"f><"top"l>rt<"bottom"ip><"clear">',
        "dom": '<"#search"f>rt<"bottom"lip><"clear">',
        "createdRow": function( row, data, index, cells )
        {
//            cells[1].innerHTML = '<a href=\"users/comp_settings.html?comPk=' + data[0] + '\">' + data[1] + '</a>';
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

