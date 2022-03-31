// jQuery selection for the 2 select boxes
var dropdown = {
  category: $('#select_category'),
  formula: $('#select_formula'),
  scoring: $('#overall_validity'),
  igc_config: $('#igc_parsing_file'),
  classification: $('#select_classification'),
  ranking_type: $('#rank_type')
};

var comp_class = dropdown.category.val();
var isSubmitting = false;

$(document).ready(function() {
  $('#main_comp_settings_form').data('initial-state', $('#main_comp_settings_form').serialize());
  populate_tasks( tasks_info );
  get_scorekeepers( compid );

  // hide form rows if all elements are hidden
  hide_unused_rows();

  // populate_rankings( dropdown.category.val() );
  document.getElementById("link_igc_config").setAttribute("href", "/users/igc_parsing_config/" + dropdown.igc_config.val());
  update_rankings();

  // function to call XHR and update formula dropdown
  function updateFormulas() {
    var cat = {
      category: dropdown.category.val()
    };
    dropdown.formula.attr('disabled', 'disabled');
    dropdown.formula.empty();
    $.getJSON("/users/_get_formulas", cat, function(data) {
      data.forEach(function(item) {
        dropdown.formula.append(
          $('<option>', {
            value: item[0],
            text: item[1]
          })
        );
      });
      dropdown.formula.removeAttr('disabled');
    });
  }

  // event listener to category dropdown change
  dropdown.category.on('change', function() {
    $('#confirm_modal .modal-title').html('Change category to '+dropdown.category.val());
    $('#confirm_modal-body p').html('This will reset formula settings and delete all category related sub rankings.<br />'+
                                    '<span class="text-danger"> Any other unsaved setting will be lost.</span>');
    $('#confirm_cancel').attr("onclick","reset_category();");
    $('#confirm_success').attr("onclick","change_category();");
    $('#confirm_modal').modal('show');
  });

  // event listener to formula dropdown change
  dropdown.formula.on('change', function() {
     ask_update('formula');
  });

  // event listener to scoring dropdown change
  dropdown.scoring.on('change', function() {
    if (dropdown.scoring.val() == 'all') {
      $('#validity_param').val(0);
      $('#validity_param_div').hide();
    }
    else {
      if (dropdown.scoring.val() == 'ftv') {
        $('#validity_param_div label').html('FTV percentage')
        $('#validity_param').val(25)
      }
      else {
        $('#validity_param_div label').html('Discard every')
        $('#validity_param').val(4)
      }
      $('#validity_param_div').show();
    }
  });

  // event listener to igc config dropdown change
  dropdown.igc_config.on('change', function() {
     $('#link_igc_config').attr("href", "/users/igc_parsing_config/" + dropdown.igc_config.val());
  });

  // event listener to ranking type dropdown change
  dropdown.ranking_type.on('change', function() {
     let rank_type = dropdown.ranking_type.val()
     update_ranking_modal(rank_type);
  });

  $('#main_comp_settings_form :input').change(function(){
    if (!isSubmitting && $('#main_comp_settings_form').serialize() != $('#main_comp_settings_form').data('initial-state')) {
      $('#main_comp_save_button').removeClass( "btn-outline-secondary" ).addClass( "btn-warning" );
      $('#save_button_warning_text').addClass('bg-warning').html('Competition needs to be saved');
    }
    else {
      $('#main_comp_save_button').removeClass( "btn-warning" ).addClass( "btn-outline-secondary" );
      $('#save_button_warning_text').removeClass('bg-warning').html('');
    }
  });

  $('#main_comp_settings_form').submit( function() {
    isSubmitting = true
  })

  $(window).on('beforeunload', function() {
    if (!isSubmitting && $('#main_comp_settings_form').serialize() != $('#main_comp_settings_form').data('initial-state')) {
      return 'You have unsaved changes which will not be saved.'
    }
  });

  // external event conversion
  $('#confirm_convert').click( function(){ $('#confirm_convert_modal').modal('show'); });
  $('#convert_confirmed').click( function(){
    window.location.href = "/users/_convert_external_comp/"+compid;
  });

});

function reset_category() {
  dropdown.category.val(comp_class);
}

function change_category() {
  let mydata = {
    old_category: comp_class,
    new_category: dropdown.category.val(),
    formula: dropdown.formula.val(),
    compid: compid
  };
  $.ajax({
    type: "POST",
    url: '/users/_change_comp_category',
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function (data) {
      if ( data.success ) window.location.reload(true);
      else create_flashed_message('Error trying to change category.', 'danger');
    }
  });
}

function hide_unused_rows() {
  $.each($('#adv_params section'), (idx, el) => {
    if ( $(el).children('input[type=hidden]').length > 0 && $(el).children('div').length === 0 ) $(el).hide();
  });
}

function ask_update(change) {
  var formula = $('#select_formula').val();
  var field = formula;

  if(change=='category') {
    field=$('#select_category').val();
    formula = field;
  }

  var heading1 = "<p>Changing to ";
  var heading2 = ". Do you also want to update the advanced parameters to the standard for ";
  $("#formula_modal-body").html(heading1 + field + heading2 + formula +'?</p>');
  $('#formula_confirmed').attr("onclick","update_formula_adv_settings()");
  $('#formula_modal').modal('show');
}

function add_task() {
  cleanup_modal('#new_task_form');
  $('#add_task_modal').modal('show');
}

function confirm_delete(task_num, taskid) {
  var x = task_num;
  var myHeading = "<p>Are you sure you want to delete Task ";
  $("#modal-body").html(myHeading + x + '?</p>');
  $('#delete_confirmed').attr("onclick","delete_task('"+taskid+"')");
  $('#delete_task_modal').modal('show');
}

function delete_task(taskid){
  $.ajax({
    type: "POST",
    url: '/users/_del_task/'+taskid,
    success: function () {
      get_tasks()
    }
  });
}

function get_tasks() {
  $.ajax({
    type: "GET",
    url: link_get_tasks,
    contentType:"application/json",
    dataType: "json",
    success: function (json) {
      populate_tasks(json);
    }
  });
}

function populate_tasks(json) {
  let columns = [
    {data: 'task_num', title:'#', className: "text-right", defaultContent: ''},
    {data: 'task_id', title:'ID', className: "text-right", defaultContent: '', visible: false},
    {data: 'date', title:'Date', defaultContent: ''},
    {data: 'region_name', title:'Region'},
    {data: 'opt_dist', title:'Dist.', name:'dist', className: "text-right", defaultContent: ''},
    {data: 'comment', title:'Comment', name:'comment', defaultContent: ''},
    {data: 'task_id', title:'Notes', name:'notes', defaultContent: '', render: function ( data, type, row ) {
                                                                                  if ( row.cancelled ) return '<span class="text-danger font-weight-bold">Cancelled</span>'
                                                                                  else if ( row.locked ) return '<span class="text-info font-weight-bold">Official Results</span>'
                                                                                  else if ( row.needs_full_rescore || row.needs_new_scoring || row.needs_recheck ) return '<span class="text-warning font-weight-bold">Check</span>'
                                                                                  else return ''}},
    {data: 'task_id', render: function ( data ) { return '<button class="btn btn-info ml-3" type="button" onclick="window.location.href = \'/users/task_admin/' + data + '\'">Settings</button>'}}
  ];
  if (!external && is_editor){
    columns.push({data: 'task_id', render: function ( data ) { return '<button class="btn btn-info ml-3" type="button" onclick="window.location.href = \'/users/track_admin/' + data + '\'">Tracks</button>'}});
  }
  if (is_editor){
    columns.push({data: 'task_id', render: function ( data ) { return '<button class="btn btn-info ml-3" type="button" onclick="window.location.href = \'/users/task_score_admin/' + data + '\'">Scores</button>'}});
  }
  if (!external && is_editor){
    columns.push({data: 'task_id', render: function ( data, type, row ) { return '<button type="button" class="btn btn-danger" onclick="confirm_delete( ' + row.task_num + ', ' + data + ' )" data-toggle="confirmation" data-popout="true">Delete</button>'}});
  }

  $('#tasks').DataTable( {
    data: json.tasks,
    destroy: true,
    paging: false,
    responsive: true,
    saveState: true,
    info: false,
    dom: 'lrtip',
    columns: columns,
    rowId: function(data) {
      return 'id_' + data.task_id;
    },
    initComplete: function(settings) {
      var table = $('#tasks');
      var rows = $("tr", table).length-1;
      // Get number of all columns
      var numCols = $('#tasks').DataTable().columns().nodes().length;
      for ( var col=1; col<numCols; col++ ) {
        var empty = true;
        table.DataTable().column(col).data().each( val => {
          if (val != "") {
            empty = false;
            return false;
          }
        });
        if (empty) {
          table.DataTable().column( col ).visible( false );
        }
      }
    }
  });
  $('#task_number').val(json['next_task']);
  $('#task_region').val(json['last_region']);
}


function save_ladders(){
  document.getElementById("save_ladders_button").innerHTML = "Saving...";
  document.getElementById("save_ladders_button").className = "btn btn-warning";
  var mydata = {};
  mydata.checked = [];
  $('#ladder_list').find('input').each( (i, el) =>  {
    if (el.checked){
      mydata.checked.push(el.value)
    }
  });
  $.ajax({
    type: "POST",
    url: link_save_comp_ladders,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function ( response ) {
      if (response.success){
        document.getElementById("save_ladders_button").innerHTML = "Saved";
        document.getElementById("save_ladders_button").className = "btn btn-success";
      }
      else {
        document.getElementById("save_ladders_button").innerHTML = "Error";
        document.getElementById("save_ladders_button").className = "btn btn-danger";
      }
      setTimeout(function(){
        document.getElementById("save_ladders_button").innerHTML="Save";
        document.getElementById("save_ladders_button").className = "btn btn-success";
      }, 3000);
   }
  });
}

$('#new_task_form').submit( function(e) {
  e.preventDefault(); // block the traditional submission of the form.
  cleanup_modal('#new_task_form');
  $('#add_task_button').hide();
  $('#add_task_spinner').html('<div class="spinner-border" role="status"><span class="sr-only"></span></div>');
  $('#new_task_form .modal-errors').empty();  // delete all previous errors
  let mydata = $('#new_task_form').serialize();
  $.ajax({
    type: "POST",
    url: link_add_task,
    data : mydata,
    dataType: "json",
    success: function (response) {
      if ( response.errors ) {
        let keys = Object.keys(response.errors);
        console.log('Error! ('+keys.length+')');
        keys.forEach( key => {
          let text = response.errors[key][0];
          $('#new_task_form .modal-body div').find("[name='"+key+"']").css('background-color', 'orange');
          let message = document.createElement( "p" );
          message.classList.add('alert', 'alert-danger');
          message.innerText = key + ': ' + text;
          $('#new_task_form .modal-errors').append(message);
        })
      }
      else {
        $('#add_task_modal').modal('hide');
        toastr.success('Task added', {timeOut: 3000});
        get_tasks();
      }
    },
    error: function(result, status, error) {
      create_flashed_message('System Error trying to create a new task', 'danger');
      get_tasks();
    },
    complete: function (result, status) {
      $('#add_task_button').show();
      $('#add_task_spinner').html('');
    }
  });
});

function get_scorekeepers(){
  $.ajax({
    type: "GET",
    url: link_get_scorekeepers,
    contentType:"application/json",
    dataType: "json",
    success: function (response) {
      // update scorekeepers list
      $('#scorekeeper_table tbody').empty();
      response['scorekeepers'].forEach( key => {
        let row = '<tr>' +
                        '<td class="">'+ key['first_name'] + ' ' + key['last_name'] +'</td>' +
                        '<td><a class="btn btn-sm btn-danger ml-3" onclick="delete_scorekeeper('+key['id']+')">Remove</a></td>' +
                      '</tr>';
        $('#scorekeeper_table tbody').append(row);
      });
      $('#owner').html(response['owner']['first_name'] + ' ' + response['owner']['last_name'] );

      // update select dropdown
      $("#scorekeeper").empty();
      if( response['dropdown'].length ) {
        response['dropdown'].forEach( key => {
          $("#scorekeeper").append($('<option>', {
              value: key['id'],
              text: key['first_name'] + ' ' + key['last_name'] + ' (' + key['username'] +')'
            }
          ))
        });
        $('#add_scorekeeper_switch').prop('disabled', false);
      }
      else {
        // hide dropdown section
        $('#add_sk').collapse('hide');
        $('#add_scorekeeper_switch').prop('disabled', true);
      }
    },
    error: function(result, status, error) {
      create_flashed_message('System Error trying to get scorekeepers list', 'danger');
    },
    complete: function (result, status) {
    }
  });
}

function add_scorekeeper(){
  $('#save_scorekeeper_button').removeClass('btn-success').addClass('btn-warning').text('Adding...');
  let mydata = {
    compid: compid,
    id: $('#scorekeeper').val()
  };
  $.ajax({
    type: "POST",
    url: link_add_scorekeeper,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function () {
      toastr.success('Scorekeeper added', {timeOut: 3000});
    },
    error: function(result, status, error) {
      clear_flashed_messages();
      create_flashed_message('System Error trying to add scorekeeper', 'danger');
      console.log( 'something went wrong: add_scorekeepers()', status, error);
    },
    complete: function (result, status) {
      $('#save_scorekeeper_button').removeClass('btn-warning').addClass('btn-success').text('Save');
      get_scorekeepers();
    }
  });
}

function delete_scorekeeper( id ) {
  let mydata = {
    compid: compid,
    id: id
  };
  $.ajax({
    type: "POST",
    url: '/users/_delete_scorekeeper',
    contentType:"application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function (response) {
      if ( response.success ) {
        //create_flashed_message('Scorekeeper removed', 'success');
        toastr.warning('Scorekeeper removed', {timeOut: 3000});
      }
      else create_flashed_message('Error trying to remove scorekeeper', 'danger');
    },
    error: function(result, status, error) {
      clear_flashed_messages();
      create_flashed_message('System Error trying to remove scorekeeper', 'danger');
      console.log( 'something went wrong: delete_scorekeepers()', status, error);
    },
    complete: function (result, status) {
      get_scorekeepers();
    }
  });
}

function update_formula_adv_settings(){
  let formula = new Object();
  formula.formula = $('#select_formula').val();
  formula.category = $('#select_category').val();
  formula.compid = compid;
  $.ajax({
    type: "POST",
    url: '/users/_update_formula_adv_settings',
    contentType:"application/json",
    data: JSON.stringify(formula),
    dataType: "json",
    success: function (data) {
      if ( data.success ) {
        console.log(data.render);
        $('#adv_params').empty().html(data.render);
        formula_preset = data.formula_preset;
        hide_unused_rows();
      }
      else create_flashed_message('Error trying to reset advanced formula parameters', 'danger');
    }
  });
}

function update_rankings() {
  $('#rankings_table').DataTable({
    ajax: '/users/_get_comp_rankings/'+compid,
    destroy: true,
    paging: false,
    responsive: true,
    saveState: true,
    info: false,
    bAutoWidth: false,
    searching: false,
    ordering: false,
    filter: false,
    columns: [
        {data: 'rank_id', title: 'ID', name: 'ID', visible: false},
        {data: 'rank_name', name: 'Name'},
        {data: 'rank_type', name: 'Type', visible: false, defaultContent: ''},
        {data: 'cert_id', name: 'Cert', visible: false, defaultContent: ''},
        {data: 'min_date', name: 'Date From', visible: false, defaultContent: ''},
        {data: 'max_date', name: 'Date To', visible: false, defaultContent: ''},
        {data: 'attr_id', name: 'Attr ID', visible: false, defaultContent: ''},
        {data: 'attr_value', name: 'Attr Value', visible: false, defaultContent: ''},
        {data: 'description', name: 'Description'},
        {data: 'rank_id', orderable: false, searchable: false, render: function ( data ) {
                                                                        let appearence = 'class="btn btn-primary" ';
                                                                        if (!is_editor) appearence = 'class="btn btn-secondary" disabled ';
                                                                        return '<td  class ="value" ><button type="button" ' + appearence + ' onclick="edit_ranking(' +  data + ')" data-toggle="confirmation" data-popout="true">Edit</button></td>'}},
        {data: 'rank_id', orderable: false, searchable: false, render: function ( data ) {
                                                                        let appearence = 'class="btn btn-danger" ';
                                                                        if (!is_editor) appearence = 'class="btn btn-secondary" disabled ';
                                                                        return '<td  class ="value" ><button type="button" ' + appearence + ' onclick="delete_ranking(' +  data + ')" data-toggle="confirmation" data-popout="true">Delete</button></td>'}}
    ],
    rowId: function(data) {
          return 'id_' + data.rank_id;
        },
    initComplete: function(settings, json) {
    }
  });
}

function add_ranking() {
  cleanup_modal('#rank_modal');
  $('#rank_type').val($('#rank_type option:first').val());
  update_ranking_modal($('#rank_type').val());
  $('#rank_modal').modal('show');
}

function edit_ranking(cranid) {
  cleanup_modal('#rank_modal')
  let table = $('#rankings_table').DataTable();
  let row = '#id_'+cranid;
  let data = table.row( row ).data();
  console.log('rank_id='+data['rank_id']+' rank_type='+data['rank_type']);
  console.log('min date='+moment(data['min_date']).format('YYYY-MM-DD'));
  [data['min_date'], data['max_date']].forEach( el => el = moment(el).format('YYYY-MM-DD'));
  if ( data['min_date'] ) data['min_date'] = moment(data['min_date']).format('YYYY-MM-DD');
  if ( data['max_date'] ) data['max_date'] = moment(data['max_date']).format('YYYY-MM-DD');
  update_ranking_modal(data['rank_type']);
  $('#rank_modal [name]').each( function( i, el ) {
    if (data[$(el).attr('name')]) $(el).val(data[$(el).attr('name')]);
  });

  $('#rank_modal').modal('show');
}

function delete_ranking( cranid ) {
  $.ajax({
    type: "POST",
    url: "/users/_delete_ranking/"+ cranid,
    contentType:"application/json",
    dataType: "json",
    success: function (response) {
      let message = 'Ranking successfully removed.';
      if (response.success) {
        create_flashed_message(message, 'warning');
        update_rankings();
      }
      else {
        message = 'Error: unable to delete ranking.';
        create_flashed_message(message, 'danger');
      }
    }
  });
}

function cleanup_modal (modal) {
  let body = modal + ' *';
  let errors = modal + ' .modal-errors';
  $(body).removeAttr('style');  // delete style added by error in form
  $(errors).empty();  // remove errors text in modal
}

function update_ranking_modal(rank_type) {
  console.log('rank_type: '+rank_type);
  let names = ['#cert_id', '#min_date', '#max_date', '#attr_id', '#rank_value'];
  $.each( names,  (i, el) => $(el).val(''));
  $.each([$('#rank_cert'), $('#rank_date'), $('#rank_attr'), $('#rank_key_value'), $('#custom_link')],  (i, el) => el.hide());
  if (rank_type == 'cert') {
    $('#cert_id').val($('#cert_id option:first').val());
    $('#rank_cert').show();
  }
  else if (rank_type == 'birthdate') $('#rank_date').show();
  else if (rank_type == 'nat') {
    $('#rank_key_value').show();
    $('label[for=rank_value]').html('FAI 3 Letters Nation Code');
  }
  else if (rank_type == 'female') {
    $('#rank_key_value').show();
    $('label[for=rank_value]').html('Minimum number of female participants');
  }
  else if (rank_type == 'custom') {
    $('#attr_id').val($('#attr_id option:first').val());
    $('label[for=rank_value]').html('Attribute Value');
    $.each([$('#rank_attr'), $('#rank_key_value'), $('#custom_link')], ( (i, el) => el.show()));
  };
}

$('#ranking_form').submit( function (e) {
  e.preventDefault(); // block the traditional submission of the form.
  $('#rank_modal .modal-errors').empty();  // delete all previous errors
  if ( check_ranking_modal() ) {
    let mydata = $('#ranking_form').serialize();
    let rankid = $('#rank_id').val()
    let url = "/users/_add_comp_ranking/"+ compid;
    if ( rankid ) url = "/users/_modify_comp_ranking/"+rankid;
    $.ajax({
      type: "POST",
      url: url,
      data: mydata, // serializes the form's elements.
      success: function (response) {
        // console.log(response);  // display the returned data in the console.
        if (response.success) {
          update_rankings();
          $('#rank_modal').modal('toggle');
          let message = 'Ranking successfully added.';
          if ( rankid ) message = 'Ranking successfully updated.';
          create_flashed_message(message, 'info');
        }
        else {
          if (response.errors) write_modal_messages(response.errors)
        }
      }
    });
  }
})

function write_modal_messages( errors ) {
  let keys = Object.keys( errors );
  console.log('Error! ('+keys.length+')');
  keys.forEach( key => {
    let text = errors[key][0];
    $('#rank_modal-body div').find("[name='"+key+"']").css('background-color', 'orange');
    let message = document.createElement( "p" );
    message.classList.add('alert', 'alert-danger');
    message.innerText = key + ': ' + text;
    $('#rank_modal .modal-errors').append(message);
  })
}

function check_ranking_modal() {
  let type = $('#rank_type').val();
  let rank_value = $('#rank_value').val();
  let min_date = $('#min_date').val();
  let max_date = $('#max_date').val();
  let errors = {};
  if ( type == 'custom' && !rank_value ) {
    message = 'Fill Attribute Value Field';
    errors['rank_value'] = [message];
  }
  else if ( type == 'nat' && !rank_value ) {
    message = 'Fill Nat Code Field';
    errors['rank_value'] = [message];
  }
  else if ( type == 'birthdate' && !min_date && !max_date ) {
    message = 'At least one date must be filled';
    errors['min_date'] = [message];
  };
  if ( Object.keys(errors).length ) {
    write_modal_messages( errors );
    return false;
  }
  else return true;
}

function export_to_fsdb(){
  $('#export_fsdb').hide();
  $('#fsdb_spinner').html('<div class="spinner-border" role="status"><span class="sr-only">Preparing FSDB...</span></div>');
  startDownloadChecker("loadingProgressOverlay", 120);
}

function startDownloadChecker(imageId, timeout) {

  var cookieName = "ServerProcessCompleteChecker";  // Name of the cookie which is set and later overridden on the server
  var downloadTimer = 0;  // reference to timer object

  // The cookie is initially set on the client-side with a specified default timeout age (2 min. in our application)
  // It will be overridden on the server side with a new (earlier) expiration age (the completion of the server operation),
  // or auto-expire after 2 min.
  setCookie(cookieName, 0, timeout);

  // set timer to check for cookie every second
  downloadTimer = window.setInterval(function () {
    var cookie = getCookie(cookieName);

    // If cookie expired (NOTE: this is equivalent to cookie "doesn't exist"), then clear "Loading..." and stop polling
    if ((typeof cookie === 'undefined')) {
      $('#export_fsdb').show();
      $('#fsdb_spinner').html('');
      window.clearInterval(downloadTimer);
    }
  }, 1000); // Every second
}

// These are helper JS functions for setting and retrieving a Cookie
function setCookie(name, value, expiresInSeconds) {
  var exdate = new Date();
  exdate.setTime(exdate.getTime() + expiresInSeconds * 1000);
  var c_value = escape(value) + ((expiresInSeconds == null) ? "" : "; expires=" + exdate.toUTCString());
  document.cookie = name + "=" + c_value + '; path=/';
}

function getCookie(name) {
  var parts = document.cookie.split(name + "=");
  if (parts.length == 2 ) {
    return parts.pop().split(";").shift();
  }
}
