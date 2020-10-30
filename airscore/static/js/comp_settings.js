$(document).ready(function() {
  get_tasks( compid );
  get_scorekeepers( compid );

  // jQuery selection for the 2 select boxes
  var dropdown = {
    category: $('#select_category'),
    formula: $('#select_formula'),
    igc_config: $('#igc_parsing_file'),
    classification: $('#select_classification')
  };

  console.log('class='+dropdown.classification.val());
  update_rankings( dropdown.classification.val() );
  document.getElementById("link_igc_config").setAttribute("href", "/users/igc_parsing_config/" + dropdown.igc_config.val());

  // function to call XHR and update formula dropdown
  function updateFormulas() {
    var cat = {
      category: dropdown.category.val()
    };
    dropdown.formula.attr('disabled', 'disabled');
    dropdown.formula.empty();
    $.getJSON("/users/_get_formulas", cat, function(data) {
      data.forEach(function(item) {
        dropdown.formula.append(
          $('<option>', {
             value: item[0],
             text: item[1]
          })
        );
      });
      dropdown.formula.removeAttr('disabled');
    });
  }

  // event listener to category dropdown change
  dropdown.category.on('change', function() {
    updateFormulas();
    ask_update('category');
  });

  // event listener to formula dropdown change
  dropdown.formula.on('change', function() {
     ask_update('formula');
  });

  // event listener to igc config dropdown change
  dropdown.igc_config.on('change', function() {
     $('#link_igc_config').attr("href", "/users/igc_parsing_config/" + dropdown.igc_config.val());
  });

  // event listener to classification dropdown change
  dropdown.classification.on('change', function() {
     let cat_id = dropdown.classification.val()
     update_rankings(cat_id);
  });

});

function ask_update(change) {
  var formula = $('#select_formula').val();
  var field = formula;

  if(change=='category') {
    field=$('#select_category').val();
    formula = field;
  }

  var heading1 = "<p>Changing to ";
  var heading2 = ". Do you also want to update the advanced parameters to the standard for ";
  $("#formula_modal-body").html(heading1 + field + heading2 + formula +'?</p>');
  $('#formula_confirmed').attr("onclick","get_adv_settings()");
  $('#formula_modal').modal('show');
}

function add_task() {
  $('#add_task_modal').modal('show');
}

function confirm_delete(task_num, taskid) {
  var x = task_num;
  var myHeading = "<p>Are you sure you want to delete Task ";
  $("#modal-body").html(myHeading + x + '?</p>');
  $('#delete_confirmed').attr("onclick","delete_task('"+taskid+"')");
  $('#delete_task_modal').modal('show');
}

function delete_task(taskid){
  $.ajax({
    type: "POST",
    url: '/users/_del_task/'+taskid,
    success: function () {
      get_tasks()
    }
  });
}

function get_tasks() {
  $.ajax({
    type: "GET",
    url: link_get_tasks,
    contentType:"application/json",
    dataType: "json",
    success: function (json) {
      var columns = [];
      columns.push({data: 'task_num', title:'#', className: "text-right", defaultContent: ''});
      columns.push({data: 'task_id', title:'ID', className: "text-right", defaultContent: '', visible: false});
      columns.push({data: 'date', title:'Date', defaultContent: ''});
      columns.push({data: 'region_name', title:'Region'});
      columns.push({data: 'opt_dist', title:'Dist.', name:'dist', className: "text-right", defaultContent: ''});
      columns.push({data: 'comment', title:'Comment', name:'comment', defaultContent: ''});
      columns.push({data: 'task_id', render: function ( data ) { return '<button class="btn btn-info ml-3" type="button" onclick="window.location.href = \'/users/task_admin/' + data + '\'">Settings</button>'}});
      columns.push({data: 'task_id', render: function ( data ) { return '<button class="btn btn-info ml-3" type="button" onclick="window.location.href = \'/users/track_admin/' + data + '\'">Tracks</button>'}});
      columns.push({data: 'task_id', render: function ( data ) { return '<button class="btn btn-info ml-3" type="button" onclick="window.location.href = \'/users/task_score_admin/' + data + '\'">Scores</button>'}});
      columns.push({data: 'task_id', render: function ( data, type, row ) { return '<button class="btn btn-danger" type="button" onclick="confirm_delete( ' + row.task_num + ', ' + data + ' )" data-toggle="confirmation" data-popout="true">Delete</button>'}});

      $('#tasks').DataTable( {
        data: json.tasks,
        destroy: true,
        paging: false,
        responsive: true,
        saveState: true,
        info: false,
        dom: 'lrtip',
        columns: columns,
        rowId: function(data) {
          return 'id_' + data.task_id;
        },
        initComplete: function(settings) {
          var table = $('#tasks');
          var rows = $("tr", table).length-1;
          // Get number of all columns
          var numCols = $('#tasks').DataTable().columns().nodes().length;
          console.log('numCols='+numCols);
          for ( var col=1; col<numCols; col++ ) {
            var empty = true;
            table.DataTable().column(col).data().each( val => {
              if (val != "") {
                empty = false;
                return false;
              }
            });
            if (empty) {
              table.DataTable().column( col ).visible( false );
            }
          }
        }
      });
      $('#task_number').val(json['next_task']);
      $('#task_region').val(json['last_region']);
    }
  });
}

function add_scorekeeper(){
  document.getElementById("save_scorekeeper_button").innerHTML = "Adding...";
  document.getElementById("save_scorekeeper_button").className = "btn btn-warning";
  var mydata = new Object();
  var e = document.getElementById('scorekeeper');
  mydata.id = e.options[e.selectedIndex].value;
  console.log('id='+mydata.id)
  $.ajax({
    type: "POST",
    url: link_add_scorekeeper,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function () {
      get_scorekeepers()
      document.getElementById("save_scorekeeper_button").innerHTML = "Save";
      document.getElementById("save_scorekeeper_button").className = "btn btn-success";
    }
  });
}

function save_ladders(){
  document.getElementById("save_ladders_button").innerHTML = "Saving...";
  document.getElementById("save_ladders_button").className = "btn btn-warning";
  var mydata = {};
  mydata.checked = [];
  $('#ladder_list').find('input').each( (i, el) =>  {
    if (el.checked){
      mydata.checked.push(el.value)
    }
    console.log('val='+ el.value);
    console.log('checked='+ el.checked);
  });
  console.log('data='+ mydata);
  $.ajax({
    type: "POST",
    url: link_save_comp_ladders,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function ( response ) {
      if (response.success){
        document.getElementById("save_ladders_button").innerHTML = "Saved";
        document.getElementById("save_ladders_button").className = "btn btn-success";
      }
      else {
        document.getElementById("save_ladders_button").innerHTML = "Error";
        document.getElementById("save_ladders_button").className = "btn btn-danger";
      }
      setTimeout(function(){
        document.getElementById("save_ladders_button").innerHTML="Save";
        document.getElementById("save_ladders_button").className = "btn btn-success";
      }, 3000);
   }
  });
}

function save_task(){
  $('#save_task_button').hide();
  $('#add_task_spinner').html('<div class="spinner-border" role="status"><span class="sr-only"></span></div>');
  var mydata = new Object();
  mydata.task_name = $('#task_name').val();
  mydata.task_date = $('#task_date').val();
  mydata.task_num = $('#task_number').val();
  mydata.task_comment = $('#task_comment').val();
  mydata.task_region = $('#task_region').val();

  $.ajax({
    type: "POST",
    url: link_add_task,
    contentType:"application/json",
    data : JSON.stringify(mydata),
    dataType: "json",
    success: function () {
      get_tasks();
      $('#add_task_spinner').html('');
      $('#save_task_button').show();
      $('#add_task_modal').modal('hide');
    }
  });
}

function get_scorekeepers(){
  $.ajax({
     type: "GET",
     url: link_get_scorekeepers,
     contentType:"application/json",
     dataType: "json",
     success: function (response) {
       var content = '';
       for (var i = 0; i < response['scorekeepers'].length; i++) {
         content += '<tr><TD class="c3">'+ response['scorekeepers'][i]['first_name'] + ' '+ response['scorekeepers'][i]['last_name'] +'</TD></tr>'
       }
       $('#scorekeeper_table').append(content);
       $('#owner').html(response['owner']['first_name'] + ' ' + response['owner']['last_name'] );
     }
  });
}

function get_adv_settings(){
  var formula = new Object();
  formula.formula = $('#select_formula').val();
  formula.category = $('#select_category').val();
  $.ajax({
    type: "POST",
    url: link_get_adv_settings,
    contentType:"application/json",
    data : JSON.stringify(formula),
    dataType: "json",
    success: function (data) {
      $('#formula_distance').val(data.formula_distance);
      $('#formula_time').val(data.formula_time);
      $('#formula_arrival').val(data.formula_arrival);
      $('#formula_departure').val(data.formula_departure);
      $('#lead_factor').val(data.lead_factor);
      $('#no_goal_penalty').val(data.no_goal_penalty);
      $('#tolerance').val(data.tolerance);
      $('#min_tolerance').val(data.min_tolerance);
      $('#glide_bonus').val(data.glide_bonus);
      $('#arr_alt_bonus').val(data.arr_alt_bonus);
      $('#arr_max_height').val(data.arr_max_height);
      $('#arr_min_height').val(data.arr_min_height);
      $('#validity_min_time').val(data.validity_min_time);
      $('#scoreback_time').val(data.scoreback_time);
      $('#max_JTG').val(data.max_JTG);
      $('#JTG_penalty_per_sec').val(data.JTG_penalty_per_sec);
    }
  });
}

function update_rankings( cat_id ) {
    let classification = classifications.find(el => el.cat_id == cat_id );
    let cat = classification.categories;
    let name = classification.cat_name
    let columns = [];
    columns.push({data: 'title', title:'rankings:', defaultContent: ''});
    columns.push({data: 'members', render: function ( data ) { return data.join(', ')}});

    $('#rankings').DataTable({
        data: cat,
        destroy: true,
        paging: false,
        bAutoWidth: false,
        responsive: true,
        saveState: true,
        info: false,
        dom: 'lrtip',
        columns: columns,
        initComplete: function(settings, json) {
            // Female Ranking
            let female = (classification.female == 1).toString();
            console.log('female='+female);
            $('#rankings').DataTable().row.add({title: 'Female', members: [female]}).draw();
        }
    });
}

function export_to_fsdb(){
  $('#export_fsdb').hide();
  $('#fsdb_spinner').html('<div class="spinner-border" role="status"><span class="sr-only">Preparing FSDB...</span></div>');
  startDownloadChecker("loadingProgressOverlay", 120);
}

function startDownloadChecker(imageId, timeout) {

  var cookieName = "ServerProcessCompleteChecker";  // Name of the cookie which is set and later overridden on the server
  var downloadTimer = 0;  // reference to timer object

  // The cookie is initially set on the client-side with a specified default timeout age (2 min. in our application)
  // It will be overridden on the server side with a new (earlier) expiration age (the completion of the server operation),
  // or auto-expire after 2 min.
  setCookie(cookieName, 0, timeout);

  // set timer to check for cookie every second
  downloadTimer = window.setInterval(function () {
    var cookie = getCookie(cookieName);

    // If cookie expired (NOTE: this is equivalent to cookie "doesn't exist"), then clear "Loading..." and stop polling
    if ((typeof cookie === 'undefined')) {
      $('#export_fsdb').show();
      $('#fsdb_spinner').html('');
      window.clearInterval(downloadTimer);
    }
  }, 1000); // Every second
}

// These are helper JS functions for setting and retrieving a Cookie
function setCookie(name, value, expiresInSeconds) {
  var exdate = new Date();
  exdate.setTime(exdate.getTime() + expiresInSeconds * 1000);
  var c_value = escape(value) + ((expiresInSeconds == null) ? "" : "; expires=" + exdate.toUTCString());
  document.cookie = name + "=" + c_value + '; path=/';
}

function getCookie(name) {
  var parts = document.cookie.split(name + "=");
  if (parts.length == 2 ) {
    return parts.pop().split(";").shift();
  }
}
