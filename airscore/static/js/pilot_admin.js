var registered;
var non_registered;
var registered_pil=[];
var new_registered_pil = [];
var un_registered_pil=[];
var num_internal_pilots = 0;

function get_team_size_messages() {
  let table = $('#pilots').DataTable();
  if (table.column('team:name').visible()) {
    $.get( check_team_size_url, function( data ) {
      $( "#team_messages" )
      .html( data.message )
    }, "json" );
  }
  if (table.column('nat_team:name').visible()) {
    $.get( check_nat_team_size_url, function( data ) {
      $( "#team_messages" )
      .html( data.message )
    }, "json" );
  }
};

function update_pilot_count(){
  num_internal_pilots = $('#lstview_to option').length;
  $('#registered').text('Registered internal pilots: ' + num_internal_pilots);
    new_registered =[];
  $("#lstview_to option").each(function() {
    new_registered.push(parseInt($(this).val(),10));
  });
  new_registered_pil = new_registered.filter( el => !registered_pil.includes( el ) );
  un_registered_pil = registered_pil.filter( el => !new_registered.includes( el ) );
}

function get_internal_pilots() {
  $('#lstview').empty();
  $('#lstview_to').empty();
  $.getJSON(get_non_and_registered_pilots_internal_url,function(data) {
    registered = data.registered_pilots
    non_registered = data.non_registered_pilots
    if (non_registered){
        non_registered.forEach(function(item) {
          $('#lstview').append(
            $('<option>', {
              value: item.pil_id,
              text: item.first_name + ' ' + item.last_name + ' - ' + item.civl_id
            })
          );
        });
    }
    if (registered){
        registered.forEach(function(item) {
          $('#lstview_to').append(
            $('<option>', {
               value: item.pil_id,
               text: item.name + ' - ' + item.civl_id
            })
          );
          registered_pil.push(item.pil_id);
        });
    }
    update_pilot_count();
  });
}

$(function() {
  // event listener to pilot list change
  $('#lstview_to, #lstview_undo, #lstview_rightAll, #lstview_rightSelected, #lstview_leftSelected, #lstview_leftAll, #lstview_redo').on('click', function() {
        update_pilot_count();
  });
});

function register_pilots() {
  var mydata = new Object();
  mydata.register = new_registered_pil;
  mydata.unregister = un_registered_pil;
  $.ajax({
    type: "POST",
    url: register_pilots_url,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function () {
      if (pilotdb) get_internal_pilots();
      populate_registered_pilot_details(compid);
    }
  });
};

function unregister_all_external() {
  $.ajax({
    type: "POST",
    url: unregister_all_external_participants_url,
    dataType: "json",
    success: function () {
      populate_registered_pilot_details(compid);
    }
  });
}

function remove_participant(par_id) {
  var mydata = new Object();
  mydata.participant = par_id;
  $.ajax({
    type: "POST",
    url: unregister_participant_url,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function () {
      populate_registered_pilot_details(compid);
    }
  });
};

function isNotEmpty( el ) {
  return el != null && el != String.Empty
}

function edit_participant(par_id) {
  let table = $('#pilots').DataTable();
  let row = '#id_'+par_id;
  let data = table.row( row ).data();
  let paid = 0
  if (data['paid'] == 'Y') paid = 1;
  console.log('par_id='+data['par_id']);
  var team = 0;
  var nat_team = 0;
  if (table.column('team:name').visible()) {
    team = 1;
  }
  if (table.column('nat_team:name').visible()) {
    nat_team = 1;
  }
  console.log('team='+team+', '+nat_team);
  $('#mod_id_number').val(data['ID']).change();
  $('#mod_civl').val(data['civl_id']).change();
  $('#mod_name').val(data['name']).change();
  $('#mod_sex').val(data['sex']).change();
  $('#mod_nat').val(data['nat']).change();
  $('#mod_glider').val(data['glider']).change();
  $('#mod_certification').val(data['glider_cert']).change();
  $('#mod_sponsor').val(data['sponsor']).change();
  $('#mod_status').val(data['status']).change();
  $('#mod_paid').val(paid).change();
  $('#modify_confirmed').attr("onclick","save_modified_participant('"+ par_id +"')");

  // Team Sections
  if (nat_team) {
    $('#mod_nat_team').prop("checked", isNotEmpty(data['nat_team']) );
    $('#mod_nat_team_section').show();
  }
  else {$('#mod_nat_team_section').hide(); }

  if (team) {
      $('#mod_team').val(data['team']).change();
      $('#mod_team_section').show();
  }
  else {$('#mod_team_section').hide(); }

  if ( team || nat_team ) $('#mod_all_team_section').show(); else $('#mod_all_team_section').hide();

  // Track Sources Section
  if(track_source){
    if(track_source == 'xcontest'){
        $('#mod_xcontest_id').val(data['xcontest_id']).change();
        $('#mod_xcontest_section').show();
        $('#mod_flymaster_section').hide();
    }
    else if(track_source == 'flymaster'){
        $('#mod_live_id').val(data['live_id']).change();
        $('#mod_flymaster_section').show();
        $('#mod_xcontest_section').hide();
    }
    $('#mod_track_source_section').show();
  }
  else {
    $('#mod_track_source_section').hide();
  }

  $('#edit_par_modal').modal('show');
}

function save_modified_participant(par_id) {
  var mydata = new Object();
  mydata.id_num = $('#mod_id_number').val();
  mydata.name = $('#mod_name').val();
  mydata.sex = $('#mod_sex').val();
  mydata.nat = $('#mod_nat').val();
  mydata.glider = $('#mod_glider').val();
  mydata.certification = $('#mod_certification').val();
  mydata.sponsor = $('#mod_sponsor').val();
  mydata.status = $('#mod_status').val();
  mydata.paid = $('#mod_paid').val();
  mydata.CIVL = $('#mod_civl').val();
  mydata.team = $('#mod_team').val();
  mydata.nat_team = $('#mod_nat_team').is(':checked');
  mydata.live_id = $('#mod_live_id').val();
  mydata.xcontest_id = $('#mod_xcontest_id').val();

  $.ajax({
    type: "POST",
    url: "/users/_modify_participant_details/"+par_id,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function (data) {
      populate_registered_pilot_details(compid);
    }
  });
};

function save_new_participant(){
  var mydata = new Object();
  mydata.id_num = $('#add_id_number').val();
  mydata.name = $('#add_name').val();
  mydata.sex = $('#add_sex').val();
  mydata.nat = $('#add_nat').val();
  mydata.glider = $('#add_glider').val();
  mydata.certification = $('#add_certification').val();
  mydata.sponsor = $('#add_sponsor').val();
  mydata.status = $('#add_status').val();
  mydata.paid = $('#add_paid').val();
  mydata.CIVL = $('#add_civl').val();
  mydata.team = $('#add_team').val();
  mydata.nat_team = $('#add_nat_team').is(':checked');
  mydata.live_id = $('#add_live_id').val();
  mydata.xcontest_id = $('#add_xcontest_id').val();

  $.ajax({
    type: "POST",
    url: "/users/_add_participant/"+ compid,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function () {
      $('#add_modal').hide();
      populate_registered_pilot_details(compid);
    }
  });
};

jQuery(document).ready(function($) {
    $('#delete_external').hide();
    $('#add_nat_team_section').hide();
    $('#add_team_section').hide();
    $('#download_section').hide();
    $('#lstview').multiselect({
      search: {
        left: '<input type="text" name="q" class="form-control" placeholder="Search..." />',
        right: '<input type="text" name="q" class="form-control" placeholder="Search..." />',
      }
    });
    if (pilotdb) get_internal_pilots();
    populate_registered_pilot_details(compid, external_comp);

    // listeners
    $('#upload_excel_button').click(function() {
      $('#Excel_fileupload').click();
    });

    $('#FSDB_button').click(function(){
      $('#FSDB_fileupload').click();
    });

    $(function () {
      $('#Excel_fileupload').fileupload({
        dataType: 'json',
        done: function (e, data) {
          $.each(data.result.files, function (index, file) {
              $('<p/>').text(file.name).appendTo(document.body);
          });
        },
        submit: function (e, data){
          console.log('submit...');
          document.getElementById("Excel_button").innerHTML = "Processing...";
          document.getElementById("Excel_button").className = "btn btn-warning ml-4";
        },
        success: function () {
          console.log('success...');
          if (pilotdb) get_internal_pilots();
          populate_registered_pilot_details(compid);
          document.getElementById("Excel_button").innerHTML = "Done";
          document.getElementById("Excel_button").className = "btn btn-success ml-4";
        },
        fail: function () {
          console.log('fail...');
          document.getElementById("Excel_button").innerHTML = "Failed";
          document.getElementById("Excel_button").className = "btn btn-danger ml-4";
        },
        complete: function () {
          console.log('complete...');
          setTimeout(function(){
            document.getElementById("Excel_button").innerHTML = "Upload Excel File";
            document.getElementById("Excel_button").className = "btn btn-success ml-4";
          }, 3000);
        }
      });
    });

    $(function () {
      $('#FSDB_fileupload').fileupload({
        dataType: 'json',
        done: function (e, data) {
            $.each(data.result.files, function (index, file) {
                $('<p/>').text(file.name).appendTo(document.body);
            });
        },
        submit: function (e, data){
          document.getElementById("FSDB_button").innerHTML = "Processing...";
          document.getElementById("FSDB_button").className = "btn btn-warning ml-4";
        },
        success: function () {
          if (pilotdb) get_internal_pilots();
          populate_registered_pilot_details(compid);
          document.getElementById("FSDB_button").innerHTML = "Done";
          document.getElementById("FSDB_button").className = "btn btn-success ml-4";
        },
        fail: function () {
          console.log('fail...');
          document.getElementById("FSDB_button").innerHTML = "Failed";
          document.getElementById("FSDB_button").className = "btn btn-danger ml-4";
        },
        complete: function () {
          setTimeout(function(){
            document.getElementById("FSDB_button").innerHTML = "Upload FSDB File";
            document.getElementById("FSDB_button").className = "btn btn-success ml-4";
          }, 3000);
        }
      });
    });
});
