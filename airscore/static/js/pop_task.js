function populate_task(tasPk){
$(document).ready(function() {
//  var tasPk = '123' // url.pathname.trimleft("/");
    $('#task_result').dataTable({
        ajax: '/get_task_result/'+tasPk,
        paging: false,
        searching: true,
        info: false,
        "dom": 'lrtip',
        "columnDefs": [
      {
          "targets": [ 4 ],
          "visible": false
      },
      {
          "targets": [ 3 ],
          "orderData": [ 4, 0 ]
      }
  ],
        "initComplete": function(settings, json)
        {
            var table = $('#task_result');
            var rows = $("tr", table).length-1;
            var numCols = $("th", table).length;

            // comp info
            $('#comp_name').text(json.info.comp_name + " - " + json.info.task_name);
            $('#task_date').text(json.info.date + ' ' + json.info.task_type);
            $('#comp_header').append('<b>Start: ' + format_seconds(json.info.start_time + json.info.time_offset) + ' End: ' + format_seconds(json.info.task_deadline + json.info.time_offset) + '</b><br>');
            if (json.info.stopped_time)
            {
                $('#comp_header').append('<b>Stopped: ' + json.info.stopped_time + '</b><br>');
                $('#altbonus').text("S.Alt");

            }
            if (json.info.comp_class != "PG")
            {
                update_classes(json.info.comp_class);
            }

            // waypoints
            for (var c=0; c < json.route.length; c++)
            {
                $('#waypoints tbody').append("<tr><td>" + json.route[c].name +
                        "</td><td>" + json.route[c].type +
                        "</td><td>" + json.route[c].radius +
                        "</td><td>" + Number((json.route[c].cumulative_dist/1000).toFixed(1)) +
                        "</td><td>" + json.route[c].description +
                        "</td></tr>");
            }

            // task info
            var half = Object.keys(json.formula).length / 2;
            var count = 0;
            $.each( json.formula, function( key, value ) {
                if (count < half)
                {
                    $('#formula1 tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
                }
                else
                {
                    $('#formula2 tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
                }
                count++;
            });

            $.each( json.stats, function( key, value ) {
                $('#taskinfo tbody').append('<tr><td>' + key + '</td><td>' + value + '</td></tr>');
            });

            // remove empty cols
            for ( var i=1; i<=numCols; i++ ) {
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
}