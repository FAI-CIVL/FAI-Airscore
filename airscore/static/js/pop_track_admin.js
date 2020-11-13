function populate_track_admin(task_id){
    $('#tracks').DataTable({
        destroy: true,
        ajax: '/users/_get_tracks_admin/'+task_id,
        paging: true,
        order: [[ 1, 'desc' ]],
        lengthMenu: [60, 150 ],
        searching: true,
        info: false,
        columns: [
            {data: 'ID', name:'ID'},
            {data: 'name', name:'Name'},
            {data: 'Result', name:'Result'},
            {data: null}],
              rowId: function(data) {
                return 'id_' + data.par_id;
                },
        columnDefs:[{
            targets: [-1],  render: function (a, b, data, d) {
            if(data['Result']=='Not Yet Processed' | data['Result'].indexOf("G record") >= 0){
            var buttons;
            buttons =
             '<button id="ABS' + data.par_id  +'" class="btn btn-primary mt-3" type="button" onclick="set_result(' + data.par_id +',\'abs\')">Set ABS</button> '
             +'<button id="MD' + data.par_id  +'" class="btn btn-primary mt-3" type="button" onclick="set_result(' + data.par_id +',\'mindist\')">Set Min Dist</button> '
             +'<button id="DNF' + data.par_id  +'" class="btn btn-primary mt-3" type="button" onclick="set_result(' + data.par_id +',\'dnf\')">Set DNF</button> '
             +'<button id="TrackUp' + data.par_id  +'" class="btnupload btn btn-primary mt-3" onclick="choose_file(' + data.par_id +');">Upload Track</button>'
//             +'<button id="TrackUp_overide_check' + data.par_id  +'" class="hideatstart btnupload btn btn-warning mt-3" onclick="choose_file(' + data.par_id +', false, true);">Upload Track - Overide quality check</button>'
             +'<div class = "hideatstart"  id="progress_percentage'+ data.par_id+ '" ><p id="progress_percentage _text'+data.par_id +'"></p></div>'
             +' <div id="filediv' + data.par_id  +'" class = "hideatstart" > <input id="fileupload' + data.par_id +'" type="file" size="chars" class="custom-file-input"  oninput="filesize(this);" data-url="/users/_upload_track/'+ task_id + '/' + data.par_id + '" name="tracklog" >'
             + ' <div id="filediv' + data.par_id  +'" class = "hideatstart" > <input id="fileupload_NO_G' + data.par_id +'" type="file" size="chars" class="custom-file-input"  oninput="filesize(this);" data-url="/users/_upload_track/'+ task_id + '/' + data.par_id + '" name="tracklog_NO_G" >'
             + ' <div id="filediv' + data.par_id  +'" class = "hideatstart" > <input id="fileupload_NO_V' + data.par_id +'" type="file" size="chars" class="custom-file-input"  oninput="filesize(this);" data-url="/users/_upload_track/'+ task_id + '/' + data.par_id + '" name="tracklog_NO_V" >'
//             +'<div id="progress'+ data.par_id+ '" ><div class="bar" style="width: 0%;"><p id="spinner'+ data.par_id + '"></p><p id="progress_text'+data.par_id +'"></p></div></div>'
             +'</div>'

             ;
             return buttons;
            }
            else if (data['Result']=='Processing..') {
            return data['file']
                        }

           else{ return '<button class="btn btn-danger mt-3" type="button" onclick="delete_track('+ data.track_id +','+ data.par_id +')">Delete Track</button> ';}

        }                 }],
        initComplete: function() {
             $(".hideatstart").hide();},
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
    var table = $('#tracks').dataTable();
    new_data.ID = $('#tracks').DataTable().row( $('tr#id_'+ new_data.par_id)).data()['ID'];
    new_data.name = $('#tracks').DataTable().row( $('tr#id_'+ new_data.par_id)).data()['name'];
    table.fnUpdate(new_data, $('tr#id_'+ new_data.par_id), undefined, false);
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
            update_track_pilot_stats();
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
  var mydata = new Object();
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
      update_track_pilot_stats();
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
  document.getElementById("xcontest_button").innerHTML = "Getting Tracks...";
  document.getElementById("xcontest_button").className = "btn btn-warning ml-4";
  $.ajax({
    type: "POST",
    url: url_get_xcontest_tracks,
    contentType:"application/json",
    dataType: "json",
    success: function () {
      if (production == false){
        populate_track_admin(taskid);
        update_track_pilot_stats();
      }
      document.getElementById("xcontest_button").innerHTML = "Xcontest";
      document.getElementById("xcontest_button").className = "btn btn-primary ml-4";
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
      $('#zip_modal_message').hide();
      $('#zip_progress').show();
      $('#zip_spinner').show();
      $('#zip_progress_text').text(data.files[0].name + ' - processing');
      $('#zip_spinner').html('<div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div>');
    },
    success: function () {
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
    }
  });
  $('#bulk_fileupload').click();
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
      $('#progress_percentage'+ par_id).show();
      $('#progress_percentage'+ par_id).text('uploading..');
      $('#filediv'+ par_id).show();
    },
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
      if(response.error){
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
      $('#progress'+ par_id+' .bar').css(
        'width',
        progress + '%'
      );
    }
  });
  $('#fileupload' + par_id).click();
};

function choose_file(par_id) {
    if (production == true) choose_file_prod(par_id); else choose_file_test(par_id);
}

$(document).ready(function(){
    populate_track_admin(taskid);
    update_track_pilot_stats();
    console.log('production='+production);

    function initES() {
      if (es == null || es.readyState == 2) { // this is probably not necessary.
        es = new EventSource(url_sse_stream);
        es.onerror = function(e) {
          if (es.readyState == 2) {
            setTimeout(initES, 5000);
          }
        };
        es.addEventListener('% complete', function(event) {
          var data = JSON.parse(event.data);
          $('#progress_percentage'+ data.id).text(data.message + ' % complete');
        }, false);
        es.addEventListener('counter', function(event) {
          var data = JSON.parse(event.data);
          $('#ProcessModalTitle').text('Tracklog Processing. ' + data.message);
        }, false);
        es.addEventListener('info', function(event) {
          var data = JSON.parse(event.data);
          $('#process_text').append(data.message + "<br/>");
        }, false);
        es.addEventListener('open_modal', function(event) {
          $('#log_button').show();
          $('#ProcessModal').modal('show');
        }, false);
        es.addEventListener('result', function(event) {
          var data = JSON.parse(event.data);
          if(data.message == 'error'){
            $('#ABS'+ data.id).show();
            $('#MD'+ data.id).show();
            $('#DNF'+ data.id).show();
            $('#TrackUp'+ data.id).show();
            $('#upload_box'+ data.id).show();
            $('#filediv'+ data.id).hide();
            $.alert(response.error,{
              type: 'danger',
              position: ['center', [-0.42, 0]],
              autoClose: false
            });
            update_track_pilot_stats();
          }
          else {
            update_row($.parseJSON(data.message));
          }
        }, false);
        es.addEventListener('valid_fail', function(event) {
          var data = JSON.parse(event.data);
          data.message = JSON.parse(data.message);
          $('#ABS'+ data.id).show();
          $('#MD'+ data.id).show();
          $('#DNF'+ data.id).show();
          $('#TrackUp'+ data.id).show();
          $('#upload_box'+ data.id).show();
          $('#filediv'+ data.id).hide();
          $('#progress_percentage'+ data.id).hide();
          data.message.Result = '<button id="TrackUp_noV' + data.id  +'" class="btnupload btn btn-warning mt-3" onclick="choose_file(' + data.id +', false, true);">Upload IGC ignoring quality check & G record</button>'
          update_row(data.message);
        }, false);
        es.addEventListener('g_record_fail', function(event) {
          var data = JSON.parse(event.data);
          data.message = JSON.parse(data.message);
          $('#ABS'+ data.id).show();
          $('#MD'+ data.id).show();
          $('#DNF'+ data.id).show();
          $('#TrackUp'+ data.id).show();
          $('#upload_box'+ data.id).show();
          $('#filediv'+ data.id).hide();
          $('#progress_percentage'+ data.id).hide();
          data.message.Result = '<button id="TrackUp_noG' + data.id  +'" class="btnupload btn btn-warning mt-3" onclick="choose_file(' + data.id +', true);">Upload IGC ignoring G record</button>'
          update_row(data.message);
        }, false);
        es.addEventListener('reload', function(event) {
          populate_track_admin(taskid);
          update_track_pilot_stats();
        }, false);
      }
    }

    if (production == true) {
        var es = null;
        initES();
    }
});
