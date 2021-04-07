// Task Scores Table
function populate_task_scores(){
  let filename = task.selected;
  $('#task_result').dataTable({
    ajax: '/users/_get_task_score_from_file/' + taskid + '/' + filename,
    paging: false,
    destroy: true,
    searching: true,
    info: false,
    columns: [
      {data: 'rank', title:'#'},
      {data: 'name', title:'Pilot'},
      {data: 'SSS', title:'SS'},
      {data: 'ESS', title:'ES'},
      {data: 'time', title:'Time'},
      {data: 'realdist', title:'real dist', id:'realdist', name:'realdist', visible: false},
      {data: 'altbonus', title:'alt bonus', id:'altbonus', name:'altbonus', visible: false},
      {data: 'distance', title:'Kms'},
      {data: 'speedP', title:'Spd', name:'spd'},
      {data: 'leadP', title:'LO', id:'leading', name:'leading'},
      {data: 'arrivalP', title:'Arv', id:'arv', name:'arv'},
      {data: 'distanceP', title:'Dst'},
      {data: 'penalty', title:'Pen'},
      {data: 'score', title:'Tot'},
      {data: null, title: 'Notifications'},
      {data: null, title: ""}
    ],
    rowId: function(data) {
      return 'id_' + data.par_id;
    },
    columnDefs: [{
      targets: [-2],  render: function (a, b, data, d) {
      if (data.notifications){
        var airspace = '';
        var track = '';
        var JTG = '';
        var admin = '';
        $.each( data.notifications, function( key, value ) {
          if (value.notification_type=="airspace"){
            airspace = 'CTR ';
          }
          if (value.notification_type=="track"){
            track = 'IGC ';
          }
          if (value.notification_type=="admin"){
            admin = 'Admin ';
          }
          if (value.notification_type=="jtg"){
            JTG = 'JTG ';
          }
        });
        return(airspace + track + JTG + admin);
      }
      else { return (""); }
      }},
      {
      targets: [-1],  render: function (a, b, data, d) {
      if ( !external && !task_info.locked ){
        return ('<td  class ="value" ><button type="button" class="btn btn-primary" onclick="adjust('
          + data.par_id + ')" data-toggle="confirmation" data-popout="true">Edit</button></td>');
      }
      else { return (""); }
      }}
    ],

    "language": {
      "emptyTable":     "Error: result file not found"
    },
    "initComplete": function(settings, json) {
      let table = $('#task_result').DataTable();
      if ( !json.stats.avail_arr_points ){
        table.column( 'arv:name' ).visible( false );
      };
      if ( !json.stats.avail_dep_points ){
        table.column( 'leading:name' ).visible( false );
      };
      if ( !json.stats.avail_time_points ){
        table.column( 'spd:name' ).visible( false );
      };
      if ( json.info.stopped_time ){
        table.column( 'realdist:name' ).visible( true );
        table.column( 'altbonus:name' ).visible( true );
      };
      score_data = json;
      $('#taskinfo tbody').empty()
      $.each( json.stats, function( key, value ) {
        $('#taskinfo tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
      });
    }
  });
}

function get_tracks_processed(){
  $.ajax({
    type: "GET",
    url: '/users/_get_tracks_processed/'+taskid,
    contentType:"application/json",
    dataType: "json",
    success: function (response) {
      if (response.tracks == response.pilots) {
        create_flashed_message('All pilots have a valid result for the task', 'success');
        suggested_status = 'Provisional Results';
      }
      else {
        create_flashed_message((response.pilots - response.tracks)+' pilots do not have a valid result for the task', 'warning');
        suggested_status = 'Partial Results ('+response.tracks+'/'+response.pilots+' Pilots)';
      }
      $('#TracksProcessed').text('Tracks Collected: ' + response.tracks + '/' + response.pilots)
    }
  });
}

function updateFiles(load_latest=false) {
  var mydata = new Object();
  mydata.offset = new Date().getTimezoneOffset();
  task.dropdown.empty().attr('disabled', 'disabled');

  $.ajax({
    type: "POST",
    url: url_get_task_result_files,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      let active = response.task_active;
      let header = response.task_header;
      let choices = response.task_choices;
      task.dropdown.empty().attr('disabled', 'disabled');
      task.header.html(header)
      if (choices.length == 0) {
        task.scoring_section.hide();
      }
      else {
        task.scoring_section.show();
        choices.forEach(function(item) {
          task.dropdown.append(
            $('<option>', {
              value: item[0],
              text: item[1]
            })
          );
        });
        if (!external) task.dropdown.removeAttr('disabled');
        if (active) task.active_file = active;
        task.latest = task.dropdown.find('option:first').val();
        if (load_latest || !active) task.dropdown.val(task.latest);
        else task.dropdown.val(active);
        task.selected = task.dropdown.find('option:selected').val();
        array = task.dropdown.find('option:selected').text().split(' - ');
        task.timestamp = array[0];
        task.status = array[1];
        console.log('active: '+task.active_file);
        console.log('selected: '+task.selected);
        console.log('latest: '+task.latest);
        console.log('status: '+task.status);
        console.log('timestamp: '+task.timestamp);
      };
      update_buttons();
      if (!task.selected) task.results_panel.hide();
      else {
        task.results_panel.show();
        populate_task_scores();
      }
    }
  });
}

// Toggle Publish
function toggle_publish() {
  let mydata = {
    filetext: task.dropdown.find('option:selected').text(),
    filename: task.dropdown.find('option:selected').val(),
    iscomp: false,
    compid: compid,
    taskid: taskid
  }
  let url = '';
  if (mydata.filename == task.active_file) {
    url = '/users/_unpublish_result';
  }
  else {
    url = '/users/_publish_result';
  }
  $.ajax({
    type: "POST",
    url: url,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      task.active_file = response.filename;
      update_buttons();
      task.header.text(response.header);
    }
  });
}

// Scores
function Score_modal() {
  $('#status_comment').val(suggested_status);
  $('#scoremodal').modal('show');
}

function Score() {
  var mydata = new Object();
  mydata.autopublish = $("#autopublish").is(':checked');
  mydata.status = $('#status_comment').val();
  $('#score_btn').hide();
  $('#cancel_score_btn').hide();
  $('#score_spinner').html('<div class="spinner-border" role="status"><span class="sr-only">Scoring...</span></div>');
  $.ajax({
    type: "POST",
    url: url_score_task,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      clear_flashed_messages();
      if ( response.success ){
        if (production) {
          $('#scoremodal').modal('hide');
          create_flashed_message('New scoring file created.', 'success');
          updateFiles(load_latest=true);
        }
        else if (response.redirect) {
          window.location.href = response.redirect;
        }
      }
    }
  });
}

function FullRescore() {
  var mydata = new Object();
  mydata.autopublish = $("#fullautopublish").is(':checked');
  mydata.status = $('#fullstatus_comment').val();
  $('#fullscore_btn').hide();
  $('#cancel_fullscore_btn').hide();
  $('#fullscore_spinner').html('<div class="spinner-border" role="status"><span class="sr-only">Preparing to score..</span></div>');
  $.ajax({
    type: "POST",
    url: url_full_rescore_task,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      clear_flashed_messages();
      if (production == false) {
        $('#fullscoremodal').modal('hide');
        create_flashed_message('All tracks have been processed. New scoring file created.', 'success');
      }
      else {
        create_flashed_message('Processing tracks. Please wait...', 'warning');
      }
    }
  });
}

// Change Status
function open_status_modal() {
  $('#status_modal_filename').val(task.selected);
  $('#status_modal_comment').val(task.status);
  $('#statusmodal').modal('show');
}

function change_status() {
  let mydata = {
    filename: $('#status_modal_filename').val(),
    status: $('#status_modal_comment').val()
  }
  $.ajax({
    type: "POST",
    url: url_change_result_status,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      if (response.success) {
        updateFiles();
        $('#status_modal_filename').val('');
        $('#status_modal_comment').val('');
        $('#statusmodal').modal('hide');
      }
    }
  });
}

// Result Adjustment
function adjust(par_id){
  $("#edit_table tbody").empty();
  $.each( score_data.data, function(  key, value ) {
    if(value.par_id==par_id){
      $.each( this.notifications, function(  key, value ) {
        var edit='false'
        if(value.notification_type=='admin'){ edit='true'}
        $('#edit_table tbody').append('<tr><td data-editable="false" style="display:none;" class ="value">'+ value.not_id +'</td>'
          +'<td data-editable="false" class ="value">'+ value.notification_type +'</td>'
          +'<td data-editable="false" class ="value">'+ value.percentage_penalty*100 +'%</td>'
          +'<td data-editable='+ edit + ' class ="value">'+ value.flat_penalty +'</td>'
          +'<td data-editable='+ edit + ' class ="value">'+ value.comment +'</td></tr>');
    <!--          <td data-editable="false" class ="value"><button type="button" class="btn btn-primary">Delete</button></td>-->
      });
    }
    $('#save_adjustment').attr("onclick","save_adjustment("+par_id+")");
    $('#edit_table').editableTableWidget();
    $('#editmodal').modal('show');
  });
}

function get_table_data(){
  table_data=[];
  // loop over each table row (tr)
  $("#edit_table tr").each(function(){
    var currentRow=$(this);
    var obj={};
    obj.not_id=parseInt(currentRow.find("td:eq(0)").text());
    obj.source=currentRow.find("td:eq(1)").text();
    obj.penalty=parseInt(currentRow.find("td:eq(3)").text());
    obj.comment=currentRow.find("td:eq(4)").text();
    if(obj.source == "admin"){
      table_data.push(obj);
    }
  });
}

function save_adjustment(par_id){
  var mydata = new Object();
  mydata.filename = task.selected;
  mydata.par_id = par_id;
  mydata.changes = [];
  mydata.new = {};
  if($('#penalty').val()!=0 || $('#comment').val()!=''){
    mydata.new.penalty = parseInt($('#penalty').val());
    mydata.new.comment = $('#comment').val();
    mydata.new.sign = $('#penalty_bonus').val();
  }
  //get any admin rows
  get_table_data();
  if (table_data!=[]) {
    //see if there are any changes to admin rows
    $.each(score_data.data, function(  key, value ) {
      //find original values
      if(value.par_id==par_id){
        $.each( this.notifications, function(  key, value ) {
          if(value.notification_type == 'admin'){
            table_data.forEach(function(element) {
              if(element.not_id==value.not_id){
                //we have a match
                if((element.comment!=value.comment)||(element.penalty!=value.flat_penalty)) {
                  mydata.changes.push(element);
                }
              }
            });
          }
        });
      }
    });
  }
  if ((mydata.new.penalty || mydata.new.comment) || mydata.changes){
    //send the adjustment
    $.ajax({
      type: "POST",
      url:  url_adjust_task_result,
      contentType: "application/json",
      data: JSON.stringify(mydata),
      dataType: "json",
      success: function(response) {
        populate_task_scores();
        $('#editmodal').modal('hide');
      }
    });
  }
}

// Delete Result
function delete_result_modal() {
  let title = 'Delete Task Result';

  $('#delete_modal_filename').val(task.selected);
  let selected = task.dropdown.find('option:selected').text().split(' - ');
  let ran = selected[0];
  let status = selected[1];
  if (!status) status = '<span class="text-secondary">No status</span>';
  else status = 'Status: <strong class="text-info">'+status+'</strong>';
  $('#delete_modal_title').html(title);
  $('#delete_description').html('Ran: <strong class="text-info">'+ran+'</strong>; '+status);
  $('#deletemodal').modal('show');
}

function delete_result(){
  var mydata = new Object();
  mydata.deletefile = $("#deletefile").is(':checked');
  mydata.filename = $('#delete_modal_filename').val();
  $.ajax({
    type: "POST",
    url:  '/users/_delete_task_result',
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      updateFiles();
      $('#deletemodal').modal('hide');
    }
  });
}

// Functions
function get_preview_url() {
  let file = task.selected;
  let url = '/task_result/'+taskid;
  url += '?file='+file;
  return url
}

function get_status(){
  let array = task.dropdown.find('option:selected').text().split(' - ');
  task.timestamp = array[0];
  task.status = array[1];
}

function ismissing(status){
  if (status == 'FILE NOT FOUND') return true; else return false;
}

function update_publish_button() {
  if (task.selected == task.active_file) {
    task.publish.text('Un-Publish results');
    task.publish.addClass('btn-warning').removeClass('btn-success');
  }
  else {
    task.publish.text('Publish results');
    task.publish.addClass('btn-success').removeClass('btn-warning');
  }
}

function check_active() {
  let html = 'task_html';
  let filename = task.active_file;

  if (task.active_file) {
    task.download_html.attr('onclick', "location.href='/users/_download/"+html+"/"+filename+"'");
    task.download_html.show();
    // check file exists
    if (task.dropdown.find('option[value="'+task.active_file+'"]').text().includes('FILE NOT FOUND')){
      task.download_html.prop('disabled', true);
    }
    else task.download_html.prop('disabled', false);
  }
  else {
    task.download_html.attr('onclick', "");
    task.download_html.hide();
  }
}

function update_buttons() {
  if ( task_info.locked ) {
    task.publish.text('Locked');
    task.publish.addClass('btn-secondary').removeClass('btn-success').removeClass('btn-warning');
    task.publish.prop('disabled', true);
    task.change_status.removeClass('btn-secondary').addClass('btn-primary');
    task.change_status.prop('disabled', false);
    task.preview.removeClass('btn-secondary').addClass('btn-primary');
    task.preview.attr('onclick', "window.open('"+ get_preview_url()+"','preview')");
    task.preview.prop('disabled', false);
  }
  else if (ismissing(task.status)) {
    task.publish.text('Publish results');
    task.publish.addClass('btn-secondary').removeClass('btn-success').removeClass('btn-warning');
    task.publish.prop('disabled', true);
    task.change_status.addClass('btn-secondary').removeClass('btn-primary');
    task.change_status.prop('disabled', true);
    task.preview.addClass('btn-secondary').removeClass('btn-primary');
    task.preview.removeAttr('onclick');
    task.preview.prop('disabled', true);
  }
  else {
    task.publish.removeClass('btn-secondary');
    task.publish.prop('disabled', false);
    update_publish_button();
    task.change_status.removeClass('btn-secondary').addClass('btn-primary');
    task.change_status.prop('disabled', false);
    task.preview.removeClass('btn-secondary').addClass('btn-primary');
    task.preview.attr('onclick', "window.open('"+ get_preview_url()+"','preview')");
    task.preview.prop('disabled', false);
  }
  if (external || (task.selected == task.active_file && !ismissing(task.status)) || task.selected.includes('Overview')){
    task.delete_file.prop('disabled', true);
  }
  else task.delete_file.prop('disabled', false);
  check_active();
}


// Main Section
var score_data = new Object();
table_data = [];

// jQuery selection for the file select box
var task = {
  dropdown: $('select[name="task_result_file"]'),
  delete_file: $('#delete_result'),
  publish: $('#publish'),
  change_status: $('#change_status'),
  download_html: $('#download_task_html'),
  preview: $('#task_preview'),
  header: $("#task_result_header"),
  scoring_section: $('#scoring_runs_section'),
  results_panel: $('#task_results_panel'),
  lock_switch: $('#lock_task_button'),
  active_file: '',
  selected: '',
  latest: '',
  timestamp: '',
  status: ''
};

var suggested_status = '';

$(document).ready(function() {
  if (task_info.locked) {
    suggested_status = 'Official Results';
  }
  else get_tracks_processed();

  updateFiles();


  // Event listener to the file picker to redraw on input
  task.dropdown.change(function() {
    task.selected = task.dropdown.find('option:selected').val();
    get_status(task);
    update_buttons();
    populate_task_scores();
  });

  task.lock_switch.click( function() {
    let mydata = {
      locked: task_info.locked
    }
    $.ajax({
      type: "POST",
      url:  '/users/_task_lock_switch/'+taskid,
      contentType: "application/json",
      data: JSON.stringify(mydata),
      dataType: "json",
      success: function(response) {
        window.location.reload(true);
      }
    });
  });

  function initES() {
    if (es == null || es.readyState == 2) { // this is probably not necessary.
      es = new EventSource(url_sse_stream);
      es.onerror = function(e) {
        if (es.readyState == 2) {
          setTimeout(initES, 5000);
        }
      };
      es.addEventListener('info', function(event) {
        var data = JSON.parse(event.data);
        $('#process_text').append(data.message + "<br/>");
      }, false);
      es.addEventListener('open_modal', function(event) {
        $('#log_button').show();
        $('#fullscoremodal').modal('hide');
        $('#ProcessModal').modal('show');
      }, false);

      es.addEventListener('track_counter', function(event) {
        var data = JSON.parse(event.data);
        $('#ProcessModalTitle').text('Tracklog Processing:'+ data.message);
      }, false);

      es.addEventListener('reload', function(event) {
        task.selected = task.dropdown.find('option:selected').val();
        clear_flashed_messages();
        updateFiles();
        create_flashed_message('All tracks have been processed. New scoring file created.', 'success');
      }, false);

      es.addEventListener('reload_select_latest', function(event) {
        clear_flashed_messages();
        updateFiles(load_latest=true);
        create_flashed_message('All tracks have been processed. New scoring file created.', 'success');
      }, false);
    }
  }

  if (production == true) {
    var es = null;
    initES();
  }
});
