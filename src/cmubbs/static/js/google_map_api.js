var map;
var mc;
var place;
var default_location = {lat: 40.4433, lng: -79.9436};

function loadEvents() {
  $.get($('#load-events-url').val())
  .done(function(data){
    for (var i = 0; i < data['events'].length; i++) {
      var eventi = data['events'][i];
      var location = new google.maps.LatLng(eventi.lat, eventi.lng);
      var marker = new google.maps.Marker({  
          position: location,  
          map: map
      });
      var content = eventi.map_html;
      marker.setValues({'event_info':content});
      mc.addMarker(marker);
      (function (marker, eventi) {  
              google.maps.event.addListener(marker, "click", function (e) {  

                  var infowindow = new google.maps.InfoWindow({
                   content: eventi.map_html
                  });

                  infowindow.open(map, marker);
              });  
          })(marker, eventi);  

    }
  });
}

// This function Refers to example code in google maps api: https://developers.google.com/maps/documentation/javascript/examples/places-autocomplete
function initMap(infoSuffix) {
  if (typeof infoSuffix === "undefined" || infoSuffix === null) { 
    infoSuffix = ""; 
  }
  var mapOptions = {
   zoom: 16,
   maxZoom: 18,
   center: default_location,
   mapTypeId: google.maps.MapTypeId.ROADMAP
  };
  map = new google.maps.Map($("#map_inforum")[0], mapOptions);
  mc = new MarkerClusterer(map,[],{'zoomOnClick':false});
  $('#search-div').css('width','300px');
  cur_query =  $("#google_address").val();
  var query_address = $("#google_address")[0];
  map.controls[google.maps.ControlPosition.TOP_LEFT].push($("#search-div")[0]);
  if ($("#close-btn").length > 0 ){
    map.controls[google.maps.ControlPosition.TOP_RIGHT].push($("#close-btn")[0]);
  }
  var autocomplete = new google.maps.places.Autocomplete(query_address);
  autocomplete.bindTo('bounds', map);
  var infowindow = new google.maps.InfoWindow();
  var marker = new google.maps.Marker({
    map: map,
  });
  
  autocomplete.addListener('place_changed', function() {
    infowindow.close();
    marker.setVisible(false);
    place = autocomplete.getPlace();
    if (!place.geometry) {
      window.alert("Invalid address.");
      $("#google_address").val('');
      cur_query =  $("#google_address").val();
      return;
    }
    cur_query =  $("#google_address").val();

    if (place.geometry.viewport) {
      map.fitBounds(place.geometry.viewport);
    } else {
      map.setCenter(place.geometry.location);
    }
    marker.setIcon(({
      url: place.icon,
      size: new google.maps.Size(71, 71),
      origin: new google.maps.Point(0, 0),
      anchor: new google.maps.Point(17, 34),
      scaledSize: new google.maps.Size(35, 35)
    }));
    marker.setPosition(place.geometry.location);
    marker.setVisible(true);
    var address = '';
    if (place.address_components) {
      address = [
        (place.address_components[0] && place.address_components[0].short_name || ''),
        (place.address_components[1] && place.address_components[1].short_name || ''),
        (place.address_components[2] && place.address_components[2].short_name || '')
      ].join(' ');
    }

    infowindow.setContent('<div><strong>' + place.name + '</strong><br>' + address + infoSuffix);
    infowindow.open(map, marker);
  });
}

