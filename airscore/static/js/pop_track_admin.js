

function populate_track_admin(task_id){
    $(document).ready(function(){
    $('#tracks').DataTable({
        destroy: true,
        ajax: '/users/_get_tracks_admin/'+task_id,
        paging: true,
        order: [[ 1, 'desc' ]],
        lengthMenu: [60, 150 ],
        searching: true,
        info: false,
        columns: [
            {data: 'ID', name:'ID'},
            {data: 'name', name:'Name'},
            {data: 'Result', name:'Result'},
            {data: null}],
              rowId: function(data) {
                return 'id_' + data.par_id;
                },
        columnDefs:[{
            targets: [-1],  render: function (a, b, data, d) {
            if(data['Result']=='Not Yet Processed' | data['Result'].indexOf("G record") >= 0){
            var buttons;
            buttons =
             '<button id="ABS' + data.par_id  +'" class="btn btn-primary mt-3" type="button" onclick="set_result(' + data.par_id +',\'abs\')">Set ABS</button> '
             +'<button id="MD' + data.par_id  +'" class="btn btn-primary mt-3" type="button" onclick="set_result(' + data.par_id +',\'mindist\')">Set Min Dist</button> '
             +'<button id="DNF' + data.par_id  +'" class="btn btn-primary mt-3" type="button" onclick="set_result(' + data.par_id +',\'dnf\')">Set DNF</button> '
             +'<button id="TrackUp' + data.par_id  +'" class="btnupload btn btn-primary mt-3" onclick="choose_file(' + data.par_id +');">Upload Track</button>'
             +'<div class = "hideatstart"  id="progress_percentage'+ data.par_id+ '" ><p id="progress_percentage _text'+data.par_id +'"></p></div>'
             +' <div id="filediv' + data.par_id  +'" class = "hideatstart" > <input id="fileupload' + data.par_id +'" type="file" size="chars" class="custom-file-input"  oninput="filesize(this);" data-url="/users/_upload_track/'+ task_id + '/' + data.par_id + '" name="tracklog" >'
            + ' <div id="filediv' + data.par_id  +'" class = "hideatstart" > <input id="fileupload_NO_G' + data.par_id +'" type="file" size="chars" class="custom-file-input"  oninput="filesize(this);" data-url="/users/_upload_track/'+ task_id + '/' + data.par_id + '" name="tracklog_NO_G" >'
//             +'<div id="progress'+ data.par_id+ '" ><div class="bar" style="width: 0%;"><p id="spinner'+ data.par_id + '"></p><p id="progress_text'+data.par_id +'"></p></div></div>'
             +'</div>'

             ;
             return buttons;
            }
            else if (data['Result']=='Processing..') {
            return data['file']
                        }

           else{ return '<button class="btn btn-danger mt-3" type="button" onclick="delete_track('+ data.track_id +','+ data.par_id +')">Delete Track</button> ';}

        }                 }],
        initComplete: function() {
             $(".hideatstart").hide();},
});

});
}

function open_bulk_modal() {
    $('#bulkmodal').modal('show');
}

function filesize(elem){
    document.cookie = `filesize=${elem.files[0].size}; SameSite=Strict; path=/`
}

function update_row(new_data){
    update_track_pilot_stats();
    var table = $('#tracks').dataTable();
    new_data.ID = $('#tracks').DataTable().row( $('tr#id_'+ new_data.par_id)).data()['ID'];
    new_data.name = $('#tracks').DataTable().row( $('tr#id_'+ new_data.par_id)).data()['name'];
    table.fnUpdate(new_data, $('tr#id_'+ new_data.par_id), undefined, false);
}

function delete_track(track_id, par_id){
    var mydata = new Object();
    mydata.track_id = track_id;
    mydata.par_id = par_id;
    $.ajax({
        type: "POST",
        url: "/users/_delete_track/" + track_id,
        contentType:"application/json",
        data : JSON.stringify(mydata),
        dataType: "json",
        success: function (response, par_id) {
            update_row(response);
            update_track_pilot_stats();
        }
    });
}

