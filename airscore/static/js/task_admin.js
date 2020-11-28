var turnpoints;

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
      if(response.reload){
        location.reload();
        return;
      }
      if(response.map != null) {
        $('#map_container').html(response.map);
        $('#map_container').attr("hidden", false);
      }
      else{
        $('#map_container').attr("hidden", true);
      }
      if(response.turnpoints.length > 0) {
        $('#import_task_btn').hide()
      }
      else {
        $('#delete_all_btn').hide();
        $('#import_task_btn').show()
      }
      update_turnpoints(response);
    }
  });
}

function update_turnpoints(json) {
  $('#delete_all_btn').hide();
  turnpoints = json.turnpoints;
  var columns = [];

  columns.push({data: 'num', title: '#', className: "text-right", defaultContent: ''});
  columns.push({data: 'wpt_id', title: 'wpt_id', defaultContent: '', visible: false});
  columns.push({data: 'name', title: 'ID', defaultContent: ''});
  columns.push({data: 'type', title: '', name: 'type', render: function ( data, type, row ) {
                                                                if ( data == 'Waypoint' ){return ''}
                                                                else {return data}
                                                               }});
  columns.push({data: 'radius', title: 'Radius', name: 'radius', className: "text-right", defaultContent: ''});
  columns.push({data: 'partial_distance', title: 'Dist.', name: 'dist', className: "text-right", defaultContent: ''});
  if (!external){
    columns.push({data: 'wpt_id', render: function ( data, type, row ) { return '<button class="btn btn-warning ml-3" type="button" onclick="modify_tp(' + data + ')" data-toggle="confirmation" data-popout="true">Modify</button>'}});
    columns.push({data: 'wpt_id', render: function ( data, type, row ) { return '<button class="btn btn-danger ml-3" type="button" onclick="confirm_delete(' + row.num + ',' + data + ',' + row.partial_distance + ')" data-toggle="confirmation" data-popout="true">Delete</button>'}});
  }
  $('#task_wpt_table').DataTable( {
    data: json.turnpoints,
    destroy: true,
    paging: false,
    responsive: true,
    saveState: true,
    info: false,
    dom: 'lrtip',
    columns: columns,
    rowId: function(data) {
      return 'id_' + data.wpt_id;
    },
    initComplete: function(settings) {
      var table = $('#task_wpt_table');
      var rows = $("tr", table).length-1;
      // Get number of all columns
      var numCols = table.DataTable().columns().nodes().length;
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
  $('#number').val(json['next_number']);
  $('#delete_all_btn').show();
}

function save_turnpoint(){
  $('#save_task_button').hide();
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
    success: function () {
      if(mydata.type == 'goal') {
        location.reload();
      }
      else {
        get_turnpoints();
        $('#save_task_button').show();
        $('#add_tp_spinner').html('');
      }
    }
  });
}

function delete_tp(tpid, partial_d){
    var mydata = new Object();
    mydata.partial_distance = partial_d;
    mydata.taskid = taskid;
    $('#delete_confirmed').hide();
    $('#delete_spinner').html('<div class="spinner-border" role="status"><span class="sr-only"></span></div>');
    $.ajax({
        type: "POST",
        url: '/users/_del_turnpoint/'+ tpid,
        contentType:"application/json",
        data : JSON.stringify(mydata),
        dataType: "json",
        success: function () {
            $('#delmodal').modal('hide');
            $('#delete_confirmed').show();
            $('#delete_spinner').html('');
            get_turnpoints();
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
       contentType:"application/json",
       data : JSON.stringify(mydata),
       dataType: "json",
       success: function () {
           get_turnpoints();
       }
   });
}

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
