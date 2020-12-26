var registered;
var non_registered;
var registered_pil=[];
var new_registered_pil = [];
var un_registered_pil=[];
var num_internal_pilots = 0;
var IDs = [];

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
  cleanup_modal('mod_modal')
  let table = $('#pilots').DataTable();
  let row = '#id_'+par_id;
  let data = table.row( row ).data();
  let paid = 0
  if (data['paid'] == 'Y') paid = 1;
  console.log('par_id='+data['par_id']);
  $('#mod_par_id').val('').val(data['par_id']);
  $('#mod_original_id_number').val('').val(data['ID']);
  $('#mod_last_id_number').val('').val(data['ID']);
  $('#mod_id_number').val(data['ID']);

  $('#mod_civl').val(data['civl_id']);
  $('#mod_name').val(data['name']);
  $('#mod_sex').val(data['sex']);
  $('#mod_nat').val(data['nat']);
  $('#mod_glider').val(data['glider']);
  $('#mod_certification').val(data['glider_cert']);
  $('#mod_sponsor').val(data['sponsor']);
  $('#mod_status').val(data['status']);
  $('#mod_paid').val(paid);
  $('#modify_confirmed').attr("onclick","save_modified_participant('"+ par_id +"')");

  $('#mod_nat_team').prop("checked", isNotEmpty(data['nat_team']) );
  $('#mod_team').val(data['team'])
  $('#mod_xcontest_id').val(data['xcontest_id'])
  $('#mod_live_id').val(data['live_id'])

  $('#mod_modal').modal('show');
}

$('#participant_form').submit( function (e) {
  e.preventDefault(); // block the traditional submission of the form.
  $('#mod_modal .modal-errors').empty();  // delete all previous errors
  let mydata = $('#participant_form').serialize();
  let parid = $('#mod_par_id').val()
  let url = "/users/_add_participant/"+ compid;
  if ( parid ) url = "/users/_modify_participant_details/"+parid;
  $.ajax({
    type: "POST",
    url: url,
    data: mydata, // serializes the form's elements.
    success: function (response) {
      // console.log(response);  // display the returned data in the console.
      if (response.success) {
        populate_registered_pilot_details(compid);
        $('#mod_modal').modal('toggle');
        let message = 'Pilot successfully registered.';
        if ( parid ) message = 'Pilot successfully updated.';
        create_flashed_message(message, 'info');
      }
      else {
        if (response.errors) {
          let keys = Object.keys(response.errors);
          console.log('Error! ('+keys.length+')');
          keys.forEach( key => {
            let text = response.errors[key][0];
            $('#mod_modal-body div').find("[name='"+key+"']").css('background-color', 'orange');
            let message = document.createElement( "p" );
            message.classList.add('alert', 'alert-danger');
            message.innerText = key + ': ' + text;
            $('#mod_modal .modal-errors').append(message);
          })
        }
      }
    }
  });
});

function cleanup_modal (modal) {
  let body = modal + '-body';
  let names = ['CIVL', 'name', 'glider', 'certification', 'sponsor', 'live_id', 'xcontest_id', 'team'];
  $('#'+modal+' .modal-errors').empty();  // delete all previous errors
  $('#'+body+' [name]').each( function( i, el ) {
    if ( names.includes($(el).attr('name')) ) $(el).val('');
    $(el).removeAttr('style');
  });
}

function add_participant() {
  cleanup_modal('mod_modal');
  $('#mod_par_id').val('');
  let id = assign_id();
  $('#mod_original_id_number').val(id);
  $('#mod_last_id_number').val(id);
  $('#mod_id_number').val(id);

  $('#mod_modal').modal('show');
}

function check_id_number(input, orig, last) {
  let modified = parseInt(input.val()); // value given in input
  let original = parseInt(orig.val());  // original value
  let valid = parseInt(last.val());     // last valid value in input
  let ids_list = IDs.filter(item => item != original);

  if( (modified != original && ids_list.includes(modified)) || !modified || modified < 1 ) {
    // console.log('value already exists or is invalid');
    input.val(valid);
  }
  else {
    // console.log('value is ok');
    last.val(modified);
  }
}

function assign_id() {
  let id = 101;
  while ( IDs.includes(id) ) id ++;
  return id;
}

function populate_registered_pilot_details(compid, readonly=false){
  $.ajax({
    type: "GET",
    url: '/_get_participants/' + compid,
    contentType:"application/json",
    dataType: "json",
    success: function (json) {
      var columns = [
          {data: 'par_id', title: 'par_id', name: 'par_id', visible: false, searchable: false, defaultContent: ''},
          {data: 'ID', title:'#', name: 'ID', width: '1rem', className: "text-right", defaultContent: ''},
          {data: 'civl_id', title:'CIVLID', width: '1.5rem', className: "text-right", defaultContent: ''},
          {data: 'name', title:'Pilot', width: '350px', render: function ( data, type, row ) { let span = '<span>'; if (row.sex == 'F'){span='<span class="sex-F">'}; return span + data + '</span>'}},
          {data: 'sex', title:'Sex', name:'sex', visible: false, defaultContent: ''},
          {data: 'nat', title:'NAT', width: '1.2rem', name:'nat', defaultContent: ''},
          {data: 'glider', title: "Glider", width: '200px', defaultContent: ''},
          {data: 'glider_cert', title: "Cert.", width: '1rem', defaultContent: ''},
          {data: 'sponsor', title: "Sponsor", width: '250px', defaultContent: ''},
          {data: 'team', title: "Team", name: 'team', width: '4rem', visible: false, searchable: false, defaultContent: ''},
          {data: 'nat_team', title: "Nat team", name: 'nat_team', width: '1rem', visible: false, searchable: false, defaultContent: ''},
          {data: 'status', title: "Status", width: '2rem', defaultContent: ''},
          {data: 'paid', title: "Paid", width: '1rem', defaultContent: ''},
          {data: 'xcontest_id', title: 'XContest ID', name: 'xcontest_id', width: '2rem', visible: false, defaultContent: ''},
          {data: 'live_id', title: 'Live ID', name: 'live_id', width: '2.5rem', visible: false, defaultContent: ''}
      ];
      if (!external_comp) {
        columns.push({data: 'pil_id', title: "Source", render: function ( data ) { if (data){ return 'internal' } else { return 'external'}}});
        columns.push({data: 'par_id', orderable: false, searchable: false, render: function ( data ) { return '<td  class ="value" ><button type="button" class="btn btn-primary" onclick="edit_participant(' +  data + ')" data-toggle="confirmation" data-popout="true">Edit</button></td>'}});
        columns.push({data: 'par_id', orderable: false, searchable: false, render: function ( data ) { return '<td  class ="value" ><button type="button" class="btn btn-danger" onclick="remove_participant(' +  data + ')" data-toggle="confirmation" data-popout="true">Remove</button></td>'}});
      }

      $('#pilots').DataTable({
        data: json.data,
        destroy: true,
        paging: false,
        responsive: true,
        saveState: true,
        info: false,
        bAutoWidth: false,
        searching: true,
        filter: true,
        dom: '<"#search"f>rt<"bottom"lip><"clear">',
        columns: columns,
        rowId: function(data) {
          return 'id_' + data.par_id;
        },
        initComplete: function(data) {
            $('#total_pilots').text('Total pilots registered: ' + json.data.length );
            if(json.data.length > 0){ $('#download_section').show(); } else { $('#download_section').hide(); }
            $('#total_external_pilots').text(json.external);
            $('#delete_external').hide();
            if(json.external > 0){ $('#delete_external').show(); }
            // list of pilots IDs
            let table = $('#pilots').DataTable();
            IDs = table
                  .columns( 1 )
                  .data()
                  .eq( 0 )          // Reduce the 2D array into a 1D array of data
                  .sort()           // Sort data alphabetically
                  .unique()         // Reduce to unique values
                  .toArray()        // obj to Array
                  .filter(Boolean); // removes null, NaN, undifined

            // Team Section
            if(json.teams.country_scoring){
                $('#pilots').DataTable().column('nat_team:name').visible( true );
                $.get( '/users/_check_nat_team_size/' + compid, function( data ) {
                $( "#team_messages" ).html( data.message )}, "json" );
                $('#add_nat_team_section').show();
                $('#mod_nat_team_section').show();
            }
            if(json.teams.team_scoring){
                $('#pilots').DataTable().column('team:name').visible( true );
                $.get( '/users/_check_team_size/' + compid, function( data ) {
                $( "#team_messages" ).html( data.message )}, "json" );
                $('#add_team_section').show();
                $('#mod_team_section').show();
            }
            if ( json.teams.team_scoring || json.teams.country_scoring ) $('#add_all_team_section').show(); else $('#add_all_team_section').hide();

            // Track Source Section
            if(track_source){
                if(track_source == 'xcontest'){
                    $('#pilots').DataTable().column('xcontest_id:name').visible( true );
                    $('#add_xcontest_section').show();
                    $('#add_flymaster_section').hide();
                    $('#mod_xcontest_section').show();
                    $('#mod_flymaster_section').hide();
                }
                else if(track_source == 'flymaster'){
                    $('#pilots').DataTable().column('live_id:name').visible( true );
                    $('#add_flymaster_section').show();
                    $('#add_xcontest_section').hide();
                    $('#mod_flymaster_section').show();
                    $('#mod_xcontest_section').hide();
                }
                $('#add_track_source_section').show();
                $('#mod_track_source_section').show();
            }
            else {
                $('#add_track_source_section').hide();
                $('#mod_track_source_section').hide();
            }
        }
      });
    }
  });
}

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

  $('#upload_fsdb_button').click(function(){
    $('#FSDB_fileupload').click();
  });

  $('#mod_id_number').on("change", function(){
    check_id_number($('#mod_id_number'), $('#mod_original_id_number'), $('#mod_last_id_number'));
  });

  $('#add_id_number').on("change", function(){
    check_id_number($('#add_id_number'), $('#add_original_id_number'), $('#add_last_id_number'));
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
