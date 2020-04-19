function populate_registered_pilot_details(compid){

    $('#pilots').dataTable({
        ajax: '/_get_participants/' + compid,
        info: true,
        paging: false,
        saveState: true,
        searching: true,
        filter: true,
        info: false,
        "dom": '<"#search"f>rt<"bottom"lip><"clear">',
        destroy: true,
        columns: [

             { data: 'ID', title: "#"},
             { data: 'name', title: "Pilot"},
             { data: 'sex', title: "Sex"},
             { data: 'nat', title: "Nat"},
             { data: 'glider', title: "Glider"},
             { data: 'glider_cert', title: "Certification"},
             { data: 'sponsor', title: "Sponsor"},
             { data: 'status', title: "Status"},
             { data: 'paid', title: "Paid"},
             { data: null, title: "Source"},
             { data: null},
             { data: null},
       ],

                     rowId: function(data) {
                return 'id_' + data.par_id;
                },
                 columnDefs:[{
            targets: [-2],  render: function (a, b, data, d) {

            return ('<td  class ="value" ><button type="button" class="btn btn-primary" onclick="edit_participant('
               +  data.par_id + ')" data-toggle="confirmation" data-popout="true">Edit</button></td>');
        }      }
  ,
             {
            targets: [-1],  render: function (a, b, data, d) {

            return ('<td  class ="value" ><button type="button" class="btn btn-danger" onclick="remove_participant('
               +  data.par_id + ')" data-toggle="confirmation" data-popout="true">Remove</button></td>');

        }},

                     {
            targets: [-3],  render: function (data) {
                if (data.pil_id){return 'internal'}
                else { return 'external'}
        }}
             ],
              initComplete: function(settings, json) {
                   $('#total_pilots').text('Total pilots registered: ' + json.data.length );
                   $('#total_external_pilots').text(json.external);
                   $('#delete_external').hide();
                   if(json.external > 0){ $('#delete_external').show();}
  }
       })

       };
