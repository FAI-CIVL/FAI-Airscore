function populate_task(tasPk){
$(document).ready(function() {

    $('#task_result').dataTable({
        ajax: '/_get_task_result/'+tasPk,
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

            // times
            var tbl = document.createElement('table');
            var tbdy = document.createElement('tbody');
            if (json.info.startgates.length > 1)
            {
                for (var i=0; i < json.info.startgates.length; i++)
                {
                    var tr = document.createElement('tr');
                    var td = document.createElement('td');
                    if (i==0)
                    {
                        td.innerHTML = '<b>Startgates:</b>'
                    }
                    else
                    {
                        td.appendChild(document.createTextNode('\u0020'))
                    }
                    tr.appendChild(td)
                    var td = document.createElement('td');
                    td.style.textAlign = "right";
                    td.innerHTML = (i+1) + '. <b>' + json.info.startgates[i] + '</b>'
                    tr.appendChild(td)
                    tbdy.appendChild(tr);
                }
            }
            else
            {
                var tr = document.createElement('tr');
                var td = document.createElement('td');
                td.innerHTML = '<b>Startgate:</b>'
                tr.appendChild(td)
                var td = document.createElement('td');
                td.style.textAlign = "right";
                td.innerHTML = '<b>' + json.info.start_time + '</b>'
                tr.appendChild(td)
                tbdy.appendChild(tr);
            }
            if (json.info.stopped_time)
            {
                var tr = document.createElement('tr');
                var td = document.createElement('td');
                td.innerHTML = '<b>Stopped: </b>'
                tr.appendChild(td)
                var td = document.createElement('td');
                td.style.textAlign = "right";
                td.innerHTML = '<b>' + json.info.stopped_time + '</b>'
                tr.appendChild(td)
            }
            else
            {
                var tr = document.createElement('tr');
                var td = document.createElement('td');
                td.innerHTML = '<b>Task Deadline: </b>'
                tr.appendChild(td)
                var td = document.createElement('td');
                td.style.textAlign = "right";
                td.innerHTML = '<b>' + json.info.task_deadline + '</b>'
                tr.appendChild(td)
            }
            tbdy.appendChild(tr);
            tbl.appendChild(tbdy);
            $('#comp_header').append(tbl)

            // waypoints
            for (var c=0; c < json.route.length; c++)
            {
                $('#waypoints tbody').append("<tr><td>" + json.route[c].name +
                        "</td><td>" + json.route[c].type +
                        "</td><td>" + json.route[c].radius +
                        "</td><td>" + json.route[c].cumulative_dist +
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