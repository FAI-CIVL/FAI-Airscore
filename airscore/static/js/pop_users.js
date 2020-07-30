function populate_users(){
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

            return ('<td  class ="value" ><button type="button" class="btn btn-primary" onclick="edit_user('
               +  data.id + ')" data-toggle="confirmation" data-popout="true">Edit</button></td>');
        }      }

       ]

})

       };


function modify_user(id){
$('#edit_user_modal').modal('show');
}

