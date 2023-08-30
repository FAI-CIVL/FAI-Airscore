function populate_team_overall(compid){
    $('#comp_name').text('Loading Results ...');

    $.ajax({
        type: "GET",
        url: '/_get_comp_team_result/'+compid,
        contentType:"application/json",
        dataType: "json",
        success: function (json) {
            var compid = json.info.id;
            var taskNum = json.stats.valid_tasks
            console.log('taskNum='+taskNum);
            var columns = [];
            var idx = 0;
            // rankings
            //console.log(json.rankings);
            // json.rankings.forEach( function(item, index) {
            //   columns.push({data: 'rankings.'+item.rank_id.toString(), title: '#', name: item.rank_id.toString(), className: "text-right", defaultContent: '', visible: false});
            // });
            columns.push({data: 'group', title:'Group', className: "text-right", defaultContent: '', visible: false});
            columns.push({data: 'score', title:'Total', className: "text-right", defaultContent: '', visible: false});
            columns.push({data: 'team_score', title:'Team Total', className: "text-right", defaultContent: '', visible: false});
            columns.push({data: 'fai_id', title:'FAI', className: "text-right", defaultContent: '', visible: false});
            columns.push({data: 'civl_id', title:'CIVL', className: "text-right", defaultContent: '', visible: false});
            columns.push({data: 'name', title:'Name', render: function ( data, type, row ) { let span = '<span>'; if (row.sex == 'F'){span='<span class="sex-F">'}; return span + data + '</span>'}});
            columns.push({data: 'glider', title:'Equip'});
            columns.push({data: 'glider_cert', title:'EN', defaultContent: '', visible: false});
            columns.push({data: 'nat', title:'NAT', defaultContent: '', visible: false});
            columns.push({data: 'sex', title:'Sex', defaultContent: '', visible: false});
            columns.push({data: 'sponsor', title:'Sponsor'});
            json.tasks.forEach( function(item, index) {
                let code = item.task_code
                console.log( item.task_code.toString() + ': ' + item.training.toString());
                if ( !item.training ) {
                  columns.push({data: 'results.'+code+'.score', title: code, className: "text-right", defaultContent: ''});
                }
            });
            $('#results_table').dataTable({
                data: json.data,
                paging: false,
                searching: true,
                saveState: true,
                info: false,
                dom: 'lrtip',
                columns: columns,
                orderFixed: [[3, 'desc'],[2, 'desc']],
                rowGroup: {dataSrc: 'group'},
                initComplete: function(settings) {
                    var table= $('#results_table');
                    var rows = $("tr", table).length-1;
                    var numCols = table.DataTable().columns().nodes().length;

                    // comp info
                    console.log(json.info);
                    $('#comp_name').text(json.info.comp_name + "  - Teams");
                    $('#comp_date').text(json.info.date_from + ' - ' + json.info.date_to);

                    // some GAP parameters
                    $('#formula tbody').append(
                        "<tr><td>Director</td><td>" + json.info.MD_name + "</td></tr>" +
                        "<tr><td>Location</td><td>" + json.info.comp_site + "</td></tr>" +
                        "<tr><td>Formula</td><td>" + json.formula.team_size + " scoring, max " +  json.formula.max_team_size + " pilots</td></tr>"
                    );

                    $("#dhv option").remove(); // Remove all <option> child tags.
                    // $.each(json.rankings, function(index, item) {
                    //     $("#dhv").append(
                    //         $("<option></option>")
                    //             .text(item.rank_name)
                    //             .val(item.rank_id)
                    //     );
                    // });
                }
            });
        }
    });
}