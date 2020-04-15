function populate_registered_pilot_details(compid, pilot_data){

    $('#pilots').dataTable({
        ajax: '/users/_get_participants/' + compid,
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
             { data: null}
       ],

                     rowId: function(data) {
                return 'id_' + data.par_id;
                },
                 columnDefs:[{
            targets: [-1],  render: function (a, b, data, d) {

            return ('<td  class ="value" ><button type="button" class="btn btn-primary" onclick="edit_participant('
               +  data.par_id + ')" data-toggle="confirmation" data-popout="true">Edit</button></td>');



        }                 }],



       })

       };
