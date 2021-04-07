function create_flashed_message(text, category){
  if($('#flashed_messages').length){
    let newdiv = document.createElement( "div" );
    let newdivclass = 'alert-'+category;
    newdiv.classList.add('alert', newdivclass);
    let close = document.createElement( "a" );
    close.classList.add('close');
    close.setAttribute('title','Close');
    close.setAttribute('href','#');
    close.setAttribute('data-dismiss','alert');
    close.innerHTML = '&times;';
    newdiv.innerText = text;
    newdiv.appendChild(close);
    $('#flashed_messages').append(newdiv);
  }
}

function clear_flashed_messages() {
  $('#flashed_messages').empty();
}