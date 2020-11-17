function populate_registered_pilot_details(compid){
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
          {data: 'live_id', title: 'Live ID', name: 'live_id', width: '2.5rem', visible: false, defaultContent: ''},
          {data: 'pil_id', title: "Source", render: function ( data ) { if (data){ return 'internal' } else { return 'external'}}},
          {data: 'par_id', orderable: false, searchable: false, render: function ( data ) { return '<td  class ="value" ><button type="button" class="btn btn-primary" onclick="edit_participant(' +  data + ')" data-toggle="confirmation" data-popout="true">Edit</button></td>'}},
          {data: 'par_id', orderable: false, searchable: false, render: function ( data ) { return '<td  class ="value" ><button type="button" class="btn btn-danger" onclick="remove_participant(' +  data + ')" data-toggle="confirmation" data-popout="true">Remove</button></td>'}}
      ];

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
            if(json.external > 0){ $('#delete_external').show();}

            // Team Section
            if(json.teams.country_scoring){
                $('#pilots').DataTable().column('nat_team:name').visible( true );
                $.get( '/users/_check_nat_team_size/' + compid, function( data ) {
                $( "#team_messages" ).html( data.message )}, "json" );
                $('#add_nat_team_section').show();
            }
            if(json.teams.team_scoring){
                $('#pilots').DataTable().column('team:name').visible( true );
                $.get( '/users/_check_team_size/' + compid, function( data ) {
                $( "#team_messages" ).html( data.message )}, "json" );
                $('#add_team_section').show();
            }
            if ( json.teams.team_scoring || json.teams.country_scoring ) $('#add_all_team_section').show(); else $('#add_all_team_section').hide();

            // Track Source Section
            if(track_source){
                if(track_source == 'xcontest'){
                    $('#pilots').DataTable().column('xcontest_id:name').visible( true );
                    $('#add_xcontest_section').show();
                    $('#add_flymaster_section').hide();
                }
                else if(track_source == 'flymaster'){
                    $('#pilots').DataTable().column('live_id:name').visible( true );
                    $('#add_flymaster_section').show();
                    $('#add_xcontest_section').hide();
                }
                $('#add_track_source_section').show();
            }
            else {
                $('#add_track_source_section').hide();
            }
        }
      });
    }
  });
}