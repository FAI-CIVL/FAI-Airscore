var form_elements = ['user_id', 'first_name', 'last_name', 'email', 'confirm', 'username', 'password'];

$('#user_form').submit( function (e) {
  e.preventDefault(); // block the traditional submission of the form.
  cleanup_errors();
  let url = "/_activate_user/";
  $('#user_id').val(user_id);
  $('#username').val($('#email').val());  // use email as username
  let mydata = $('#user_form').serialize();
  console.log(mydata);

  $.ajax({
    type: "POST",
    url: url,
    data: mydata, // serializes the form's elements.
    success: function (response) {
      if (response.success) {
        let message = 'User successfully activated. You can now login.';
        create_flashed_message(message, 'info');
        setTimeout(function () {
            window.open('/');
        }, 5000);
      }
      else {
        if (response.errors) {
          let keys = Object.keys(response.errors);
          console.log('Error! ('+keys.length+')');
          keys.forEach( key => {
            let text = response.errors[key][0];
            $('#user_form div').find("[name='"+key+"']").css('background-color', 'orange');
            message = key + ': ' + text;
            create_flashed_message(message, 'danger');
          })
        }
      }
    }
  });
});

function cleanup_errors() {
  $('#user_form [name]').each( ( i, el ) => $(el).removeAttr('style') );
}

jQuery(document).ready(function($) {

});

