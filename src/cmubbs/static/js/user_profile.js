function unfollow(url){
  $.get(url)
    .done(function(data) {
       $("#unfollow-btn").css('display','none');
       $("#follow-btn").css('display','');
       var num_followers = parseInt($("#num_followers").text());
       $("#num_followers a").text(num_followers-1);
    });
}

function follow(url){
    $.get(url)
    .done(function(data) {
       $("#unfollow-btn").css('display','');
       $("#follow-btn").css('display','none');
       var num_followers = parseInt($("#num_followers").text());
       $("#num_followers a").text(num_followers+1);
    });
}


function acceptApplication(url, next_url) {
  $.get(url)
  .done(function(data) {
    if(data['successful']){
      profileSidebar(next_url);
    }
  });
}

function declineApplication(url, next_url) {
  $.get(url)
  .done(function(data) {
    if(data['successful']){
      profileSidebar(next_url);
    }
  });
}

$(document).on('click', '.nav li', function() {
  $(".nav li").removeClass("active");
  $(this).addClass("active");
});

function gotoPage(url) {
  window.location.hash = window.location.hash.split('?')[0] + '?page='+ $('#page-selector').val()
  profileSidebar(url + '?page=' + $('#page-selector').val());
}

function profileSidebar(url) {
  $.get(url)
  .done(function(data) {
    $("#profile-content").html(data['html']);
    $('#edit-form').submit(function(){
      $.post($(this).attr('action'), $(this).serialize())
        .done(function(data) {
          profileSidebar($('#userinfo-url').val());
          $(".nav li").removeClass("active");
          $("#about-nav").addClass("active");
        });
      return false;
    });
  }).fail(function(data){
    $("#profile-content").html(data['responseText'] );
  });
}

$( document ).ready(function(){
  var para = '';
  if (window.location.hash.split('?').length > 1) {
    para = '?' + window.location.hash.split('?')[1];
  }
  
  if (window.location.hash.startsWith('#event_applications') && $('#event-applications-url').length > 0) {
    profileSidebar($('#event-applications-url').val() + para);
  } else if (window.location.hash.startsWith('#events')) {
    profileSidebar($('#events-url').val() + para);
  } else if (window.location.hash.startsWith('#participating_events')) {
    profileSidebar($('#participating-events-url').val() + para);
  } else if (window.location.hash.startsWith('#collections')) {
    profileSidebar($('#collections-url').val() + para);
  } else if (window.location.hash.startsWith('#edit_profile') && $('#edit-profile-url').length > 0) {
    profileSidebar($('#edit-profile-url').val() + para);
  } else if (window.location.hash.startsWith('#self_topics')) {
    profileSidebar($('#self-topics-url').val() + para);
  } else if (window.location.hash.startsWith('#activities')) {
    profileSidebar($('#activities-url').val() + para);
  } else {
    profileSidebar($('#userinfo-url').val() + para);
  }
});