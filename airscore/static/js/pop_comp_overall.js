function populate_comp_overall(comPk){
    $(document).ready(function() {
        $('#results_table').dataTable({
            ajax: '/_get_comp_result/'+comPk,
            paging: false,
            searching: true,
            saveState: true,
            info: false,
            "dom": 'lrtip',
            columns: [
                {data: 'ranks.rank', title:'#'},
                {data: 'ranks.class1', title:'#', defaultContent: ''},
                {data: 'ranks.class2', title:'#', defaultContent: ''},
                {data: 'ranks.class3', title:'#', defaultContent: ''},
                {data: 'ranks.class4', title:'#', defaultContent: ''},
                {data: 'fai_id', title:'FAI'},
                {data: 'civl_id', title:'CIVL'},
                {data: 'name', title:'Name'},
                {data: 'nat', title:'NAT'},
                {data: 'sex', title:'Sex'},
                {data: 'glider', title:'Glider'},
                {data: 'glider_cert', title:'EN'},
                {data: 'sponsor', title:'Sponsor'},
                {data: 'score', title:'Total'},
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
                {data: 'results.T20.score', title: 'T20'},
            ],
            rowId: function(data) {
                return 'id_' + data.par_id;
            },
            "columnDefs": [
                {
                    "targets": [ 1, 2, 3, 4, 5, 6, 9, 11 ],
//                    "targets": [ 5, 7 ],
                    "visible": false
                },
                //{ "type" : "numeric", "targets": [ 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 ] }
            ],
            "initComplete": function(settings, json) {
                var table = $('#results_table');
                var rows = $("tr", table).length-1;
                // Get number of all columns
                var numCols = $('#results_table').DataTable().columns().nodes().length;
                console.log('numCols='+numCols);

                // comp info
                $('#comp_name').text(json.info.comp_name);
                $('#comp_date').text(json.info.date_from + ' - ' + json.info.date_to);
                if (json.info.comp_class != "PG") {
                    update_classes(json.info.comp_class);
                }

                // some GAP parameters
                $('#formula tbody').append(
                            "<tr><td>Director</td><td>" + json.info.MD_name + '</td></tr>' +
                            "<tr><td>Location</td><td>" + json.info.comp_site + '</td></tr>' +
                            "<tr><td>Formula</td><td>" + json.formula.formula_name + '</td></tr>' +
                            "<tr><td>Overall Scoring</td><td>" + json.formula.overall_validity + ' (' + json.formula.validity_param + ')</td></tr>');
                if (json.formula.overall_validity == 'ftv') {
                    $('#formula tbody').append(
                            "<tr><td>Total Validity</td><td>" + json.stats.tot_validity + '</td></tr>');
                }

                // remove empty cols
                for ( var i=1; i<numCols; i++ ) {
                    var empty = true;
                    table.DataTable().column(i).data().each( function (e, i) {
                        if (e != "") {
                            empty = false;
                            return false;
                        }
                    } );

                    if (empty) {
                        table.DataTable().column( i ).visible( false );
                    }
                }
                // class picker
                $("#dhv option").remove(); // Remove all <option> child tags.
                // at the moment we provide the highest EN rating for a class and the overall_class_filter.js uses this.
                // if we want to be more specific and pass a list of all EN ratings inside a class we can do something like this: https://stackoverflow.com/questions/15759863/get-array-values-from-an-option-select-with-javascript-to-populate-text-fields
                $.each(json.classes, function(index, item) {
                    $("#dhv").append(
                        $("<option></option>")
                            .text(item.name)
                            .val(item.limit)
                    );
                });
            }
        });
    });
}