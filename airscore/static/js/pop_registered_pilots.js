function populate_pilots(compid){
$(document).ready(function() {

    $('#pilots').dataTable({
        ajax: '/get_registered_pilots/'+compid,
        paging: false,
        searching: false,
        info: true,
//        columnDefs: [
//            {
//                targets: [ 0 ],
//                render: function ( data, type, row ) {
//                    return data;
//            },
//            {
//                targets: [ 1 ],
//                visible: false,
//                searchable: false
//            }
//        ],
        columns: [
//             { data: 'par_id', name: "par_id" },
//             { data: 'pil_id', name: "pil_id" },
             { data: 'ID', name: "#" },
             { data: 'name', name: "Pilot" },
             { data: 'nat', name: "Nat" },
             { data: 'glider', name: "Glider" },
             { data: 'sponsor', name: "Sponsor" },
             { data: 'status', name: "Status" }
       ],
        "initComplete": function(settings, json)
        {
            var table = $('#pilots');
            var rows = $("tr", table).length-1;
            var numCols = $("th", table).length;

            // comp info
            $('#comp_name').text(json.info.comp_name);
            $('#comp_site').text(json.info.comp_site);
            $('#comp_date').text(json.info.date_from + ' - ' + json.info.date_to);
            // user registration
            if (json.pilot == null){
                $('#register').text('You need to Login to register')
            } else if (json.pilot == 0){
                var button = document.createElement("button");
                button.innerHTML = "Register";
                document.getElementById("register").appendChild(button);
                button.addEventListener ("click", function() {
                        alert("So, you want to register");
                    });
            } else if (json.pilot.ID == null){
                $('#register').text('You are already registered')
            } else {
                $('#register').text('You are already registered with ID ' + json.pilot.ID)
            }
        }
    });
});
}