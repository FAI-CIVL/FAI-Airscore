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
    success: function ( response ) {
      if (response.success) {
//        let message = 'Participants successfully deleted.';
//        create_flashed_message(message, 'warning');
        window.location.reload();
      }
      else {
        if (response.error) {
          let message = 'There was an error removing participants.';
          create_flashed_message(message, 'danger');
          populate_registered_pilot_details(compid, external_comp);
        }
      }
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
  return el != null || el != String.Empty
}

function edit_participant(par_id) {
  cleanup_modal('mod_modal');
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
  $('#mod_birthdate').val(moment(data['birthdate']).format('YYYY-MM-DD'));
  $('#mod_sex').val(data['sex']);
  $('#mod_nat').val(data['nat']);
  $('#mod_glider').val(data['glider']);
  $('#mod_certification').val(data['glider_cert']);
  $('#mod_sponsor').val(data['sponsor']);
  $('#mod_status').val(data['status']);
  $('#mod_paid').val(paid);
  $('#modify_confirmed').attr("onclick","save_modified_participant('"+ par_id +"')");

  $('#nat_team').prop("checked", isNotEmpty(data['nat_team']) );
  $('#mod_team').val(data['team'])
  $('#mod_xcontest_id').val(data['xcontest_id'])
  $('#mod_live_id').val(data['live_id'])
  $.each( data.custom, (key, value) => $('#attr_'+key).val(value) );

  $('#mod_modal').modal('show');
}

$('#nat_team').click(function(){
  $('#nat_team').val($('#nat_team').is(':checked'));
});

$('#participant_form').submit( function(e) {
  e.preventDefault(); // block the traditional submission of the form.
  $('#mod_modal .modal-errors').empty();  // delete all previous errors
  let mydata = $('#participant_form').serialize();
  let parid = $('#mod_par_id').val();
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
  let names = ['CIVL', 'name', 'birthdate', 'nat', 'glider', 'sponsor', 'live_id', 'xcontest_id', 'team', 'nat_team'];
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
        {data: 'birthdate', title:'Birthdate', name:'birthdate', visible: false, defaultContent: ''},
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
//      $.each(json.data[0].custom, (key, value) => columns.push({data: 'custom.'+key, title: attributes.find(x => x.attr_id == key).attr_name, name: 'attr_'+key} ));
      $.each(attributes, (idx, el) => columns.push({data: 'custom.'+el.attr_id, title: el.attr_value, name: 'attr_'+el.attr_id, defaultContent: ''} ));
      if (!external_comp) {
        if ( pilotdb ) {
          columns.push({data: 'pil_id', title: "Source", render: function ( data ) { if (data){ return 'internal' } else { return 'external'}}});
        }
        if ( is_editor ) {
          columns.push({data: 'par_id', orderable: false, searchable: false, render: function ( data ) { return '<td  class ="value" ><button type="button" class="btn btn-primary" onclick="edit_participant(' +  data + ')" data-toggle="confirmation" data-popout="true">Edit</button></td>'}});
          columns.push({data: 'par_id', orderable: false, searchable: false, render: function ( data ) { return '<td  class ="value" ><button type="button" class="btn btn-danger" onclick="remove_participant(' +  data + ')" data-toggle="confirmation" data-popout="true">Remove</button></td>'}});
        }
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

function populate_custom_attributes(compid, readonly=false){
    $.ajax({
    type: "GET",
    url: '/users/_get_custom_attributes/' + compid,
    contentType:"application/json",
    dataType: "json",
    success: function (json) {
      var columns = [
        {data: 'attr_id', title: 'id', name: 'attr_id', visible: false, searchable: false, defaultContent: ''},
        {data: 'attr_value', title:'Attribute', name: 'attr_value', defaultContent: ''}
      ];
      if (!readonly) {
        columns.push({data: 'attr_id', orderable: false, searchable: false, render: function ( data ) { return '<td  class ="value" ><button type="button" class="btn btn-primary" onclick="edit_attribute(' +  data + ');">Edit</button></td>'}});
        columns.push({data: 'attr_id', orderable: false, searchable: false, render: function ( data, type, row ) { if (row.used) return 'Attribute is used in Rankings'; else return '<td  class ="value" ><button type="button" class="btn btn-danger" onclick="remove_attribute(' +  data + ');">Remove</button></td>';}});
      }

      $('#attributes_table').DataTable({
        data: json,
        destroy: true,
        paging: false,
        responsive: true,
        saveState: true,
        info: false,
        bAutoWidth: false,
        searching: false,
        filter: false,
        columns: columns,
        rowId: function(data) {
          return 'id_' + data.attr_id;
        },
        initComplete: function(data) {
          if( json.length > 0 ) {
            $('#total_attributes').text( json.length + ' attributes.' );
            $('#attributes_table').show();
          }
          else {
            $('#total_attributes').text( 'No attributes' );
            $('#attributes_table').hide();
          }
        }
      });
    }
  });
}

function remove_attribute( attr_id ) {
  let data = get_row_info('#attributes_table', attr_id);
  $('#remove_attr_id').val('').val(attr_id);
  $('#delete_attr_name').text(data.attr_value);
  console.log('data='+ attr_id + ', '+$('#remove_attr_id').val());

//  $('#attribute_confirmed').attr("onclick",'confirm_remove_attribute('+attr_id+');');
  $('#remove-attribute_modal').modal('show');
}

function confirm_remove_attribute() {
  let attr_id = $('#remove_attr_id').val()
  let url = '/users/_remove_custom_attribute/' + attr_id;
  $.ajax({
    type: "POST",
    url: url,
    contentType:"application/json",
    success: function ( response ) {
      if (response.success){
//        populate_custom_attributes(compid, external_comp);
//        populate_registered_pilot_details(compid, external_comp);
//        create_flashed_message('Attribute successfully deleted.', 'warning');
        window.location.reload();
      }
      else {
        create_flashed_message('There was an error trying to delete attribute.', 'danger');
      }
   }
  });
}

function get_row_info(table_id, row_id) {
  let table = $(table_id).DataTable();
  let row = '#id_'+row_id;
  return table.row( row ).data();
}

function edit_attribute( attr_id ) {
  let data = get_row_info('#attributes_table', attr_id);
  console.log('data='+ attr_id);
  $('#attr_id').val(attr_id);
  $('#attr_value').val(data.attr_value);
  $('#attr_modal').modal('show');
}

function new_attribute() {
  $('#attr_id').val('');
  $('#attr_value').val('');
  $('#attr_modal').modal('show');
}

function save_custom_attribute() {
  let url = '/users/_add_custom_attribute/' + compid;
  let mydata = {};
  mydata.attr_value = $('#attr_value').val();
  if ( $('#attr_id').val() ) {
    mydata.attr_id = $('#attr_id').val();
    mydata.comp_id = compid;
    url = '/users/_edit_custom_attribute/' + mydata.attr_id;
  }
  $.ajax({
    type: "POST",
    url: url,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function ( response ) {
      if (response.success){
//        populate_custom_attributes(compid, external_comp);
//        populate_registered_pilot_details(compid, external_comp);
//        create_flashed_message('Attribute save.', 'info');
        window.location.reload();
      }
      else {
        create_flashed_message('There was an error trying to save attribute.', 'danger');
      }
   }
  });
}

$(document).ready(function() {
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
  populate_custom_attributes(compid, (external_comp || !is_editor));

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
        document.getElementById("Excel_button").innerHTML = "Processing...";
        document.getElementById("Excel_button").className = "btn btn-warning ml-4";
      },
      // Response received
      success: function (response) {
        if (response.success) {
          if (pilotdb) get_internal_pilots();
//          populate_registered_pilot_details(compid, external_comp);
          document.getElementById("Excel_button").innerHTML = "Done";
          document.getElementById("Excel_button").className = "btn btn-success ml-4";
//          create_flashed_message('Participants successfully imported from excel file.', 'info');
          window.location.reload();
        }
        else {
          create_flashed_message('There was an error trying to import participants from excel file.', 'danger');
          if (response.error) create_flashed_message(response.error, 'warning');
        }
      },
      // Response missing
      fail: function (e) {
        console.log('fail...');
        console.log(e);
        document.getElementById("Excel_button").innerHTML = "Failed";
        document.getElementById("Excel_button").className = "btn btn-danger ml-4";
        create_flashed_message('There was an error trying to import participants from excel file.', 'danger');
      },
      complete: function () {
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
      // Response received
      success: function (response) {
        console.log('success...');
        console.log(response);
        if (response.success){
          if (pilotdb) get_internal_pilots();
//          populate_registered_pilot_details(compid, external_comp);
          document.getElementById("FSDB_button").innerHTML = "Done";
          document.getElementById("FSDB_button").className = "btn btn-success ml-4";
//          create_flashed_message('Participants successfully imported from FSDB file.', 'info');
          window.location.reload();
        }
        else {
          create_flashed_message('There was an error trying to import participants from FSDB file.', 'danger');
          if (response.error) create_flashed_message(response.error, 'warning');
        }
      },
      // Response missing
      fail: function (e) {
        console.log('fail...');
        console.log(e);
        document.getElementById("FSDB_button").innerHTML = "Failed";
        document.getElementById("FSDB_button").className = "btn btn-danger ml-4";
        create_flashed_message('There was an error trying to import participants from FSDB file.', 'danger');
        if ( e.error ) create_flashed_message(e.error, 'warning');
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
