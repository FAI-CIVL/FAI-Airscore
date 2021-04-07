// Comp Result Info Table
function updateFiles(load_latest=false) {
  let mydata = new Object();
  mydata.offset = new Date().getTimezoneOffset();
  comp.dropdown.empty().attr('disabled', 'disabled');

  $.ajax({
    type: "POST",
    url: '/users/_get_comp_result_files/'+compid,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      active = response.comp_active;
      header = response.comp_header;
      choices = response.comp_choices;
      comp.dropdown.empty().attr('disabled', 'disabled');
      comp.header.html(header)
      if (choices.length == 0) {
        comp.active_file = '';
        comp.scoring_section.hide();
        comp.info_section.hide();
        comp.download_html.attr('onclick', "").hide();
      }
      else {
        comp.scoring_section.show();
        comp.info_section.show();
        comp_result_files_info = response.comp_choices;
        console.log(comp_result_files_info);
        choices.forEach(function(item) {
          comp.dropdown.append(
            $('<option>', {
              value: item.filename,
              text: item.text
            })
          );
        });
        if (!external) comp.dropdown.removeAttr('disabled');
        if (active) comp.active_file = active;
        comp.latest = comp.dropdown.find('option:first').val();
        if (load_latest || !active) comp.dropdown.val(comp.latest);
        else comp.dropdown.val(active);
        get_status();
        update_buttons();
//        console.log('active: '+comp.active_file);
//        console.log('selected: '+comp.selected);
//        console.log('latest: '+comp.latest);
//        console.log('status: '+comp.status);
//        console.log('timestamp: '+comp.timestamp);
      }
    }
  });
}

// Toggle Publish
function toggle_publish() {
  let mydata = {
    filetext: comp.dropdown.find('option:selected').text(),
    filename: comp.dropdown.find('option:selected').val(),
    iscomp: true,
    compid: compid
  }
  let url = '';
  if (mydata.filename == comp.active_file) {
    url = '/users/_unpublish_result';
  }
  else {
    url = '/users/_publish_result';
  }
  $.ajax({
    type: "POST",
    url: url,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      comp.active_file = response.filename;
      update_buttons();
      comp.header.text(response.header);
    }
  });
}

// Scores
function Score_modal() {
  $('#score_btn').show();
  $('#cancel_score_btn').show();
  $('#comp_calculate_spinner').html('');
  $('#status_comment').val(suggested_status);
  $('#scoremodal').modal('show');
}

function comp_calculate() {
  let mydata = {
    offset: new Date().getTimezoneOffset(),
    status: $('#status_comment').val(),
    autopublish: $("#autopublish").is(':checked')
  };

  $('#score_btn').hide();
  $('#cancel_score_btn').hide();
  $('#score_spinner').html('<div class="spinner-border" role="status"><span class="sr-only">Calculating...</span></div>');
  $.ajax({
    type: "POST",
    url:  url_calculate_comp_result,
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      create_flashed_message(response.message, response.success ? 'success' : 'danger');
      $('#scoremodal').modal('hide');
      updateFiles();
    }
  });
}

// Change Status
function open_status_modal() {
  $('#status_modal_filename').val(comp.selected);
  $('#status_modal_comment').val(comp.status);
  $('#statusmodal').modal('show');
}

function change_status() {
  let mydata = {
    filename: $('#status_modal_filename').val(),
    status: $('#status_modal_comment').val()
  }
  $.ajax({
    type: "POST",
    url: '/users/_change_result_status',
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      if (response.success) {
        updateFiles();
        $('#status_modal_filename').val('');
        $('#status_modal_comment').val('');
        $('#statusmodal').modal('hide');
      }
    }
  });
}

// Delete Result
function delete_result_modal() {
  let title = 'Delete Comp Result';

  $('#delete_modal_filename').val(comp.selected);
  let selected = comp.dropdown.find('option:selected').text().split(' - ');
  let ran = selected[0];
  let status = selected[1];
  if (!status) status = '<span class="text-secondary">No status</span>';
  else status = 'Status: <strong class="text-info">'+status+'</strong>';
  $('#delete_modal_title').html(title);
  $('#delete_description').html('Ran: <strong class="text-info">'+ran+'</strong>; '+status);
  $('#deletemodal').modal('show');
}

function delete_result(){
  let mydata = new Object();
  mydata.deletefile = $("#deletefile").is(':checked');
  mydata.filename = $('#delete_modal_filename').val();
  $.ajax({
    type: "POST",
    url:  '/users/_delete_task_result',
    contentType: "application/json",
    data: JSON.stringify(mydata),
    dataType: "json",
    success: function(response) {
      updateFiles();
      $('#deletemodal').modal('hide');
    }
  });
}

// Functions
function get_preview_url() {
  let file = comp.selected;
  let url = '/comp_result/'+compid;
  url += '?file='+file;
  return url
}

function get_status(){
  comp.selected = comp.dropdown.find('option:selected').val();
  let info = comp_result_files_info.find(el => el.filename == comp.selected);
  comp.timestamp = info.timestamp;
  comp.status = info.status;
  if (comp.status && comp.status.includes('Auto Generated' )) {
    comp.status = comp.status.replace('Auto Generated ', '');
  }
  $('#info_status').html(info.status);
  $('#info_timestamp').html(info.timestamp);
  $('#tasks_table').dataTable({
    data: info.tasks,
    paging: false,
    destroy: true,
    info: false,
    bFilter: false,
    bSort: false,
    columns: [
      {data: 'task_code', title:''},
      {data: 'date', title:'Date'},
      {data: 'day_quality', title:'Day Quality', render: function ( data ) { return Math.round(data*10000)/10000 }},
      {data: 'locked', title:'', render: function ( data ) { return ( !data ? '' : '<span class="text-success font-weight-bold">Official</span>')}},
    ],
    bAutoWidth: false,
    aoColumns : [
        { sWidth: '5px' },
        { sWidth: '10rem' },
        { sWidth: '5rem' },
        { sWidth: '10rem' }
    ],
    language: {
      "emptyTable":     "No Data"
    },
    initComplete: function(settings, json) {
      var api = this.api();
      $('#info_tasks_num').html(api.rows().count());
    }
  });
}

function ismissing(status){
  if (status == 'FILE NOT FOUND') return true; else return false;
}

function update_publish_button() {
  if (comp.selected == comp.active_file) {
    comp.publish.text('Un-Publish results');
    comp.publish.addClass('btn-warning').removeClass('btn-success');
  }
  else {
    comp.publish.text('Publish results');
    comp.publish.addClass('btn-success').removeClass('btn-warning');
  }
}

function check_active() {
//  console.log('active_file: '+comp.active_file);
  if (comp.active_file) {
    comp.download_html.attr('onclick', "location.href='/users/_download/comp_html/"+compid+"'");
    comp.download_html.show();
    // check file exists
    if (comp.dropdown.find('option[value="'+comp.active_file+'"]').text().includes('FILE NOT FOUND')){
      comp.download_html.prop('disabled', true);
    }
    else comp.download_html.prop('disabled', false);
  }
  else {
    comp.download_html.attr('onclick', "");
    comp.download_html.hide();
  }
}

function update_buttons() {
  if (ismissing(comp.status)) {
    comp.publish.text('Publish results');
    comp.publish.addClass('btn-secondary').removeClass('btn-success').removeClass('btn-warning');
    comp.publish.prop('disabled', true);
    comp.change_status.addClass('btn-secondary').removeClass('btn-primary');
    comp.change_status.prop('disabled', true);
    comp.preview.addClass('btn-secondary').removeClass('btn-primary');
    comp.preview.removeAttr('onclick');
    comp.preview.prop('disabled', true);
  }
  else {
    comp.publish.removeClass('btn-secondary');
    comp.publish.prop('disabled', false);
    update_publish_button();
    comp.change_status.removeClass('btn-secondary').addClass('btn-primary');
    comp.change_status.prop('disabled', false);
    comp.preview.removeClass('btn-secondary').addClass('btn-primary');
    comp.preview.attr('onclick', "window.open('"+ get_preview_url()+"','preview')");
    comp.preview.prop('disabled', false);
  }
  if (external || (comp.selected == comp.active_file && !ismissing(comp.status)) || comp.selected.includes('Overview')){
    comp.delete_file.prop('disabled', true);
  }
  else comp.delete_file.prop('disabled', false);
  check_active();
}

function calculate_status() {
  suggested_status = 'Official';

  tasks.every( el => {
    if (!el.locked) {
      suggested_status = 'Provisional';
      return false;
    }
    return true;
  });
}

// Main Section
var score_data = new Object();

// jQuery selection for the file select box
var comp = {
  dropdown: $('select[name="comp_result_file"]'),
  delete_file: $('#delete_comp_result'),
  publish: $('#comp_publish'),
  change_status: $('#change_comp_status'),
  download_html: $('#download_comp_html'),
  preview: $('#comp_preview'),
  header: $('#comp_header'),
  scoring_section: $('#comp_scoring_runs_section'),
  info_section: $('#comp_result_info_panel'),
  active_file: '',
  selected: '',
  latest: '',
  timestamp: '',
  status: ''
};

var suggested_status = '';
var comp_result_files_info = new Object();

$(document).ready(function() {
  updateFiles();
  calculate_status();

  //dropdown change listener
  comp.dropdown.change(function() {
    comp.selected = comp.dropdown.find('option:selected').val();
    get_status();
    update_buttons();
  });
});
