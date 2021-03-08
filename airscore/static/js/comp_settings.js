// jQuery selection for the 2 select boxes
var dropdown = {
    category: $('#select_category'),
    formula: $('#select_formula'),
    scoring: $('#overall_validity'),
    igc_config: $('#igc_parsing_file'),
    classification: $('#select_classification'),
    ranking_type: $('#rank_type')
};

$(document).ready(function() {
  populate_tasks( tasks_info );
  get_scorekeepers( compid );

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
    populate_rankings(dropdown.category.val())
    updateFormulas();
    ask_update('category');
  });

  // event listener to formula dropdown change
  dropdown.formula.on('change', function() {
     ask_update('formula');
  });

  // event listener to scoring dropdown change
  dropdown.scoring.on('change', function() {
    console.log(dropdown.scoring.val());
    if (dropdown.scoring.val() == 'all') $('#validity_param_div').hide(); else $('#validity_param_div').show();

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
    console.log('form changed');
    $('#main_comp_save_button').removeClass( "btn-outline-secondary" ).addClass( "btn-warning" );
    $('#save_button_warning_text').addClass('bg-warning').html('Competition needs to be saved');
  });

  // external event conversion
  $('#confirm_convert').click( function(){ $('#confirm_convert_modal').modal('show'); });
  $('#convert_confirmed').click( function(){
    window.location.href = "/users/_convert_external_comp/"+compid;
  });

});

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
  $('#formula_confirmed').attr("onclick","get_adv_settings()");
  $('#formula_modal').modal('show');
}

function add_task() {
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
  if (!external){
    columns.push({data: 'task_id', render: function ( data ) { return '<button class="btn btn-info ml-3" type="button" onclick="window.location.href = \'/users/track_admin/' + data + '\'">Tracks</button>'}});
  }
  columns.push({data: 'task_id', render: function ( data ) { return '<button class="btn btn-info ml-3" type="button" onclick="window.location.href = \'/users/task_score_admin/' + data + '\'">Scores</button>'}});
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
      console.log('numCols='+numCols);
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

function add_scorekeeper(){
  document.getElementById("save_scorekeeper_button").innerHTML = "Adding...";
  document.getElementById("save_scorekeeper_button").className = "btn btn-warning";
  var mydata = new Object();
  var e = document.getElementById('scorekeeper');
  mydata.id = e.options[e.selectedIndex].value;
  console.log('id='+mydata.id)
  $.ajax({
    type: "POST",
    url: link_add_scorekeeper,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function () {
      get_scorekeepers()
      document.getElementById("save_scorekeeper_button").innerHTML = "Save";
      document.getElementById("save_scorekeeper_button").className = "btn btn-success";
    }
  });
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
    console.log('val='+ el.value);
    console.log('checked='+ el.checked);
  });
  console.log('data='+ mydata);
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

function save_task(){
  $('#save_task_button').hide();
  $('#add_task_spinner').html('<div class="spinner-border" role="status"><span class="sr-only"></span></div>');
  var mydata = new Object();
  mydata.task_name = $('#task_name').val();
  mydata.task_date = $('#task_date').val();
  mydata.task_num = $('#task_number').val();
  mydata.task_comment = $('#task_comment').val();
  mydata.task_region = $('#task_region').val();

  $.ajax({
    type: "POST",
    url: link_add_task,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function () {
      get_tasks();
      $('#add_task_spinner').html('');
      $('#save_task_button').show();
      $('#add_task_modal').modal('hide');
    }
  });
}

function get_scorekeepers(){
  $.ajax({
     type: "GET",
     url: link_get_scorekeepers,
     contentType:"application/json",
     dataType: "json",
     success: function (response) {
       var content = '';
       for (var i = 0; i < response['scorekeepers'].length; i++) {
         content += '<tr><TD class="c3">'+ response['scorekeepers'][i]['first_name'] + ' '+ response['scorekeepers'][i]['last_name'] +'</TD></tr>'
       }
       $('#scorekeeper_table').append(content);
       $('#owner').html(response['owner']['first_name'] + ' ' + response['owner']['last_name'] );
     }
  });
}

function get_adv_settings(){
  var formula = new Object();
  formula.formula = $('#select_formula').val();
  formula.category = $('#select_category').val();
  formula.compid = compid;
  console.log(formula);
  $.ajax({
    type: "POST",
    url: link_get_adv_settings,
    contentType:"application/json",
    data : JSON.stringify(formula),
    dataType: "json",
    success: function (data) {
      $('#formula_distance').val(data.formula_distance);
      $('#formula_time').val(data.formula_time);
      $('#formula_arrival').val(data.formula_arrival);
      $('#formula_departure').val(data.formula_departure);
      $('#lead_factor').val(data.lead_factor);
      $('#no_goal_penalty').val(data.no_goal_penalty);
      $('#tolerance').val(data.tolerance);
      $('#min_tolerance').val(data.min_tolerance);
      $('#glide_bonus').val(data.glide_bonus);
      $('#arr_alt_bonus').val(data.arr_alt_bonus);
      $('#arr_max_height').val(data.arr_max_height);
      $('#arr_min_height').val(data.arr_min_height);
      $('#validity_min_time').val(data.validity_min_time);
      $('#scoreback_time').val(data.scoreback_time);
      $('#max_JTG').val(data.max_JTG);
      $('#JTG_penalty_per_sec').val(data.JTG_penalty_per_sec);
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
  cleanup_modal('rank_modal');
  $('#rank_type').val($('#rank_type option:first').val());
  update_ranking_modal($('#rank_type').val());
  $('#rank_modal').modal('show');
}

function edit_ranking(cranid) {
  cleanup_modal('rank_modal')
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
  let body = modal + '-body';
  let names = ['rank_id', 'rank_name', 'cert_id', 'min_date', 'max_date', 'attr_id', 'rank_value'];
  $('#'+modal+' .modal-errors').empty();  // delete all previous errors
  $('#'+body+' [name]').each( ( i, el ) => {
    if ( names.includes($(el).attr('name')) ) $(el).val('');
    $(el).removeAttr('style');
  });
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
