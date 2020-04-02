function populate_country_overall(comPk){
$(document).ready(function() {
    $('#task_result').dataTable({
        ajax: '/_get_comp_country_result/'+comPk,
        paging: false,
        searching: true,
        saveState: true,
        info: false,
        "dom": 'lrtip',
        columns: [
            {data: 'group', title:'group'},
            {data: 'score', title:'Total'},
            {data: 'nation_score', title:'Nation Total'},
            {data: 'fai_id', title:'FAI'},
            {data: 'civl_id', title:'CIVL'},
            {data: 'glider', title:'Glider'},
            {data: 'glider_cert', title:'EN'},
            {data: 'name', title:'Name'},
            {data: 'nat', title:'NAT'},
            {data: 'sex', title:'Sex'},
            {data: 'sponsor', title:'Sponsor'},
            {data: 'results.T1.score', title:'T1'},
            {data: 'results.T2.score', title: 'T2'},
            {data: 'results.T3.score', title: 'T3'},
            {data: 'results.T4.score', title: 'T4'},
            {data: 'results.T5.score', title: 'T5'},
            {data: 'results.T6.score', title: 'T6'},
            {data: 'results.T7.score', title: 'T7'},
            {data: 'results.T8.score', title: 'T8'},
            {data: 'results.T9.score', title: 'T9'},
            {data: 'results.T10.score', title: 'T10'},
            {data: 'results.T11.score', title: 'T11'},
            {data: 'results.T12.score', title: 'T12'},
            {data: 'results.T13.score', title: 'T13'},
            {data: 'results.T14.score', title: 'T14'},
            {data: 'results.T15.score', title: 'T15'},
            {data: 'results.T16.score', title: 'T16'},
            {data: 'results.T17.score', title: 'T17'},
            {data: 'results.T18.score', title: 'T18'},
            {data: 'results.T19.score', title: 'T19'},
            {data: 'results.T20.score', title: 'T20'}
],

    orderFixed: [[2, 'desc'],[1, 'desc']],

    rowGroup: {
        dataSrc: ['group']
//        startRender: function (rows, group) {     return (group )}

    },
        "columnDefs": [
            {
                "targets": [ 0, 1, 2, 3, 4, 5, 6,],
                "visible": false
            },
        ],
        "initComplete": function(settings, json)
        {
            var table= $('#task_result');
            var rows = $("tr", table).length-1;
            var numCols = $("th", table).length+6;

            // comp info
            $('#comp_name').text(json.info.comp_name + "  - Nations");
            $('#comp_date').text(json.info.date_from + ' - ' + json.info.date_to);

            // some GAP parameters
            $('#formula tbody').append(
                        "<tr><td>Director</td><td>" + json.info.MD_name + '</td></tr>' +
                        "<tr><td>Location</td><td>" + json.info.comp_site + '</td></tr>' +
                        "<tr><td>Formula</td><td>" + json.formula.formula + '</td></tr>' +
                        "<tr><td>Overall Scoring</td><td>" + json.formula.overall_validity + ' (' + json.formula.validity_param*100 + ')</td></tr>');
            if (json.formula.overall_validity == 'ftv')
            {
                $('#formula tbody').append(
                        "<tr><td>Total Validity</td><td>" + json.stats.tot_validity + '</td></tr>');
            }

            // remove empty cols
            for ( var i=1; i<=numCols; i++ )
            {
                var empty = true;
                table.DataTable().column(i).data().each( function (e, i) {
                    if (e != "")
                    {
                        empty = false;
                        return false;
                    }
                } );

                if (empty) {
                    table.DataTable().column( i ).visible( false );
                }
            }

        }
    });
});
}