
$(document).ready(function() {
    // var url = new URL('http://highcloud.net/xc/get_result.php' + window.location.search);
    // var comPk = url.searchParams.get("comPk");
    $('#task_result').dataTable({
        ajax: '/get_comp_result/32',
        paging: false,
        searching: true,
        saveState: true,
        info: false,
        "dom": 'lrtip',
        "columnDefs": [
            {
                "targets": [ 1, 2, 6, 8 ],
                "visible": false
            },
            //{ "type" : "numeric", "targets": [ 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25 ] }
        ],
        "initComplete": function(settings, json)
        {
            var table= $('#task_result');
            var rows = $("tr", table).length-1;
            var numCols = $("th", table).length+3;

            // comp info
            $('#comp_name').text(json.info.comp_name);
            $('#comp_date').text(json.info.date_from + ' - ' + json.info.date_to);
            if (json.info.comp_class != "PG")
            {
                update_classes(json.info.comp_class);
            }

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
