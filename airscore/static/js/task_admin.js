var turnpoints;
var task = {
  isset: null,
  ready_to_score: null
}


$(document).ready(function() {
  get_turnpoints();

  $('#main_task_settings_form :input').change(function(){
    console.log('form changed');
    $('#main_task_save_button').removeClass( "btn-outline-secondary" ).addClass( "btn-warning" );
    $('#save_button_warning_text').addClass('bg-warning').html('Task needs to be saved');
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
    {data: 'type', title: '', name: 'type', render: function ( data ) {
                                                                  if ( data == 'Waypoint' ){return ''}
                                                                  else {return data}
                                                                 }},
    {data: 'radius', title: 'Radius', name: 'radius', className: "text-right", defaultContent: ''},
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
      $('#number').val(json.next_number);
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

function save_turnpoint(){
  $('#add_waypoint_button').hide();
  $('#add_tp_spinner').html('<div class="spinner-border" role="status"><span class="sr-only"></span></div>');

  var radius = $('#radius').val();
  if( $('#type').val() == 'launch' && $('#check_launch').val() == 'n' ) {
    radius = 400;
  }
  var mydata = new Object();
  mydata.number = $('#number').val();
  mydata.type = $('#type').val();
  mydata.rwp_id = $('#name').val();
  mydata.direction = $('#how').val();
  mydata.shape = $('#shape').val();
  mydata.radius = radius;
  mydata.wpt_id = null
  $.ajax({
    type: "POST",
    url: url_add_turnpoint,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function (response) {
      if(task.isset != null && response.task_set != task.isset) {
        location.reload(true);
        return;
      }
      else {
        $('#add_waypoint_button').show();
        $('#add_tp_spinner').html('');
        update_turnpoints(response);
      }
    }
  });
}

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
  var found = turnpoints.find( el => el.wpt_id == tpid)
  console.log('found='+found.wpt_id+', '+found.name+', '+found.original_type)
  var original_num = found.num
  var myHeading = "<p>Modify turnpoint ";

  $('#mod_tp_number').val(found.num).change();
  $('#mod_tp_type').val(found.original_type).change();
  $('#mod_tp_name').val(found.rwp_id).change();
  $('#mod_tp_how').val(found.how).change();
  $('#mod_tp_shape').val(found.shape).change();
  $('#mod_tp_radius').val(found.radius).change();
  $("#delmodal-body").html(myHeading + original_num + '?</p>');
  $('#modify_confirmed').attr("onclick","save_modified_turnpoint('"+ tpid +"')");
  $('#modmodal').modal('show');
}

function save_modified_turnpoint(id){
  var radius =$('#mod_tp_radius').val();
  if($('#mod_tp_type').val() == 'launch' ){
    radius = 400;
    if($('#check_launch').val()=='y' ){
       radius = $('#mod_tp_launch_radius').val();
    }
  }
  var mydata = new Object();
  mydata.number = $('#mod_tp_number').val();
  mydata.type = $('#mod_tp_type').val();
  mydata.rwp_id = $('#mod_tp_name').val();
  mydata.direction = $('#mod_tp_how').val();
  mydata.shape = $('#mod_tp_shape').val();
  mydata.radius = radius;
  mydata.wpt_id = id

  $.ajax({
    type: "POST",
    url: url_add_turnpoint,
    data : JSON.stringify(mydata),
    contentType:"application/json",
    dataType: "json",
    success: function (response) {
      if(task.isset != null && response.task_set != task.isset) {
        location.reload(true);
        return;
      }
      update_turnpoints(response);
    }
  });
}

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
<!--         $('#progress_text').text(data.files[0].name);-->
    },
    success: function () {
      get_turnpoints();
    }
  });
});

function filesize(elem){
  document.cookie = `filesize=${elem.files[0].size}; SameSite=Strict; path=/`
}
