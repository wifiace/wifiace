$(document).ready(function(){

    // init housekeeing.
    // this need for the popover to be placed properly.
    $('[data-toggle]').popover('show');
    $('[data-toggle]').popover('hide');

    //================ START SCAN
    // get result data for the table
    $('#start-scan').click(function(){
      console.log('#start-scan : CLICKED');

      var sec = $('#scan-time').val();

      console.log('sec : '+sec);

      // show loading
      $('#start-scan').popover('show');

      $.ajax({
        url: '/recon/start_scan',
        data: {sec:sec},
        type: 'GET',
        beforeSend: function(){
          console.log('#start-scan : Ajax request send.');

          $('#start-scan').attr('disabled', 'disabled');
          $('#scan-time').attr('disabled', 'disabled');

          // clearing the table initial before every new scan
          $('#scan-result tr').remove();
          $('#scan-result-unassociated tr').remove();

          // show loading
          $('#start-scan').popover('show');

          // fix for auto dismissing popover.
          setTimeout(function(){
              // show loading
              $('#start-scan').popover('show');
          }, 500);

        },
        complete: function(){
          console.log('#start-scan : Ajax response received.');

          $('#start-scan').removeAttr('disabled');
          $('#scan-time').removeAttr('disabled');

          $('#start-scan').popover('hide');

        },
        success: function(response){
          console.log('#start-scan : Ajax response SUCCESS.');

          // filling the result into the table
          $.each(response['result'], function(i, ap) {
            if (ap.bssid != '(not associated)'){
              if (ap.essid == '')ap_essid='<i class=text-primary>hidden</i>';
              else ap_essid = ap.essid;
              ap_essid = ap_essid + '<input type="hidden" name="ap_essid" value="{ap_essid}">'.formatUnicorn({ap_essid:ap.essid});
              ap_bssid = '<img src="/static/img/ic_router_black.png" alt="Router"> <button  type="button" class="btn btn-link" data-toggle="modal" data-target="#apModal">{ap_bssid}</button>'.formatUnicorn({ap_bssid:ap.bssid});
              $('<tr>').append(
                    $('<td>').html(ap_essid),
                    $('<td>').html(ap_bssid),
                    $('<td>').text(ap.channel),
                    $('<td>').text(ap.cipher),
                    $('<td>').text(ap.auth),
                    $('<td>').text(ap.power),

              ).appendTo('#scan-result');

              $.each(JSON.parse(ap.connected_clients), function(i, client) {
                  client_td = `
                    <button  type='button' class='btn btn-link' data-toggle='modal' data-target='#staModal'>{client_bssid}</button>
                    <input type='hidden' name='ap_bssid' value='{ap_bssid}'>
                    <input type='hidden' name='client_bssid' value='{client_bssid}'>
                    <input type='hidden' name='ap_channel' value='{ap_channel}'>
                    `;
                    client_td = client_td.formatUnicorn({client_bssid:client.mac, ap_bssid:ap.bssid, ap_channel:ap.channel});

                    $('<tr class="active">').append(
                    $('<td>').text(''),
                    $('<td>').html(client_td),
                    $('<td>').text(''),
                    $('<td>').text(''),
                    $('<td>').text(''),
                    $('<td>').text('')

                ).appendTo('#scan-result');

              });
            }else{
                $.each(JSON.parse(ap.connected_clients), function(i, client) {
                    $('<tr class="active">').append(
                    $('<td>').text(client.mac),
                    $('<td>').text(client.probed_essids)
                ).appendTo('#scan-result-unassociated');
                });
            }

          });
        },
        error: function(error){
          console.log('#start-scan : Ajax response ERROR.');
          console.log(error)
          // refreshing the pg.
          window.location = '/recon'
        }
      });

    });

    $('#ap-start-deauth').click( function(){
      console.log('#ap-start-deauth : CLICKED');

      var packets = $('#ap-deauth-packets').val().trim();
      var ap_bssid = $('#apModal').find('input[name=ap_bssid]').val().trim();
      var channel = $('#apModal').find('input[name=ap_channel]').val().trim();

      console.log({packets:packets, channel:channel, ap_bssid:ap_bssid});

      $.ajax({
      url: '/recon/start_deauth',
      data: {packets:packets, channel:channel, ap_bssid:ap_bssid},
      type: 'GET',
      success: function(response) {
          console.log('#ap-start-deauth : Ajax response SUCCESS : ' + ap_bssid);
          $('#ap-message').html('<div class="alert alert-success" role="alert">{message}</div>'.formatUnicorn({message:response['message']}));
      },
      error: function(error) {
          console.log('#ap-start-deauth : Ajax response ERROR');
          console.log(error);
          $('#ap-message').html('<div class="alert alert-warning" role="alert">{message}</div>'.formatUnicorn({message:error.responseJSON["message"]}));
      }
      });
    });

    $('#sta-start-deauth').click( function(){
      console.log('#sta-start-deauth : CLICKED');

      var packets = $('#sta-deauth-packets').val().trim();
      var ap_bssid = $('#staModal').find('input[name=ap_bssid]').val().trim();
      var channel = $('#staModal').find('input[name=ap_channel]').val().trim();
      var client_bssid = $('#staModal').find('input[name=client_bssid]').val().trim();

      console.log({packets:packets, channel:channel, ap_bssid:ap_bssid, client_bssid:client_bssid});

      $.ajax({
      url: '/recon/start_deauth',
      data: {packets:packets, channel:channel, ap_bssid:ap_bssid, client_bssid:client_bssid},
      type: 'GET',
      success: function(response) {
          console.log('#sta-start-deauth : Ajax response SUCCESS : ' + client_bssid);
          $('#sta-message').html('<div class="alert alert-success" role="alert">{message}</div>'.formatUnicorn({message:response['message']}));
      },
      error: function(error) {
          console.log('#sta-start-deauth : Ajax response ERROR');
          console.log(error);
          $('#sta-message').html('<div class="alert alert-warning" role="alert">{message}</div>'.formatUnicorn({message:error.responseJSON["message"]}));
      }
      });
    });

    $("#add-to-accept").click(function(){

      var client_bssid = $('#staModal').find('input[name=client_bssid]').val().trim();
      console.log(client_bssid);
      $.ajax({
      url: '/clients/add_to_filter',
      data: {file:'accept', mac:client_bssid},
      type: 'GET',

      success: function(response) {
        $('#sta-message').html('<div class="alert alert-success" role="alert">{message}</div>'.formatUnicorn({message:response['message']}));
        console.log(response);
      },
      error: function(error) {
          console.log(error);
          $('#sta-message').html('<div class="alert alert-warning" role="alert">{message}</div>'.formatUnicorn({message:error.responseJSON["message"]}));
      }
      });
    });

    $("#add-to-deny").click(function(){

      var client_bssid = $('#staModal').find('input[name=client_bssid]').val().trim();
      $.ajax({
      url: '/clients/add_to_filter',
      data: {file:'deny', mac:client_bssid},
      type: 'GET',

      success: function(response) {
        $('#sta-message').html('<div class="alert alert-success" role="alert">{message}</div>'.formatUnicorn({message:response['message']}));
        console.log(response);
      },
      error: function(error) {
          console.log(error);
          $('#sta-message').html('<div class="alert alert-warning" role="alert">{message}</div>'.formatUnicorn({message:error.responseJSON["message"]}));
      }
      });
    });

    //----------
    $('#apModal').on('show.bs.modal', function (event) {
      var button = $(event.relatedTarget);
      var ap_bssid = $(button).closest('tr').find('td:eq(1)').text();
      var channel = $(button).closest('tr').find('td:eq(2)').text();
      var tmptd = $(button).closest('tr').find('td:eq(0)');
      var ap_essid = $(tmptd).find('input[name=ap_essid]').val();
      var modal = $(this);
      modal.find('.modal-title').html( 'AP : ' + ap_bssid + '<small> @ ' + channel +'</small>');
      hidden_fields = `
      <input type='hidden' name='ap_bssid' value='{ap_bssid}'>
      <input type='hidden' name='ap_channel' value='{ap_channel}'>
      <input type='hidden' name='ap_essid' value='{ap_essid}'>
      `;

      hidden_fields =  hidden_fields.formatUnicorn({ap_bssid:ap_bssid, ap_channel:channel, ap_essid:ap_essid});
      $('#ap-hidden').html(hidden_fields);
    });

    $('#apModal').on('hidden.bs.modal', function(){
        $('#ap-message').html('');
        $('#ap-hidden').html('');
    });


    $('#staModal').on('show.bs.modal', function (event) {
      var button = $(event.relatedTarget);
      var client_bssid = $(button).closest('td').find('input[name=client_bssid]').val();
      var channel = $(button).closest('td').find('input[name=ap_channel]').val();
      var ap_bssid = $(button).closest('td').find('input[name=ap_bssid]').val();
      var modal = $(this);
      modal.find('.modal-title').html( 'STA : ' + client_bssid + '<small> @ ' + channel +'</small>');
      hidden_fields = `
      <input type='hidden' name='ap_bssid' value='{ap_bssid}'>
      <input type='hidden' name='ap_channel' value='{ap_channel}'>
      <input type='hidden' name='client_bssid' value='{client_bssid}'>
      `;
      hidden_fields = hidden_fields.formatUnicorn({ap_bssid:ap_bssid, ap_channel:channel, client_bssid:client_bssid});
      $('#sta-hidden').html(hidden_fields);
    });

    $('#staModal').on('hidden.bs.modal', function(){
        $('#sta-message').html('');
        $('#sta-hidden').html('');

    });


});
