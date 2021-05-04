var form_elements = ['first_name', 'last_name', 'nat', 'access', 'email', 'username', 'active'];

function populate_users(editable){
//  console.log('editable='+editable);
  $.ajax({
    type: "GET",
    url: '/users/_get_users',
    contentType:"application/json",
    dataType: "json",
    success: function ( json ) {
      let columns = [
        {data: 'id', title: 'id', name: 'id', visible: false, searchable: false, defaultContent: ''},
        {data: 'first_name', title:'Name', name: 'first_name', defaultContent: ''},
        {data: 'last_name', title:'Surname', name: 'last_name', defaultContent: ''},
        {data: 'nat', title:'Nation', width: '1.2rem', name:'nat', defaultContent: ''},
        {data: 'username', title:'Username', name:'username', defaultContent: ''},
        {data: 'email', title:'Email', name:'email', defaultContent: ''},
        {data: 'access', title:'Access Level', name:'access', defaultContent: ''},
        {data: 'active', title:'Enabled', name:'active', defaultContent: ''},
        {data: 'id', title: '', render: function ( data, type, row ) {
                                          if ( !editable ) return '<p class="text-muted mt-2 mb-2">External</p>'
                                          else if ( !is_admin && ['admin', 'manager'].includes(row.access) ) return '<p class="text-muted mt-2 mb-2">&nbsp;</p>'
                                          else return '<button type="button" class="btn btn-primary" onclick="edit_user(' + data + ')">Edit</button>'
                                        }}
      ];

      $('#users').dataTable({
        data: json.data,
        destroy: true,
        paging: false,
        responsive: true,
        saveState: true,
        info: false,
        bAutoWidth: false,
        searching: true,
        filter: true,
        dom: '<"#search"f>rt<"bottom"lip><"clear">',
        columns: columns,
        rowId: function( data ) {
          return 'id_' + data.id;
        }
      })
    }
  });
}

function edit_user( user_id ) {
  cleanup_modal('user_modal');
  if ( user_id ) {
    let table = $('#users').DataTable();
    let row = '#id_'+user_id;
    let data = table.row( row ).data();

//    console.log('user_id='+data.id);
    $('#user_id').val(user_id);
    $.each(form_elements, (idx, el) => { $("#"+el).is(':checkbox') ? $("#"+el).prop("checked", data[el] == true) : $("#"+el).val(data[el]) } );
    $('#active').checked = (data.active == true);
    $('#username_dummy').text(data.username);
    $('#username_section').show();
    $('#active_section').show();
    $('#email_copy_section').hide();
  }
  else {
    $('#username_section').hide();
    $('#active_section').hide();
    $("#email_copy").prop("checked", true);
    $('#email_copy_section').show();
  }
  $('#user_modal').modal('show');
}

$('#user_form').submit( function (e) {
  e.preventDefault(); // block the traditional submission of the form.
  $('#user_modal .modal-errors').empty();  // delete all previous errors
  let userid = $('#user_id').val();
  let url = "/users/_add_user/";
  $('#username').val($('#email').val());  // use email as username
  console.log('user id= '+ userid + ' username='+$('#username').val());
  if ( userid ) url = "/users/_modify_user/"+userid;
  let mydata = $('#user_form').serialize();
//  console.log(mydata);

  $.ajax({
    type: "POST",
    url: url,
    data: mydata, // serializes the form's elements.
    success: function (response) {
      // console.log(response);  // display the returned data in the console.
      if (response.success) {
        populate_users(editable);
        $('#user_modal').modal('toggle');
        let message = 'User successfully saved. An email has been sent to new user address.';
        if ( userid ) message = 'User successfully updated.';
        create_flashed_message(message, 'info');
      }
      else {
        if (response.mail_error) {
          create_flashed_message('Failed to create a new user: Error trying to send registration email.', 'danger');
          $('#user_modal').modal('toggle');
        }
        else if (response.errors) {
          let keys = Object.keys(response.errors);
          console.log('Error! ('+keys.length+')');
          keys.forEach( key => {
            let text = response.errors[key][0];
            $('#user_modal-body div').find("[name='"+key+"']").css('background-color', 'orange');
            let message = document.createElement( "p" );
            message.classList.add('alert', 'alert-danger');
            message.innerText = key + ': ' + text;
            $('#user_modal .modal-errors').append(message);
          })
        }
      }
    }
  });
});

function cleanup_modal (modal) {
  let body = modal + '-body';
  $('#'+modal+' .modal-errors').empty();  // delete all previous errors
  $('#user_id').val('');
  $('#'+body+' [name]').each( function( i, el ) {
    if ( form_elements.includes($(el).attr('name')) ) {
      $(el).addClass('form-control form-control-sm');
      if ( $(el).is(':checkbox') ) $(el).prop("checked", false); else $(el).val('');
    }
    $(el).removeAttr('style');
  });
  $('#access').val('scorekeeper');
}

jQuery(document).ready(function($) {
    populate_users(editable);
});

