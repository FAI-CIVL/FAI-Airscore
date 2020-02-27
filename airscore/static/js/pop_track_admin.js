function populate_track_admin(task_id){
    $(document).ready(function(){
    $('#tracks').DataTable({
        destroy: true,
        ajax: '/users/_get_tracks_admin/'+task_id,
        paging: true,
        order: [[ 1, 'desc' ]],
        lengthMenu: [ 60, 150 ],
        searching: true,
        info: false,
        columns: [
            {data: 'name', name:'Name'},
            {data: 'par_id', name:'par_id'},
            {data: 'Result', name:'Result'},
            {data: null}],
              rowId: function(data) {
                return 'id_' + data.par_id;
                },
        columnDefs:[{
            targets: [-1],  render: function (a, b, data, d) {
            if(data['Result']=='Not Yet Processed'){
            var buttons;
            buttons =
             '<button class="btn btn-primary mt-3" type="button" onclick="set_result(' + data.par_id +',\'abs\')">Set ABS</button> '
             +'<button class="btn btn-primary mt-3" type="button" onclick="set_result(' + data.par_id +',\'mindist\')">Set Min Dist</button> '
              +'<button class="btn btn-primary mt-3" type="button" onclick="set_result(' + data.par_id +',\'dnf\')">Set DNF</button> '
//             +'<button class="btn btn-primary mt-3" type="button" >Add Track</button> '
             +'<input id="fileupload" type="file" class="btn btn-primary mt-3 custom-file-input"  oninput="filesize(this);" data-url="/users/_upload_track/'+ data.track_id + '/' + data.par_id + '" name="tracklog" ><label class="custom-file-label" for="image">Add track</label><div id="progress'+ data.par_id+ '"><div class="bar" style="width: 0%;"><p id="progress_text'+data.par_id +'"></p></div>';
             return buttons;
            }
           else{ return '<button class="btn btn-danger mt-3" type="button" onclick="delete_track('+ data.track_id +','+ data.par_id +')">Delete Track</button> ';}

        }                 }],
});
});
}

