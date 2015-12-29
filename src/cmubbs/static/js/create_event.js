var useBtn = "<br><a type='button' class='button' data-dismiss='modal' onClick='updateAddress()''>Use this address</a>"

function updateAddress(){
  $("#id_formatted_address").val(place.formatted_address);
  $('#lat').val(place.geometry.location.lat());
  $('#lng').val(place.geometry.location.lng());
}

$(document).ready(function () {

	initMap(useBtn);
	$("#map-modal").on("shown.bs.modal", function(e) {
		google.maps.event.trigger(map, "resize");
		if (place && place.geometry) {
			map.setCenter(place.geometry.location);
		} else {
			map.setCenter(default_location);
		}	
	});
});
