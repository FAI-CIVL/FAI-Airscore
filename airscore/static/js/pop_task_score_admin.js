function populate_task_scores(taskid, filename){
    $(document).ready(function() {
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
    });
}

