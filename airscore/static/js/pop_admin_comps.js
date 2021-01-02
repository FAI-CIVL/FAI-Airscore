var csrftoken = $('meta[name=csrf-token]').attr('content');

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken)
    }
  }
})

$('#new_comp_form').submit( function (e) {
  e.preventDefault(); // block the traditional submission of the form.
  $('#compmodal .modal-errors').empty();  // delete all previous errors
  let mydata = $('#new_comp_form').serialize();
  let url = "/users/_create_comp";
  $.ajax({
    type: "POST",
    url: url,
    data: mydata, // serializes the form's elements.
    success: function (response) {
      // console.log(response);  // display the returned data in the console.
      if (response.success) {
        get_comps();
        $('#compmodal').modal('toggle');
        create_flashed_message('Comp successfully created.', 'info');
      }
      else {
        if (response.errors) {
          let keys = Object.keys(response.errors);
          console.log('Error! ('+keys.length+')');
          keys.forEach( key => {
            let text = response.errors[key][0];
            $('#compmodal .modal-body div').find("[name='"+key+"']").css('background-color', 'orange');
            let message = document.createElement( "p" );
            message.classList.add('alert', 'alert-danger');
            message.innerText = key + ': ' + text;
            $('#compmodal .modal-errors').append(message);
          })
        }
      }
    }
  });
});

function get_comps(){
  $('#competitions').dataTable({
    destroy: true,
    ajax: '/users/_get_admin_comps',
    paging: true,
    bAutoWidth: false,
    order: [[ 4, 'desc' ]],
    lengthMenu: [ 15, 30, 60, 1000 ],
    searching: true,
    info: false,
    dom: '<"#search"f>rt<"bottom"lip><"clear">',
    createdRow: function( row, data, index, cells )
    {
      if (today() < data[4]) {
        $(row).addClass('text-warning');
      }
      else if (today() < data[5]) {
        $(row).addClass('text-info');
      }
    },
    columnDefs:[{
      targets: [-1],  render: function (a, b, data, d) {
        if(data[7]=='delete'){
        return ('<td  class ="value" ><button type="button" class="btn btn-danger" onclick="confirm_delete_comp('
           +  data[0] + ')" data-toggle="confirmation" data-popout="true">Delete</button></td>');
        }
        else{ return '';}
      }},
      {targets: [0], class: 'text-right mr-2'},
      {targets: [1], class: 'mr-2'},
      {targets: [2], class: 'mr-1'},
      {targets: [3], class: 'mr-1'},
      {targets: [4], class: 'mr-1'},
      {targets: [5], class: 'text-right mr-1'},
      {targets: [-2], class: 'text-danger bold mr-1'}
    ],
    initComplete: function(settings) {
      let table = $('#competitions').DataTable();
      let empty = true;
      table.column( 6 ).data().each( val => {
        if (val != "") {
          empty = false;
          return false;
        }
      });
      if (empty) {
        table.column( 6 ).visible( false );
      }
    }
  });
}

function filesize(elem){
  document.cookie = `filesize=${elem.files[0].size}; SameSite=Strict; path=/`
}

function confirm_delete_comp(compid) {
  compid_to_delete = compid;
  $('#confirmbox').val('');
  $('#deletemodal').modal('show');
}

function delete_comp() {
  if($('#confirmbox').val().toUpperCase() == 'DELETE'){
    $.ajax({
      type: "POST",
      url: '/users/_delete_comp/' + compid_to_delete,
      success: function(response) {
        if (response.redirect) {
          window.location.href = response.redirect;
        }
        else {
          $('#deletemodal').modal('hide');
          get_comps();
          create_flashed_message('Comp has been deleted.', 'warning');
        }
      }
    });
  }
  $('#deletemodal').modal('hide');
}

var compid_to_delete = null;

$(document).ready(function() {
  get_comps();

  $('#fsdb_fileupload').fileupload({
    dataType: 'json',
    submit: function (e, data){
      // Disabling buttons
      $("#fsdb_cancel").prop('disabled', true);
      $("#get_fsdb_file_button").prop('disabled', true);

      $('#fsdb_modal_message').hide();
      $('#fsdb_progress').show();
      $('#fsdb_progress_text').text('Processing: '+data.files[0].name);
      $('#fsdb_spinner').html('<div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div>');
    },
    // Response received
    success: function(response) {
      console.log(response);
      if (response.success) {
        get_comps();
        create_flashed_message('Event successfully imported from FSDB file.', 'info');
        if (response.autopublish) {
          create_flashed_message('Results have been automatically published.', 'info');
        }
      }
      else {
        create_flashed_message('There was an error trying to import event from FSDB file.', 'danger');
        if (response.error) create_flashed_message(response.error, 'warning');
      }
    },
    // Response missing
    fail: function (e) {
      console.log('fail...');
      console.log(e);
      create_flashed_message('There was an error trying to import event from FSDB file.', 'danger');
    },
    progress: function (e, data) {
      var progress = parseInt(data.loaded / data.total * 100, 10);
      $('#fsdb_progress .bar').css(
        'width',
        progress + '%'
      );
    },
    complete: function () {
      // Enabling buttons
      $("#fsdb_cancel").prop('disabled', false);
      $("#get_fsdb_file_button").prop('disabled', false);
      // Resetting form text
      $('#importmodal').modal('hide');
      $('#fsdb_progress_text').text('');
      $('#fsdb_spinner').html('');
      $('#autopublish').prop('checked', false);;
    }
  });

  // listeners
  $('#get_fsdb_file_button').click(function() {
    $('#fsdb_fileupload').click();
  });

  $('#fsdb_fileupload').bind('fileuploadsubmit', function (e, data) {
      data.formData = { autopublish: $('#autopublish').is(':checked') };
  });

});

