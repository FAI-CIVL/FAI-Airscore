function populate_task_scores(taskid, filename){
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
            {data: 'altbonus', title:'altbonus', id:'altbonus'},
            {data: 'distance', title:'Kms'},
            {data: 'speedP', title:'Spd'},
            {data: 'leadP', title:'LO p', id:'leading'},
            {data: 'arrivalP', title:'Arv'},
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
            else{ return ("");}

            }},

            {
            targets: [-1],  render: function (a, b, data, d) {
                return ('<td  class ="value" ><button type="button" class="btn btn-primary" onclick="adjust('
                   +  data.par_id + ')" data-toggle="confirmation" data-popout="true">Edit</button></td>');

            }}
        ],

        "language": {
            "emptyTable":     "Error: result file not found"
        },
        "initComplete": function(settings, json) {
            score_data = json;
                $.each( json.stats, function( key, value ) {
                $('#taskinfo tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
            });
        }
    });
    console.log("location.href='/users/_download/task_html/"+filename+"'")
    if ( filename == null ) {
        document.getElementById('download_task_html').style.display = "none";
    }
    else {
        document.getElementById('download_task_html').style.display = "block";
        document.getElementById('download_task_html').setAttribute( "onClick", "location.href='/users/_download/task_html/"+filename+"'" );
    }
}

function update_publish_button(filename) {
  if (filename == active_file) {
    $('#publish').text('Un-Publish results');
    $('#publish').addClass('btn-danger').removeClass('btn-success');
  }
  else {
    $('#publish').text('Publish results');
    $('#publish').addClass('btn-success').removeClass('btn-danger');
  }
}

function toggle_publish() {
  var mydata = new Object();
  mydata.filetext = $('#result_file option:selected').text();
  mydata.filename = $('#result_file option:selected').val();
  var url = ''
  if (mydata.filename == active_file) {
    url = url_unpublish_result;
  }
  else {
    url = url_publish_result;
  }

  $.ajax({
    type: "POST",
    url: url,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      active_file = response.filename
      update_publish_button(mydata.filename);
      $('#task_result_header').text(response.header)
    }
  });
}


function updateFiles(load_latest=false) {
  var mydata = new Object();
  mydata.offset = new Date().getTimezoneOffset();
  dropdown.file.attr('disabled', 'disabled');
  dropdown.file.empty();
  $.ajax({
    type: "POST",
    url: url_get_task_result_files,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      $('#task_result_header').text(response.header)
      $('#comp_header').text(response.comp_header)
      if (response.display_comp_unpublish) {
          $('#comp_unpublish').show();
      }
      else {
        $('#comp_unpublish').hide();
      }
      response.choices.forEach(function(item) {
        dropdown.file.append(
          $('<option>', {
            value: item[0],
            text: item[1]
          })
        );
      });
      dropdown.file.removeAttr('disabled');
      if(response.active){
        active_file = response.active;
        $("#result_file").val(response.active);
      }
      if(load_latest){
        $("#result_file").val($("#result_file option:first").val());
      }
      var filename = $('#result_file option:selected').val();
      update_publish_button(filename);
      var status = $('#result_file option:selected').text().split(' - ')[1];
      $('#status_modal_comment').val(status);
      populate_task_scores(taskid, filename);
    }
  });
}

function Score_modal() {
  $('#scoremodal').modal('show');
}

function open_status_modal() {
  $('#statusmodal').modal('show');
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
      if (response.redirect) {
        window.location.href = response.redirect;
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
      if (production == false) {
        $('#fullscoremodal').modal('hide');
      }
    }
  });
}

function change_status() {
var mydata = new Object();
  mydata.status = $('#status_modal_comment').val();
  mydata.filename = $('#result_file option:selected').val();
  $.ajax({
    type: "POST",
    url: url_change_result_status,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      if (response.success) {
        updateFiles();
        $('#statusmodal').modal('hide');
      }
    }
  });
}

function comp_publish() {
  var mydata = new Object();
  mydata.offset = new Date().getTimezoneOffset();
  $('#comp_publish').hide();
  $('#comp_publish_spinner').html('<div class="spinner-border" role="status"><span class="sr-only">Scoring...</span></div>');
  $.ajax({
    type: "POST",
    url:  url_publish_comp_result,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      $('#comp_header').text(response.comp_header)
      $('#comp_unpublish').show();
      $('#comp_publish_spinner').html('')
      $('#comp_publish').show();
    }
  });
}

function comp_unpublish() {
  var mydata = new Object();
  mydata.offset = new Date().getTimezoneOffset();
  $.ajax({
    type: "POST",
    url:  url_unpublish_comp_result,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      $('#comp_header').text(response.comp_header)
      $('#comp_unpublish').hide();
    }
  });
}

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
  mydata.filename = $('#result_file option:selected').val();
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
        $('#comp_header').text(response.comp_header)
        populate_task_scores(taskid, mydata.filename);
        $('#editmodal').modal('hide');
      }
    });
  }
}

var score_data = new Object();
var active_file = '';
table_data = [];

// jQuery selection for the file select box
var dropdown = {
  file: $('#result_file')
};

$(document).ready(function() {

  updateFiles();

  // Event listener to the file picker to redraw on input
  $('#result_file').change(function() {
    var filename = $('#result_file option:selected').val();
    var status = $('#result_file option:selected').text().split(' - ')[1];
    update_publish_button(filename);
    populate_task_scores(taskid, filename);
    $('#status_modal_comment').val(status);
  });

  populate_task_scores(taskid,active_file);

  if (production == true) {
    var es = null;
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
          var filename = $('#result_file option:selected').val();
          populate_task_scores(taskid, filename);
        }, false);

        es.addEventListener('reload_select_latest', function(event) {
          updateFiles(load_latest=true);
        }, false);

      }
    }
  initES();
  }
});
