function delete_space(index, name){
  $("#delete_airspace_" + index).closest("tr").toggleClass("text-muted bg-dark");
  if (delete_airspace_list.includes(name)===false){
    $("#delete_airspace_" + index).text("Reinstate");
    delete_airspace_list.push(name);
  }
  else {
    $("#delete_airspace_" + index).text("Delete");
    const nameindex = delete_airspace_list.indexOf(name);
    if (nameindex > -1) {
      delete_airspace_list.splice(nameindex, 1);
    }
  }
};

function get_table_data(){
  // loop over each table row (tr)
  $("#airspace_table tr").each(function(){
    var currentRow=$(this);
    var name_value=currentRow.find("td:eq(0)").text();
    var floor_value=currentRow.find("td:eq(2)").text();
    var ceiling_value=currentRow.find("td:eq(3)").text();
    var obj={};
    obj.name=name_value;
    obj.floor=floor_value;
    obj.ceiling=ceiling_value;
    if(name_value !== ""){
      table_data.push(obj);
    }
  });
}

function save_new(){
  get_changes()
  if($("#filename").val()){
    $('#file_save_Modal').modal('hide');
    var inputs = document.getElementById('airspace_table_body').getElementsByTagName('td');
    $.ajax({
      url: '/users/save_airspace',
      contentType:"application/json",
      dataType:"json",
      data: JSON.stringify({ "delete": delete_airspace_list, "changes": changes,  "old_filename": original_file, "new_filename": $("#filename").val()}),
      type: 'PUT',
      success: function(response) {
        if (response.redirect){
          window.location.href = response.redirect;
        }
      },
      error: function(error) {
        console.log(error);
      }
    });
  }
}

function get_changes(){
  get_table_data();
  let counter = 0;
  table_data.forEach(function(element) {
    if(typeof airspace_detail[counter] !== 'undefined'){
      if( element.name==airspace_detail[counter].name) //should always be equal
      {
        if(element.floor!==airspace_detail[counter].floor_description) {
          changes.push({'name': element.name, 'old': airspace_detail[counter].floor_description, 'new': element.floor});
        };
        if(element.ceiling !==airspace_detail[counter].ceiling_description) {
          changes.push({'name': element.name, 'old': airspace_detail[counter].ceiling_description, 'new': element.ceiling});
        };
      };
   };
   counter++;
  });
  console.log(changes);
}

var delete_airspace_list = [];
var table_data=[];
var changes = [];

$(document).ready(function() {
  $('#airspace_table').editableTableWidget();
});
