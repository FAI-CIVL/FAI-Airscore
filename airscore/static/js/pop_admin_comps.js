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
            url: '/users/_create_comp',
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

function get_comps()
{

    $('#competitions').dataTable({
        destroy: true,
        ajax: '/users/get_admin_comps',
        paging: true,
        order: [[ 4, 'desc' ]],
        lengthMenu: [ 15, 30, 60, 1000 ],
        searching: true,
        info: false,
        "dom": '<"#search"f>rt<"bottom"lip><"clear">',
        "createdRow": function( row, data, index, cells )
        {

            if (today() < data[4])
            {       
                $(row).addClass('text-warning');
            }
            else if (today() < data[5])
            {
                $(row).addClass('text-info');
            }

            },
          columnDefs:[{
            targets: [-1],  render: function (a, b, data, d) {
            if(data[6]=='delete'){
            return ('<td  class ="value" ><button type="button" class="btn btn-danger" onclick="confirm_delete_comp('
               +  data[0] + ')" data-toggle="confirmation" data-popout="true">Delete</button></td>');
            }

           else{ return '';}

        }                 }]
        });

        }



