function populate_users(editable){
    console.log('editable='+editable);
    $('#users').dataTable({
        ajax: '/users/_get_users',
        info: true,
        paging: false,
        saveState: true,
        searching: true,
        filter: true,
        info: false,
        "dom": '<"#search"f>rt<"bottom"lip><"clear">',
        destroy: true,
        columns: [

            { data: 'id', title: "id"},
            { data: 'first_name', title: "Name"},
            { data: 'last_name', title: "Surname"},
            { data: 'username', title: "Username"},
            { data: 'email', title: "Email"},
            { data: 'active', title: "Enabled"},
            { data: 'access', title: "Access level"},
            { data: null}
        ],

        rowId: function(data) {
            return 'id_' + data.id;
        },
        columnDefs:[{
            targets: [-1],  render: function (a, b, data, d) {
                if (editable) {
                    return ('<td  class ="value" ><button type="button" class="btn btn-primary" onclick="edit_user('
                    +  data.id + ')" data-toggle="confirmation" data-popout="true">Edit</button></td>');
                }
                else {
                    return ('<td  class ="value" ><span style="color: grey">External</span></td>');
                }
            }
        }]
    })
}

function modify_user(id){
    $('#edit_user_modal').modal('show');
}

function isNotEmpty( el ){
    return !!$.trim(el.html());
}

function isNotEmpty( el ){
    return !!$.trim(el.html());
}

function edit_user(id){
    $('#mod_email').val($('#id_'+id).children('td:eq(4)').text()).change();
    $('#mod_active').prop('checked', isNotEmpty($('#id_'+id).children('td:eq(5)')));
    $('#mod_access').val($('#id_'+id).children('td:eq(6)').text()).change();
    $('#modify_confirmed').attr("onclick","save_modified_user('"+ id +"')");
    $('#edit_user_modal').modal('show');
}

function save_modified_user(id){
    var mydata = new Object();
    mydata.email = $('#mod_email').val();
    mydata.active = $('#mod_active').is(':checked');
    mydata.access = $('#mod_access').val();

    $.ajax({
        type: "POST",
        url: "/users/_modify_user/"+id,
        contentType:"application/json",
        data : JSON.stringify(mydata),
        dataType: "json",
        success: function (data) {
           populate_users();
        }
    });
}

jQuery(document).ready(function($) {
    populate_users(editable);
});


function edit_user(id){
    $('#mod_email').val($('#id_'+id).children('td:eq(4)').text()).change();
    $('#mod_active').prop('checked', isNotEmpty($('#id_'+id).children('td:eq(5)')));
    $('#mod_access').val($('#id_'+id).children('td:eq(6)').text()).change();
    $('#modify_confirmed').attr("onclick","save_modified_user('"+ id +"')");
    $('#edit_user_modal').modal('show');
}

function save_modified_user(id){
    var mydata = new Object();
    mydata.email = $('#mod_email').val();
    mydata.active = $('#mod_active').is(':checked');
    mydata.access = $('#mod_access').val();

    $.ajax({
        type: "POST",
        url: "/users/_modify_user/"+id,
        contentType:"application/json",
        data : JSON.stringify(mydata),
        dataType: "json",
        success: function (data) {
           populate_users();
        }
    });
}

jQuery(document).ready(function($) {
    populate_users(editable);
});


