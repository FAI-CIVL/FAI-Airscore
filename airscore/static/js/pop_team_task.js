function populate_team_task(task_id){
$(document).ready(function() {
    $('#task_result').dataTable({
        ajax: '/_get_task_team_result/'+task_id,
        paging: false,
        searching: true,
        saveState: true,
        info: false,
        "dom": 'lrtip',
        columns: [
            {data: 'group', title:'group'},
            {data: 'team_score', title:'Team Total'},
            {data: 'fai_id', title:'FAI'},
            {data: 'civl_id', title:'CIVL'},
            {data: 'glider', title:'Equip'},
            {data: 'glider_cert', title:'EN'},
            {data: 'name', title:'Name'},
            {data: 'nat', title:'NAT'},
            {data: 'sex', title:'Sex'},
            {data: 'sponsor', title:'Sponsor'},
            {data: 'score', title:'Total'}

],

    orderFixed: [[1, 'desc'],[10, 'desc']],

    rowGroup: {
        dataSrc: ['group']

    },
        "columnDefs": [
            {
                "targets": [ 0, 1, 2, 3, 4, 5],
                "visible": false
            },
        ],
        "initComplete": function(settings, json)
        {
            var table= $('#task_result');
            var rows = $("tr", table).length-1;
            var numCols = $("th", table).length+6;

            // task info
            $('#comp_name').text(json.info.comp_name)
            $('#task_name').text(json.info.task_name + " - Teams");
            $('#task_date').text(json.info.date);

            // some GAP parameters
            $('#formula tbody').append(
                    "<tr><td>Director</td><td>" + json.info.MD_name + '</td></tr>' +
                    "<tr><td>Location</td><td>" + json.info.comp_site + '</td></tr>' +
                    "<tr><td>Formula</td><td>" + json.formula.formula_name + '</td></tr>' +
                    "<tr><td>Overall Scoring</td><td>" + json.formula.overall_validity);
            if (json.formula.overall_validity == 'ftv') {
                $('#formula tbody').append(
                    ' (' + json.formula.validity_param*100 + ')</td></tr>' +
                    "<tr><td>Total Validity</td><td>" + json.stats.total_validity + '</td></tr>');
            }
            else {
                    $('#formula tbody').append('</td></tr>');
            }


        }
    });
});
}