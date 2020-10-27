// function to call XHR and update formula dropdown
function updateRegions() {
  dropdown.region.attr('disabled', 'disabled');
  dropdown.region.empty();
  $.getJSON(url_get_regions,
      function(data) {
        region_details = data.details
        data.choices.forEach(function(item) {
          dropdown.region.append(
            $('<option>', {
              value: item[0],
              text: item[1]
            })
          );
        });
        dropdown.region.removeAttr('disabled');
        $("#select_region").val(data.choices[0][0]);
        update_details();
  });
}

function update_details(){
  let regid = dropdown.region.val();
  let waypoints_filename = region_details[dropdown.region.val()].filename;
  let openair_filename = region_details[dropdown.region.val()].openair;
  if(waypoints_filename){
    $('#region_wpt_filename').text('Waypoint file: ' + waypoints_filename )
  }
  else { $('#region_wpt_filename').text('Waypoint file: None') }
  if(openair_filename){
    $('#region_oair_filename').html('Airspace file: <a href="/users/airspace_map/' + openair_filename + '">' + openair_filename +'</a>')
  }
  else { $('#region_oair_filename').text('Airspace file: None') }

  $('#region_wpt_no').text('Waypoints : ');
  populate_waypoints(regid, openair_filename);
}

function delete_region(regid){
  $.ajax({
    type: "POST",
    url: '/users/_delete_region/'+regid,
    success: function () {
      updateRegions();
//      populate_waypoints($('#select_region').val());
    }
  });
};

function confirm_delete() {
  var x =  $('#select_region option:selected').text();
  var myHeading = "<p>Are you sure you want to delete region ";
  $("#modal-body").html(myHeading + x + '?</p>');
  $('#delete_confirmed').attr("onclick","delete_region('"+ $('#select_region').val()+"')");
  $('#modal').modal('show');
}

function filesize(elem){
  document.cookie = `filesize=${elem.files[0].size}; SameSite=Strict; path=/`
}

var region_details = '';
var dropdown = {
  region: $('#select_region'),
};

$(document).ready(function() {
  updateRegions();

  // event listener to region dropdown change
  dropdown.region.on('change', function() {
    update_details();
  });
});

