function populate_pilots(compid){
    $('#pilots').dataTable({
        ajax: '/_get_participants_and_status/' + compid,
        info: true,
        paging: false,
        saveState: true,
        searching: true,
        filter: true,
        info: false,
        "dom": '<"#search"f>rt<"bottom"lip><"clear">',
        destroy: true,
        columns: [

             { data: 'ID', title: "#"},
             { data: 'name', title: "Pilot"},
             { data: 'sex', title: "Sex"},
             { data: 'nat', title: "Nat"},
             { data: 'glider', title: "Equip"},
             { data: 'glider_cert', title: "Certification"},
             { data: 'sponsor', title: "Sponsor"},
             { data: 'status', title: "Status"}

       ],
       "initComplete":
       function(settings, json){
       if(json.status == null){
               $("#reg_text").show();
       }
       else{
        $('#mod_id_number').val(json.pilot_details.ID).change();
        $('#mod_name').text(json.pilot_details.name);
        $('#mod_nat').val(json.pilot_details.nat).change();
        $('#mod_glider').val(json.pilot_details.glider).change();
        $('#mod_certification').val(json.pilot_details.glider_cert).change();
        $('#mod_sponsor').val(json.pilot_details.sponsor).change();


         if(json.status=='not_registered'){
            $("#reg_btn").show();
            $('#modify_confirmed').attr("onclick","register ('"+ json.pilot_details.pil_id +"')");
             }
         else if (json.status=='registered'){
            $("#unreg_btn").show();
            $("#modify_btn").show();
            $('#modify_confirmed').attr("onclick","save_modified_participant('"+ json.pilot_details.par_id +"')");
            $('#unreg_btn').attr("onclick","unregister('"+ json.pilot_details.pil_id +"')");
            }

       }
       }})

       };


function modify_participant(par_id){
$('#edit_par_modal').modal('show');
}

