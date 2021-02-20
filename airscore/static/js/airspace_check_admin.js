var dropdown = {
    h_boundary_penalty: $('#h_boundary_penalty'),
    v_boundary_penalty: $('#v_boundary_penalty'),
    h_max_penalty: $('#h_max_penalty'),
    v_max_penalty: $('#v_max_penalty'),
    func: $('#function')
};

function show_boundary() {
  $('#h_boundary_section').hide();
  $('#v_boundary_section').hide();
  if ( $('#double_step').is(":checked") ) {
    $('#h_boundary_section').show();
    $('#v_boundary_section').show();
  }
}

function show_v_limit() {
  $('#v_limits').hide();
  if ( $('#h_v').is(":checked") ) { $('#v_limits').show(); }
}

function update_parameters(){
  if ( dropdown.func.val() == 'linear' ) {
    $('#double_step_div').show();
    show_boundary();
    show_v_limit();
  }
  else {
    $('#double_step_div').hide();
    $('#h_boundary_section').hide();
    $('#v_boundary_section').hide();
    show_v_limit();
  }
}

$(document).ready(function() {
  show_boundary();
  show_v_limit();
  update_parameters();

  // event listener to formula dropdown change
  dropdown.func.on('change', function() {
    console.log('func changed');
    update_parameters();
  });

  // vertical limits display checkbox value change
  $('#h_v').change(function() {
    console.log('hv changed');
    show_v_limit();
  });

  // double steps checkbox value change
  $('#double_step').change(function() {
    console.log('ds changed '+$('#double_step').is(":checked"));
    show_boundary();
  });

  // inform when saving changings is needed
  $('#airspace_check_form :input').change(function(){
    console.log('form changed');
    $('#airspace_check_save_button').removeClass( "btn-outline-secondary" ).addClass( "btn-warning" );
    $('#save_button_warning_text').addClass('bg-warning').html('Parameters are changed and need to be saved');
  });

});