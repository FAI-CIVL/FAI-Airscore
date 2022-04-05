var turnpoints;
var isSubmitting = false;
var task = {
  isset: null,
  ready_to_score: null
}


$(document).ready(function() {
  $('#main_task_settings_form').data('initial-state', $('#main_task_settings_form').serialize());
  get_turnpoints();

  $('#main_task_settings_form :input').change(function(){
    if (!isSubmitting && $('form').serialize() != $('form').data('initial-state')) {
      $('#main_task_save_button').removeClass( "btn-outline-secondary" ).addClass( "btn-warning" );
      $('#save_button_warning_text').addClass('bg-warning').html('Task needs to be saved');
    }
    else {
      $('#main_task_save_button').removeClass( "btn-warning" ).addClass( "btn-outline-secondary" );
      $('#save_button_warning_text').removeClass('bg-warning').html('');
    }
  });

  $('#main_task_settings_form').submit( function() {
    isSubmitting = true
  })

  $(window).on('beforeunload', function() {
    if (!isSubmitting && $('#main_task_settings_form').serialize() != $('#main_task_settings_form').data('initial-state')) {
      return 'You have unsaved changes which will not be saved.'
    }
  });

  let stopped = $('#stopped_time').val();
  if (stopped) {
    console.log('Stopped Task');
    $('#stopped').addClass('show');;
  }

  let multigate = $('#SS_interval').val();
  if (multigate && multigate>0) {
    console.log('Multigate');
    $('#multi_start').addClass('show');;
  }

  // adding waypoint select filter
  $('#rwp_id').before('<input class="form-control form-control-sm" type="text" id="rwp_filter" value="" placeholder="Filter..." size="3">');

  $('#mod-type').on('change', function() {
    ['mod-how', 'mod-shape', 'mod-radius'].forEach( el => $('#'+el+'-div').hide() )
    let val = $(this).val();
    if ( val != 'launch' || $('#check_launch').is(':checked') ) $('#mod-radius-div').show();
    // if ( val == 'speed' ) $('#mod-how-div').show(); // not using Start direction anymore
    if ( val == 'goal' ) $('#mod-shape-div').show();
  });

  $('#type').on('change', function() {
    ['how', 'shape', 'radius'].forEach( el => $('#'+el+'-div').hide() )
    let val = $(this).val();
    if ( val != 'launch' || $('#check_launch').is(':checked') ) $('#radius-div').show();
    // if ( val == 'speed' ) $('#how-div').show(); // not using Start direction anymore
    if ( val == 'goal' ) $('#shape-div').show();
  });

  $('#rwp_filter').keyup( function() {
    let choices = $('#rwp_id option');
    let filter = $(this).val().toLowerCase();
    if( !filter ) {
      choices.each( (idx, el) => $(el).show() );
    }
    else {
      choices.each( (idx, el) => {
        if ( $(el).text().toLowerCase().includes(filter) ) $(el).show();
        else $(el).hide();
      });
    }
  });

});

function get_turnpoints(){
  $.ajax({
    type: "GET",
    url: url_get_task_turnpoints,
    contentType:"application/json",
    dataType: "json",
    success: function (response) {
      if(task.isset == null){
        task.isset = response.task_set;
      }
      else if (task.isset != response.task_set) {
        task.isset = response.task_set;
        location.reload(true);
        return;
      }
      update_turnpoints(response);
    }
  });
}

function update_turnpoints(json) {
  turnpoints = json.turnpoints;

  if(json.map != null) {
    $('#map_container').html(json.map);
    $('#map_container').attr("hidden", false);
  }
  else{
    $('#map_container').attr("hidden", true);
  }
  if (json.distance == 'Distance not yet calculated') {
    $('#task_distance').removeClass('text-info').addClass('text-warning').html(json.distance);
  }
  else {
    $('#task_distance').removeClass('text-warning').addClass('text-info').html('Task is set: Optimised distance is '+json.distance);
  }
  if( turnpoints.length == 0 ) {
    $('#delete_all_btn').hide();
    $('#import_task_btn').show();
    $('#copy_wpts_section').hide();
    if ( tasks.length > 1 ) {
      $('#copy_task_select').empty();
      tasks.forEach( t => {
        if (t.task_id != taskid) {
          $('#copy_task_select').append(
            $('<option>', {
              value: t.task_id,
              text: 'Task '+t.task_num+' - '+ t.opt_dist
            })
          );
        };
      });
      $('#copy_wpts_section').show();
    }
  }
  else {
    $('#import_task_btn').hide();
    $('#import_task').hide();
    $('#delete_all_btn').show();
  }

  let columns = [
    {data: 'num', title: '#', className: "text-right", defaultContent: ''},
    {data: 'wpt_id', title: 'wpt_id', defaultContent: '', visible: false},
    {data: 'name', title: 'ID', defaultContent: ''},
    {data: 'type_text', title: '', name: 'type', render: function ( data ) {
                                                                  if ( data == 'waypoint' ){return ''}
                                                                  else {return data}
                                                                 }},
    {data: 'radius', title: 'Radius', name: 'radius', className: "text-right", defaultContent: '', render: function ( data, type, row ) {
                                                                  if ( row.type == 'launch' && !$('#check_launch').is(':checked') ){return ''}
                                                                  else {return data}
                                                                 }},
    {data: 'partial_distance', title: 'Dist.', name: 'dist', className: "text-right", defaultContent: ''}
  ];
  if (!external){
    columns.push({data: 'wpt_id', render: function ( data, type, row ) { return '<button class="btn btn-warning ml-3" type="button" onclick="modify_tp(' + data + ')" data-toggle="confirmation" data-popout="true">Modify</button>'}});
    columns.push({data: 'wpt_id', render: function ( data, type, row ) { return '<button class="btn btn-danger ml-3" type="button" onclick="confirm_delete(' + row.num + ',' + data + ',' + row.partial_distance + ')" data-toggle="confirmation" data-popout="true">Delete</button>'}});
  }
  $('#task_wpt_table').DataTable({
    data: turnpoints,
    destroy: true,
    paging: false,
    responsive: true,
    saveState: true,
    info: false,
    bSort: false,
    dom: 'lrtip',
    columns: columns,
    rowId: function(data) {
      return 'id_' + data.wpt_id;
    },
    language: {
      emptyTable: "Task is empty"
    },
    initComplete: function(settings) {
      // manage wpt type selector
      $('#num').val(json.next_number);
      $("#type").children('option').hide();
      $("#new_waypoint_form").show();
      $("#type").prop('disabled', false).val('');
      $("#add_waypoint_button").prop('disabled', false);
      if ( json.next_number == 1 ) {
        $("#type option[value='launch']").show();
        $("#type").val('launch');
      }
      else {
        let table = $('#task_wpt_table').DataTable();
        let rows = $("tr", $('#task_wpt_table')).length-1;
        let wpt_type = table
                        .column('type:name')
                        .data()
                        .toArray();
        if ( !wpt_type.find(a =>a.includes('SSS')) ) {
          $("#type option[value='speed']").show();
          $("#type option[value='waypoint']").show();
          $("#type").val('speed');
        }
        else if ( !wpt_type.find(a =>a.includes('ESS')) ) {
          $("#type option[value='endspeed']").show();
          $("#type option[value='waypoint']").show();
          $("#type").val('waypoint');
        }
        else if ( !wpt_type.find(a =>a.includes('Goal')) ) {
          $("#type option[value='goal']").show();
          $("#type option[value='waypoint']").show();
          $("#type").val('goal');
        }
        else {
          $("#add_waypoint_button").prop('disabled', true);
          $("#type").prop('disabled', true).val('');
          $("#new_waypoint_form").hide();
        }
      }
      $("#type").trigger('change');
    }
  });
}

$('#turnpoint_form').submit( function(e) {
  e.preventDefault(); // block the traditional submission of the form.

  $('#add_waypoint_button').hide();
  $('#add_tp_spinner').html('<div class="spinner-border" role="status"><span class="sr-only"></span></div>');
  let mydata = $('#turnpoint_form').serialize();
  $.ajax({
    type: "POST",
    url: url_save_turnpoint,
    data : mydata,
    success: function (response) {
      if ( response.errors ) {
        response.errors.forEach( el => {
          let text = el[1][0];
          create_flashed_message(el[0]+': '+text, 'danger');
        });
      }
      else if(task.isset != null && response.task_set != task.isset) {
        location.reload(true);
        console.log('reload');
        return;
      }
      else {
        $('#add_waypoint_button').show();
        $('#add_tp_spinner').html('');
        update_turnpoints(response);
      }
    },
    error: function(result, status, error) {
      create_flashed_message('System Error trying to add a new waypoint', 'danger');
    }
  });
});

function delete_tp(tpid, partial_d){
  var mydata = new Object();
  mydata.partial_distance = partial_d ? partial_d : "";
  mydata.taskid = taskid;
  $('#delete_confirmed').hide();
  $('#delete_spinner').html('<div class="spinner-border" role="status"><span class="sr-only"></span></div>');
  $.ajax({
    type: "POST",
    url: '/users/_del_turnpoint/'+ tpid,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function (response) {
      if(task.isset != null && response.task_set != task.isset) {
        location.reload(true);
        return;
      }
      $('#delmodal').modal('hide');
      $('#delete_confirmed').show();
      $('#delete_spinner').html('');
      $('#map_container').html('');
      update_turnpoints(response);
    }
  });
}

function delete_all_tp(){
  $.ajax({
    type: "POST",
    url: '/users/_del_all_turnpoints/'+ taskid,
    contentType:"application/json",
    dataType: "json",
    success: function () {
      get_turnpoints();
      $('#map_container').html('');
    }
  });
}

function confirm_delete(tp_num, tpid, partial_distance) {
  var x = tp_num;
  var myHeading = "<p>Are you sure you want to delete Turnpoint ";
  $("#delmodal-body").html(myHeading + x + '?</p>');
  $('#delete_confirmed').attr("onclick","delete_tp("+tpid+", "+ partial_distance+")");
  $('#delmodal').modal('show');
}

function confirm_delete_all() {
  var myHeading = "<p>Are you sure you want to delete ALL Turnpoints";
  $("#delmodal-body").html(myHeading + '?</p>');
  $('#delete_confirmed').attr("onclick","delete_all_tp()");
  $('#delmodal').modal('show');
}

function modify_tp(tpid) {
  let found = turnpoints.find( el => el.wpt_id == tpid)
  let original_num = found.num;
  let myHeading = "<p>Modify turnpoint ";

  $('#mod-wpt_id').val(found.wpt_id).change();
  $('#mod-num').val(found.num).change();
  $('#mod-rwp_id').val(found.rwp_id).change();
  $('#mod-type').val(found.type).change();
  $('#mod-how').val(found.how).change();
  $('#mod-shape').val(found.shape).change();
  $('#mod-radius').val(found.radius).change();

  $("#delmodal-body").html(myHeading + original_num + '?</p>');
  $('#modmodal').modal('show');
}

$('#mod_turnpoint_form').submit( function(e) {
  e.preventDefault(); // block the traditional submission of the form.

  $('#mod_turnpoint_save_button').hide();
  let mydata = $('#mod_turnpoint_form').serialize();
  $.ajax({
    type: "POST",
    url: url_save_turnpoint,
    data : mydata,
    success: function (response) {
      if ( response.errors ) {
        response.errors.forEach( el => {
          let text = el[1][0];
          create_flashed_message(el[0]+': '+text, 'danger');
        });
      }
      else if(task.isset != null && response.task_set != task.isset) {
        location.reload(true);
        console.log('reload');
        return;
      }
      else {
        $('#mod_turnpoint_save_button').show();
        update_turnpoints(response);
        $('#modmodal').modal('hide');
      }
    }
  });
});

function copy_turnpoints() {
  mydata = { task_from: $('#copy_task_select').val() };
  $.ajax({
    type: "POST",
    url: '/users/_copy_turnpoints/'+taskid,
    contentType:"application/json",
    dataType: "json",
    data : JSON.stringify(mydata),
    success: function (response) {
      if ( !response.success ) {
        create_flashed_message('There was an Error trying to import Turnpoints', 'danger');
        get_turnpoints();
      }
      else {
        let data = response.data;
        if(task.isset == null){
          task.isset = data.task_set;
        }
        else if (task.isset != response.task_set) {
          task.isset = data.task_set;
//          location.reload(true);
//          return;
        }
        create_flashed_message('Turnpoints successfully imported.', 'success');
        update_turnpoints(response.data);
      }
    }
  });
}

$('#cancel_task_confirmed').click(function(){
  let mydata = {
    cancelled: task_info.cancelled,
    comment: $('#cancel_task_reason').val()
  };
  $.ajax({
    type: "POST",
    url: '/users/_declare_task_cancelled/'+ taskid,
    data : JSON.stringify(mydata),
    contentType:"application/json",
    dataType: "json",
    success: function (response) {
      if ( response.success ) window.location.reload(true);
      else create_flashed_message('Error trying to declare this task cancelled.', 'danger');
    }
  });
});

$('#XCTrack_button').click(function(){
  $('#XCTrack_fileupload').click();
});

$(function () {
  $('#XCTrack_fileupload').fileupload({
    dataType: 'json',
    done: function (e, data) {
      $.each(data.result.files, function (index, file) {
        $('<p/>').text(file.name).appendTo(document.body);
      });
    },
    submit: function (e, data){
      $('#upload_box').hide();
    },
    success: function () {
      get_turnpoints();
    }
  });
});

function filesize(elem){
  document.cookie = `filesize=${elem.files[0].size}; SameSite=Strict; path=/`
}
