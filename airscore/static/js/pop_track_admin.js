function populate_track_admin(task_id) {
  $('#tracks').DataTable({
    destroy: true,
    ajax: '/users/_get_tracks_admin/'+task_id,
    paging: false,
    order: [[ 0, 'asc' ]],
    searching: true,
    info: false,
    columns: [
      {data: 'ID', title: 'ID', name:'ID'},
      {data: 'name', title: 'Name', name:'Name'},
      {data: 'Result', title: 'Result', name:'Result'},
      {data: null}
    ],
    rowId: function(data) {
            return 'id_' + data.par_id;
    },
    columnDefs:[
      { targets: [0], width: '3rem' },
      { targets: [1], width: '12rem' },
      { targets: [2], width: '10rem' },
      {
        targets: [-1], render: function (a, b, data, d) {
          if ( task_info.cancelled || task_info.locked ) {
            return '<span class="btn btn-info">locked<span>';
          }
          else if(data['Result']=='Not Yet Processed' | data['Result'].indexOf("G record") >= 0){
            let buttons;
            buttons =
             '<button id="ABS' + data.par_id  +'" class="btn btn-primary mt-1 mb-1" type="button" onclick="set_result(' + data.par_id +',\'abs\')">Set ABS</button> '
             +'<button id="MD' + data.par_id  +'" class="btn btn-primary mt-1 mb-1" type="button" onclick="set_result(' + data.par_id +',\'mindist\')">Set Min Dist</button> '
             +'<button id="DNF' + data.par_id  +'" class="btn btn-primary mt-1 mb-1" type="button" onclick="set_result(' + data.par_id +',\'dnf\')">Set DNF</button> '
             +'<button id="TrackUp' + data.par_id  +'" class="btnupload btn btn-primary mt-1 mb-1" onclick="choose_file(' + data.par_id +');">Upload Track</button>'
             +'<div id="filediv' + data.par_id  +'" class = "hideatstart" > '
             +'<input id="fileupload' + data.par_id +'" type="file" size="chars" class="custom-file-input"  oninput="filesize(this);" data-url="/users/_upload_track/'+ task_id + '/' + data.par_id + '" name="tracklog" >'
             +'<input id="fileupload_NO_G' + data.par_id +'" type="file" size="chars" class="custom-file-input"  oninput="filesize(this);" data-url="/users/_upload_track/'+ task_id + '/' + data.par_id + '" name="tracklog_NO_G" >'
             +'<input id="fileupload_NO_V' + data.par_id +'" type="file" size="chars" class="custom-file-input"  oninput="filesize(this);" data-url="/users/_upload_track/'+ task_id + '/' + data.par_id + '" name="tracklog_NO_V" >'
             +'</div>'
             +'<div class="hideatstart progress mt-3 mb-3" id="progress'+ data.par_id +'" ><div class="progress-bar text-left pl-2" style="width: 0%;"></div></div>';
            return buttons;
          }
          else if (data['Result']=='Processing..') {
            return data['file']
          }
          else if ( ['ABS', 'DNF', 'Min Dist'].includes(data.Result) ){
            return '<button class="btn btn-warning mt-1 mb-1" type="button" onclick="delete_track('+ data.track_id +','+ data.par_id +')">Set NYP</button> ';
          }
          else {
            let column = '<button class="btn btn-danger mt-1 mb-1" type="button" onclick="delete_track('+ data.track_id +','+ data.par_id +')">Delete Track</button> ';
            if (data.outdated) column += '<button class="btn btn-warning mt-3" id="button_check_'+data.par_id+'" type="button" onclick="recheck_track('+ data.track_id +','+ data.par_id +')">Recheck Track</button> ';
            return column
          }
        }
      }
    ],
    drawCallback: function() {
      refresh_popover()
    },
    initComplete: function(response) {
      let rows = response.json.data;
      $(".hideatstart").hide();
      $('#recheck_button').hide();
      if ( rows.some( el => el.outdated ) ) {
        $('#recheck_button').prop('disabled', false).show();
      }
    },
  });
}

function open_bulk_modal() {
  $('#bulkmodal').modal('show');
}

function filesize(elem){
    document.cookie = `filesize=${elem.files[0].size}; SameSite=Strict; path=/`
}

function update_row(new_data){
  update_track_pilot_stats();
  let table = $('#tracks').dataTable();
  new_data.ID = $('#tracks').DataTable().row( $('tr#id_'+ new_data.par_id)).data()['ID'];
  new_data.name = $('#tracks').DataTable().row( $('tr#id_'+ new_data.par_id)).data()['name'];
  table.fnUpdate(new_data, $('tr#id_'+ new_data.par_id), undefined, false);
  $(".hideatstart").hide();
  refresh_popover();
  console.log(new_data.ID+' '+new_data.name);
}

function delete_track(track_id, par_id){
  var mydata = new Object();
  mydata.track_id = track_id;
  mydata.par_id = par_id;
  $.ajax({
    type: "POST",
    url: "/users/_delete_track/" + track_id,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function (response, par_id) {
        update_row(response);
    }
  });
}

function recheck_track(trackid, parid) {
  $('#button_check_'+parid).prop('disabled', true);
  let mydata = new Object();
  mydata.parid = parid;
  mydata.taskid = taskid;

  $.ajax({
    type: "POST",
    url: '/users/_recheck_track/'+trackid,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function (response) {
      if (response.success && !production) {
        update_row(response);
        create_flashed_message('Track result updated.', 'success');
      }
      else if (response.error) {
        $('#button_check_'+parid).prop('disabled', false);
        create_flashed_message('Track updating failed.', 'danger');
      }
    }
  });
}

function recheck_tracks() {
  $('#recheck_button').prop('disabled', true);
  $.ajax({
    type: "POST",
    url: '/users/_recheck_task_tracks/'+taskid,
    contentType:"application/json",
    dataType: "json",
    success: function (response) {
      if ( response.success ) {
        console.log( response );
        if (!production) {
          $('#recheck_button').prop('disabled', false);
          populate_track_admin( taskid );
          update_track_pilot_stats();
        }
        else {
          create_flashed_message('Processing tracks, please wait...', 'warning');
        }
      }
      else {
        create_flashed_message('ERROR processing tracks.', 'danger');
      }
    }
  });
}

function send_telegram(task_id){
  document.getElementById("telegram_button").innerHTML="Sending...";
  document.getElementById("telegram_button").className = "btn btn-warning ml-4";
  $.ajax({
    type: "POST",
    url: "/users/_send_telegram_update/" + task_id,
    contentType:"application/json",
    dataType: "json",
    success: function (response) {
      if (response.success == true) {
        document.getElementById("telegram_button").innerHTML="Success";
        document.getElementById("telegram_button").className = "btn btn-success ml-4";
      }
      else {
        document.getElementById("telegram_button").innerHTML="Failed";
        document.getElementById("telegram_button").className = "btn btn-danger ml-4";
      }
      setTimeout(function(){
        document.getElementById("telegram_button").innerHTML="Update Telegram";
        document.getElementById("telegram_button").className = "btn btn-primary ml-4";
      }, 3000);
    }
  });
}

function set_result(par_id, status){
  let mydata = new Object();
  mydata.par_id = par_id;
  mydata.Result = status;

  $.ajax({
    type: "POST",
    url: url_set_result,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function (response, par_id) {
      update_row(response);
    }
  });
}

function update_track_pilot_stats(){
  $.ajax({
    type: "GET",
    url: url_get_tracks_processed,
    contentType:"application/json",
    dataType: "json",
    success: function (response) {
      $('#TracksProcessed').text('Tracks Collected: ' + response.tracks + '/' + response.pilots)
    }
  });
}

function get_xcontest_tracks(){
  $('#xcontest_button').addClass('btn-warning').removeClass('btn-primary').text("Getting Tracks...");
  $.ajax({
    type: "POST",
    url: url_get_xcontest_tracks,
    contentType:"application/json",
    dataType: "json",
    success: function (response) {
      if ( response.success ) {
        if (production == false){
          populate_track_admin(taskid);
          update_track_pilot_stats();
        }
      }
      else {
        create_flashed_message("We could not find tracks on XContest for the event", "danger");
      }
      $('#xcontest_button').removeClass('btn-warning').addClass('btn-primary').text("Xcontest");
    }
  });
}

function choose_zip_file(){
  var filename;
  $('#bulk_fileupload').fileupload({
    dataType: 'json',
    done: function (e, data) {
      $.each(data.result.files, function (index, file) {
        $('<p/>').text(file.name).appendTo(document.body);
        filename = file.name;
      });
    },
    submit: function (e, data){
      $("bulk_button").text('Processing...');
      $("bulk_button").removeClass("btn-primary").addClass('btn btn-warning');
      $('#zip_modal_message').hide();
      $('#zip_progress').show();
      $('#zip_spinner').show();
      $('#zip_progress_text').text(data.files[0].name + ' - processing');
      $('#zip_spinner').html('<div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div>');
    },
    success: function (response) {
      if (response.success){
        $("bulk_button").text('Done');
        $("bulk_button").removeClass("btn-warning").addClass('btn-success');
        create_flashed_message('Archive successfully processed.', 'info');
      }
      else {
        create_flashed_message('There was an error trying to process archive.', 'danger');
        if (response.error) create_flashed_message(response.error, 'warning');
      }
      $('#bulkmodal').modal('hide');
      $('#zip_modal_message').show();
      $('#zip_progress').hide();
      $('#zip_spinner').hide();
      $('#zip_progress_text').text('');
      $('#zip_spinner').html('');
      if (production == false){
        populate_track_admin(taskid);
        update_track_pilot_stats();
      }
    },
    progress: function (e, data) {
      var progress = parseInt(data.loaded / data.total * 100, 10);
      $('#zip_progress .bar').css(
        'width',
        progress + '%'
      );
    },
    complete: function () {
      setTimeout(function(){
        $("bulk_button").text('Bulk Import Tracks');
        $("bulk_button").removeClass('btn-warning').removeClass('btn-success').addClass('btn-primary');
      }, 3000);
    }
  });
  $('#bulk_fileupload').click();
}

function get_lt_status() {
  $.ajax({
    type: "GET",
    url: '/users/_get_lt_info/'+taskid,
    contentType:"application/json",
    dataType: "json",
    success: function ( response ) {
      $('#lt_modal_button').hide();
      console.log(response);
      if ( response.success ) {
        // Livetrack service is currently running for the task
        let status = 'STATUS: ';
        let details = 'Updated: ';
        let info = '';
        if ( response.status ) {
          details += (response.status.updated ? response.status.updated + ' (UTC)' : 'Unknown') + '<br />';
          if ( response.status.finished ) status += 'Terminated <br />'
          else if ( response.status.scheduled ) {
            status += 'Running <br />';
            info = 'Next update schedule: ' + (response.registry.scheduled.length ? response.registry.scheduled[0] : 'Unknown');
          }
          else status += 'Unknown';
        }
        else status += 'Unknown';
        $('#lt_details_main').html(status + details);
        $('#lt_details_secondary').html(info);

        $('#lt_modal_button').attr("onclick","window.open('/live/"+taskid+"', '_blank')").text('LIVE Rankings').show();
        $('#livetracking_button').removeClass( "btn-primary btn-warning" ).addClass( "btn-success" ).text('Live Tracking Info');
        update_track_pilot_stats();
      }
      else if ( response.error ) {
        // Livetrack service started but stopped with errors
        $('#lt_details_main').text('ERROR');
        $('#lt_details_secondary').text(response.error);
        $('#lt_modal_button').attr("onclick","start_livetracking()").text('TRY AGAIN').show();
        $('#livetracking_button').removeClass( "btn-primary btn-success" ).addClass( "btn-warning" ).text('Live Tracking');
        update_track_pilot_stats();
      }
      else {
        // Livetrack has not run yet on this task
        $('#lt_details_main').text('Start Live Tracking');
        $('#lt_details_secondary').html('To start livetrack service, retrieving tracks in real time from ' + task_info.track_source + ', click START');
        $('#lt_modal_button').attr("onclick","start_livetracking()").text('START').show();
        $('#livetracking_button').text('Live Tracking');
        $('#livetracking_button').removeClass( "btn-warning btn-success" ).addClass( "btn-primary" ).text('Live Tracking');
      }
    }
  });
}

function start_livetracking() {
  $.ajax({
    type: "GET",
    url: '/users/_start_task_livetracking/'+taskid,
    contentType:"application/json",
    dataType: "json",
    success: function ( response ) {
      $('#lt_modal_button').hide();
      console.log(response);
      if ( response.success ) {
        $('#livetracking_button').text('Live Tracking Info');
      }
      $('#lt_modal').modal('hide');
    }
  });
}

function choose_file_prod(par_id, g_overide=false, v_overide=false){
  var filename;
  var suffix = '';
  if(g_overide){
    suffix = '_NO_G'
  }
  if(v_overide){
    suffix = '_NO_V'
  }
  $('#fileupload' + suffix + par_id).fileupload({
    dataType: 'json',
    done: function (e, data) {
      $.each(data.result.files, function (index, file) {
        $('<p/>').text(file.name).appendTo(document.body);
        filename = file.name;
      });
    },
    submit: function (e, data){
      $('#ABS'+ par_id).hide();
      $('#MD'+ par_id).hide();
      $('#DNF'+ par_id).hide();
      $('#TrackUp'+ par_id).hide();
      $('#upload_box'+ par_id).hide();
      $('#progress'+ par_id).show();
      $('#filediv'+ par_id).hide();
    },
    success: function (response) { // display success response
      if ( response.success ) {
        console.log('Success!');
      }
      else {
        $('#ABS'+ par_id).show();
        $('#MD'+ par_id).show();
        $('#DNF'+ par_id).show();
        $('#TrackUp'+ par_id).show();
        $('#upload_box'+ par_id).show();
        $('#filediv'+ par_id).hide();
        $('#progress'+ par_id).hide();
        toastr.error(response.error, 'Error', {timeOut: 5000});
      }
    },
    error: function (response) {
      $('#ABS'+ par_id).show();
      $('#MD'+ par_id).show();
      $('#DNF'+ par_id).show();
      $('#TrackUp'+ par_id).show();
      $('#upload_box'+ par_id).show();
      $('#filediv'+ par_id).hide();
      $('#progress'+ par_id).hide();
      clear_flashed_messages();
      create_flashed_message('System error. Please contact Administrators.', 'danger'); // display error response
    }
  });
  $('#fileupload' + suffix + par_id).click();
};

function choose_file_test(par_id){
  var filename;
  $('#fileupload' + par_id).fileupload({
    dataType: 'json',
    done: function (e, data) {
      $.each(data.result.files, function (index, file) {
        $('<p/>').text(file.name).appendTo(document.body);
        filename = file.name;
      });
    },
    submit: function (e, data){
      $('#ABS'+ par_id).hide();
      $('#MD'+ par_id).hide();
      $('#DNF'+ par_id).hide();
      $('#TrackUp'+ par_id).hide();
      $('#upload_box'+ par_id).hide();
      $('#filediv'+ par_id).show();
      $('#progress_text'+ par_id).text(data.files[0].name + ' - processing');
      $('#spinner' + par_id).html('<div class="spinner-border" role="status"><span class="sr-only"></span></div>');
    },
    success: function (response) {
      if (response.error){
        $('#ABS'+ par_id).show();
        $('#MD'+ par_id).show();
        $('#DNF'+ par_id).show();
        $('#TrackUp'+ par_id).show();
        $('#upload_box'+ par_id).show();
        $('#filediv'+ par_id).hide();
        $.alert(response.error,{
          type: 'danger',
          position: ['center', [-0.42, 0]],
          autoClose: false
        });
      }
      update_row(response);
    },
    progress: function (e, data) {
      var progress = parseInt(data.loaded / data.total * 100, 10);
      $('#progress'+ par_id+' .progress-bar').css(
        'width',
        progress + '%'
      );
    }
  });
  $('#fileupload' + par_id).click();
};

function choose_file(par_id, g_overide=false, v_overide=false) {
    if (production == true) choose_file_prod(par_id, g_overide, v_overide); else choose_file_test(par_id);
}

$(document).ready(function(){
  $('#log_button').hide();
  populate_track_admin(taskid);
  update_track_pilot_stats();

  // check livetracking status if feature is available
  if ( $('#livetracking_button').length ) {
    get_lt_status();

    // listener
    $('#livetracking_button').click( function() {
      get_lt_status();
      $('#lt_modal').modal('show');
    });
  }

  function initES() {
    if (es == null || es.readyState == 2) { // this is probably not necessary.
      es = new EventSource(url_sse_stream);
      es.onerror = function(e) {
        if (es.readyState == 2) {
          setTimeout(initES, 5000);
        }
      };

      es.addEventListener('flashed', function(event) {
        let data = JSON.parse(event.data);
        create_flashed_message(data.message, 'warning');
      }, false);

      es.addEventListener('track_error', function(event) {
        let data = JSON.parse(event.data);
        create_flashed_message(data.message.text, 'danger');
        $('#ABS'+ data.id).show();
        $('#MD'+ data.id).show();
        $('#DNF'+ data.id).show();
        $('#TrackUp'+ data.id).show();
        $('#upload_box'+ data.id).show();
        $('#filediv'+ data.id).hide();
        $('#progress'+ data.id).hide();
//        update_row(data.message);
      }, false);

      es.addEventListener('% complete', function(event) {
        let data = JSON.parse(event.data);
        $('#progress'+ data.id).show();
        $('#progress'+ data.id + ' .progress-bar').css("width", data.message + "%").text(data.message + '%');
      }, false);

      es.addEventListener('track_counter', function(event) {
        let data = JSON.parse(event.data);
        $('#ProcessModalTitle').text('Tracklog Processing: ' + data.message);
      }, false);

      es.addEventListener('info', function(event) {
        let data = JSON.parse(event.data);
        $('#process_text').append(data.message + "<br/>");
      }, false);

      es.addEventListener('open_modal', function(event) {
        $('#log_button').show();
        $('#ProcessModal').modal('show');
      }, false);

      es.addEventListener('result', function(event) {
        let data = JSON.parse(event.data);
        if(data.message == 'error'){
          $('#ABS'+ data.id).show();
          $('#MD'+ data.id).show();
          $('#DNF'+ data.id).show();
          $('#TrackUp'+ data.id).show();
          $('#upload_box'+ data.id).show();
          $('#filediv'+ data.id).hide();
          update_track_pilot_stats();
        }
        else if (data.id){
          let info = $.parseJSON(data.message);
          toastr.success('Result: '+info.Result, 'Pilot ID '+info.ID, {timeOut: 5000});
          update_row(info);
        }
      }, false);

      es.addEventListener('valid_fail', function(event) {
        let data = JSON.parse(event.data);
        data.message = JSON.parse(data.message);
        $('#ABS'+ data.id).show();
        $('#MD'+ data.id).show();
        $('#DNF'+ data.id).show();
        $('#TrackUp'+ data.id).show();
        $('#upload_box'+ data.id).show();
        $('#filediv'+ data.id).hide();
        $('#progress'+ data.id).hide();
        data.message.Result = '<button id="TrackUp_noV' + data.id  +'" class="btnupload btn btn-warning mt-3" onclick="choose_file(' + data.id +', false, true);">Upload IGC ignoring quality check & G record</button>';
        update_row(data.message);
        toastr.warning(data.message.text, 'Track not Valid', {timeOut: 5000});
      }, false);

      es.addEventListener('g_record_fail', function(event) {
        let data = JSON.parse(event.data);
        data.message = JSON.parse(data.message);
        $('#ABS'+ data.id).show();
        $('#MD'+ data.id).show();
        $('#DNF'+ data.id).show();
        $('#TrackUp'+ data.id).show();
        $('#upload_box'+ data.id).show();
        $('#filediv'+ data.id).hide();
        $('#progress'+ data.id).hide();
        data.message.Result = '<button id="TrackUp_noG' + data.id  +'" class="btnupload btn btn-warning mt-3" onclick="choose_file(' + data.id +', true);">Upload IGC ignoring G record</button>';
        update_row(data.message);
        toastr.warning(data.message.text, 'G Record Fail', {timeOut: 5000});
      }, false);

      es.addEventListener('livetracking', function(event) {
        let data = JSON.parse(event.data);
        toastr.success(data.id + ': ' + data.message, 'Live Tracking', {timeOut: 5000});
        console.log(data.id + ': ' + data.message, 'Live Tracking')
        get_lt_status();
      }, false);

      es.addEventListener('reload', function(event) {
        clear_flashed_messages();
        populate_track_admin(taskid);
        update_track_pilot_stats();
      }, false);

      es.addEventListener('page_reload', function(event) {
        clear_flashed_messages();
        create_flashed_message('Process completed successfully', 'success');
        populate_track_admin(taskid);
        update_track_pilot_stats();
//        window.location.reload(true);
      }, false);
    }
  }

  if (production == true) {
      var es = null;
      initES();
  }
});
