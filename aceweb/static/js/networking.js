function genMAC(){
    var hexDigits = "0123456789ABCDEF";
    var macAddress = "";
    for (var i = 0; i < 6; i++) {
        var num = ""
        num+=hexDigits.charAt(Math.round(Math.random() * 15));
        num+=hexDigits.charAt(Math.round(Math.random() * 15));

        if (i==0){
          num = (parseInt(num, 16) & 254) | 2;
          num = num.toString(16);
          num = num.toUpperCase();
        }

        macAddress+=num;

        if (i != 5) macAddress += ":";
    }

    return macAddress;
}

$("document").ready(function(){
  // toggle status enable/disable interfaces.
  $(".toggle-istatus").click(function(){
    // get current status of the button.
    var istatus = $(this).val();
    // get the interface name form the same row (0) column.
    var iface_name = $(this).closest('tr').find('td:eq(0)').text();
    // get the url to redirect to.
    var redirect_url = "/networking"

    if(istatus == "up"){
        redirect_url = redirect_url+"/disable_interface";
    }else{
        redirect_url = redirect_url+"/enable_interface";
    }

    // redirect to the given url
    window.location = redirect_url+"?name="+iface_name;
  });

  // toogle inused add revert virtual monitor mode interfaces.
  $(".toggle-inused").click(function(){
    // get current status of the button.
    var istatus = $(this).val();
    // get the interface name form the same row (0) column.
    var iface_name = $(this).closest('tr').find('td:eq(0)').text();
    // get the url to redirect to.
    var redirect_url = "/networking"

    if(istatus == "True"){
        redirect_url = redirect_url+"/revert_virtual_interface";
    }else{
        redirect_url = redirect_url+"/create_virtual_interface";
    }

    // redirect to the given url
    window.location = redirect_url+"?name="+iface_name;
  });

  // set priority for loaded devices
  $('input[type=radio][name=priority-options]').change(function() {
      // get current status of the button.
      var istatus = $(this).val();
      // get the interface name form the same row (0) column.
      var iface_name = $(this).closest('tr').find('td:eq(0)').text();
      // get the url to redirect to.
      var priority_to_set = $(this).val();

      // redirect to the given url
      var redirect_url = "/networking/set_priority";

      window.location = redirect_url+"?name="+iface_name+"&priority="+priority_to_set;

  });

  // toogle inused add revert virtual monitor mode interfaces.
  $("#rfkill-unblock").click(function(){
    // redirect url.
    var redirect_url = document.URL + "rfkill_unblock"
    // redirect to the given url
    window.location = redirect_url;
  });


  $('#macChangerModel').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget);
    var iface = $(button).closest('tr').find('td:eq(0)').text();
    var modal = $(this);
    modal.find('.modal-title').text(iface);
    $('#mac-text').val(button.text());
  });

  $('#macChangerModel').on('hidden.bs.modal', function(){
    $('#mac-model-msg').html('');
    window.location = '/networking/'
  });

  $('#get-random-mac').click(function(){
    $('#mac-text').val(genMAC());
  });

  $('#save-mac').click(function(){
    var iface = $('#macChangerModel').find('.modal-title').text();
    var mac = $('#mac-text').val();

    $.ajax({
    url: '/networking/change_mac',
    data: {iface:iface, mac:mac},
    type: 'GET',

    success: function(response) {
      $('#mac-model-msg').html('<div class="alert alert-success" role="alert">{message}</div>'.formatUnicorn({message:response['message']}));
        console.log(response);
    },
    error: function(error) {
      $('#mac-model-msg').html('<div class="alert alert-warning" role="alert">{message}</div>'.formatUnicorn({message:error.responseJSON["message"]}));
        console.log(error);
    }
    });

  });

  $('#restore-mac').click(function(){
    var iface = $('#macChangerModel').find('.modal-title').text();

    $.ajax({
    url: '/networking/restore_mac',
    data: {iface:iface},
    type: 'GET',

    success: function(response) {
      $('#mac-model-msg').html('<div class="alert alert-success" role="alert">{message}</div>'.formatUnicorn({message:response['message']}));
        console.log(response);
    },
    error: function(error) {
      $('#mac-model-msg').html('<div class="alert alert-warning" role="alert">{message}</div>'.formatUnicorn({message:error.responseJSON["message"]}));
        console.log(error);
    }
    });

  });


});
