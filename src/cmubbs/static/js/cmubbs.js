function delete_confirmation(url, del_item){
  var confirm_msg = "";
  if (del_item == "topic"){
    confirm_msg = "Are you sure to delete this topic ?"
  }else if (del_item == "father_forum"){
    confirm_msg = "Are you sure to delete this forum, including all its subforums ?"
  }else if (del_item == 'sub_forum'){
    confirm_msg = "Are you sure to delete this forum?"
  }else if (del_item == "moderator"){
    confirm_msg = "Are you sure to delete this moderator?"
  }else if (del_item == "participant"){
    confirm_msg = "Are you sure to delete this participant?"
  }
  bootbox.confirm(confirm_msg, function(result) {
    if(result == true){
      $.get(url)
        .done(function(data){
          location.reload();
        });
    }
  }); 
}

function checkAllForums(){
  var forums = document.getElementsByName("optionsForums");
  for (fi in forums){
    forums[fi].checked=false;
  }
  var sub_forums = document.getElementsByClassName("sub-forum-tag");
  for (sub_fi in sub_forums){
    if (sub_forums[sub_fi].style){
      sub_forums[sub_fi].style.display = 'none';
    }
  }
}

function checkFatherForums(e){
  document.getElementById("all_forums").checked = false;
  e = e || window.event;
  var target = e.target || e.srcElement;
  var sub_forum = target.parentNode.nextSibling.nextSibling.childNodes;

  for (child in sub_forum){
    if(typeof sub_forum[child].style === 'undefined'){
      continue;
    }
    sub_forum[child].style.display = target.checked?'':'none';
    sub_forum[child].childNodes[1].checked=false;
  }
}

function checkSubForums(e){
  e = e || window.event;
  var target = e.target || e.srcElement;
  target.parentNode.parentNode.parentNode.childNodes[1].childNodes[1].checked=false;
}

function checkAllTags(){
  var tags = document.getElementsByName("optionsTags");
  for (ti in tags){
    tags[ti].checked=false;
  }
}

function uncheckAllTags(){
  document.getElementById("all_tags").checked = false;
}

function favoriteForum(url) {
    $.get(url)
    .done(function(data) {
       $("#favorite-forum-btn").css('display','none');
       $("#dislike-forum-btn").css('display','');
    });
}

function dislikeForum(url) {
    $.get(url)
    .done(function(data) {
       $("#dislike-forum-btn").css('display','none');
       $("#favorite-forum-btn").css('display','');
    });
}

function likeTopic(url) {
    $.get(url)
    .done(function(data) {
       $("#liked-topic-btn").css('display','');
       $("#like-topic-btn").css('display','none');
    });
}

function dislikeTopic(url) {
    $.get(url)
    .done(function(data) {
       $("#liked-topic-btn").css('display','none');
       $("#like-topic-btn").css('display','');
    });
}

function rsvpEvent(url) {
  $.get(url)
  .done(function(data) {
    if (data['rsvp_successful']){
      alert("RSVP successful.");
      $("#undo-rsvp-btn").css('display','');
      $("#rsvp-btn").css('display','none');
    } else {
      alert("RSVP failed.");
    }
    location.reload();
  });
}

function undoRsvpEvent(url) {
  $.get(url)
  .done(function(data) {
    if (data['undo_rsvp_successful']){
      alert("Undo RSVP successful.");
      $("#rsvp-btn").css('display','');
      $("#undo-rsvp-btn").css('display','none');
    } else {
      alert("Undo RSVP failed.");
    }
    location.reload();
  });
}

function dropOutEvent(url) {
  $.get(url)
  .done(function(data) {
    if (data['undo_rsvp_successful']){
      alert("Drop out event successful.");
      $("#apply-event-btn").css('display','');
      $("#drop-out-btn").css('display','none');
    } else {
      alert("Drop out event failed.");
    }
    location.reload();
  });
}

function upTopic(url) {
    $.get(url)
    .done(function(data) {
       $("#down-topic-btn").css('display','');
       $("#up-topic-btn").css('display','none');
    });
}

function downTopic(url) {
    $.get(url)
    .done(function(data) {
       $("#down-topic-btn").css('display','none');
       $("#up-topic-btn").css('display','');
    });
}

function goodTopic(url) {
    $.get(url)
    .done(function(data) {
       $("#normal-topic-btn").css('display','');
       $("#good-topic-btn").css('display','none');
    });
}

function normalTopic(url) {
    $.get(url)
    .done(function(data) {
       $("#normal-topic-btn").css('display','none');
       $("#good-topic-btn").css('display','');
    });
}

function removeNotification(url) {
  $.get(url);
}

function getNotifications(url) {
    if ($('input:hidden[name=islogin]').val() == 'no') {
        $("#notify-badge").css('display','none');
        $("#notification-dropdown").html("<li>No notifications</li>");
    }
    else {
      var notify = $("#notify-badge")
      var list = $("#notification-dropdown");
      $.get(url)
      .done(function(data) {
        if (data['unread'].length == 0) {
          notify.css('display','none');
          list.html("<li>No notifications</li>");
        }
        else {
          list.html('');
          for (var i = 0; i < data['unread'].length; i++) {
            if( data['unread'][i]['type'] == 'message')
            {
              list.append("<li><a href='" + data['unread'][i]['url'] +  "'>You have new messages from <b>" + data['unread'][i]['text'] + "</b></a></li>");
            }
            else if( data['unread'][i]['type'] == 'reply-replypost' || data['unread'][i]['type'] == 'reply')
            {
              list.append("<li><a href='" + data['unread'][i]['url'] +  "' onclick=removeNotification('" + data['unread'][i]['id'] + "')>Your post in topic <b>" + data['unread'][i]['text'] + "</b> has a new reply.</a></li>");
            }
            else if( data['unread'][i]['type'] == 'reply-newpost' )
            {
              list.append("<li><a href='" + data['unread'][i]['url'] +  "' onclick=removeNotification('" + data['unread'][i]['id'] + "')>Your topic <b>" + data['unread'][i]['text'] + "</b> has a new post.</a></li>");
            }
            else if( data['unread'][i]['type'] == 'reply-likepost' )
            {
              list.append("<li><a href='" + data['unread'][i]['url'] +  "' onclick=removeNotification('" + data['unread'][i]['id'] + "')>Your favorite topic <b>" + data['unread'][i]['text'] + "</b> has a new post.</a></li>");
            }
            else if( data['unread'][i]['type'] == 'follow' )
            {
              list.append("<li><a href='" + data['unread'][i]['url'] +  "' onclick=removeNotification('" + data['unread'][i]['id'] + "')>You have a new follower <b>" + data['unread'][i]['text'] + "</b></a></li>");
            }
            else if( data['unread'][i]['type'] == 'moderator-add' )
            {

                list.append("<li><a href='" + data['unread'][i]['url'] +  "' onclick=removeNotification('" + data['unread'][i]['id'] + "')>You are now the moderator for forum <b>" + data['unread'][i]['text'] + "</b></a></li>");
              
            }
            else if( data['unread'][i]['type'] == 'moderator-remove' )
            {

                list.append("<li><a href='" + data['unread'][i]['url'] +  "' onclick=removeNotification('" + data['unread'][i]['id'] + "')>You have been removed from the moderators of forum <b>" + data['unread'][i]['text'] + "</b></a></li>");
       
            }
            else if( data['unread'][i]['type'] == 'event_app' )
            {
              list.append("<li><a href='" + data['unread'][i]['url'] +  "' onclick=removeNotification('" + data['unread'][i]['id'] + "')>You have a new event application for <b>" + data['unread'][i]['text'] + "</b></a></li>");
            }
            else if( data['unread'][i]['type'] == 'event_add' )
            {
              list.append("<li><a href='" + data['unread'][i]['url'] +  "' onclick=removeNotification('" + data['unread'][i]['id'] + "')>You are added to an event <b>" + data['unread'][i]['text'] + "</b></a></li>");
            }
            else if( data['unread'][i]['type'] == 'event_del' )
            {
              list.append("<li><a href='" + data['unread'][i]['url'] +  "' onclick=removeNotification('" + data['unread'][i]['id'] + "')>You are deleted from an event <b>" + data['unread'][i]['text'] + "</b></a></li>");
            }
            else {
              console.log(data);
            }

          }
          notify.css('display','');
          notify.html(data['unread'].length);
        }
        
      });

    }
    
}

$(document).ready(function () {
  var $loginForm = $('#login-form');
  var $registerForm = $('#register-form');
  var $authForms = $('#auth-forms');
  var $formChangeTime = 300;

  var notificationurl = $('#notification-url').val();
  getNotifications(notificationurl);

  window.setInterval(function(){ getNotifications(notificationurl); }, 5000);

  $('[data-toggle="tooltip"]').tooltip(); 
  $('[data-toggle="tooltip"]').tooltip().click( function () {
    $(this).blur(); 
  }); 

  $('#login-form').submit(function(){
      $.post($(this).attr('action'), $(this).serialize())
        .done(function(data) {
          if (data["login_successful"]) {
            $("#text-login-msg").html("Login successful.");
            location.reload();
          } else {
            console.log(data);
              $("#text-login-msg").html("Incorrect user name or password.");
          }

        });
      return false;
  });
  $('#register-form').submit(function(){
      $.post($(this).attr('action'), $(this).serialize())
        .done(function(data) {
          if (data["register_successful"]) {
            $("#text-register-msg").html("Register successful.");
            location.reload();
          } else {
              $("#text-register-msg").html(data["html"]);
                var $newH = $registerForm.height();
                $authForms.css("height",$newH);
          }

        });
      return false;
  });

  $('#add-participant-form').submit(function(){
      $.post($(this).attr('action'), $(this).serialize())
        .done(function(data) {
          if (data["successful"]) {
            location.reload();
          } else {
              $("#participant-form-div").html(data["html"]);
          }
        });
      return false;
  });

  $('#logout-btn').click(function(){
    $.get($(this).attr('href'))
        .done(function() {
          location.reload();

        });
      return false;
  });

  $('#login-register-btn').click( function () { changeForm($loginForm, $registerForm); });
    $('#register-login-btn').click( function () { changeForm($registerForm, $loginForm); });

    function changeForm ($oldForm, $newForm) {
        var $oldH = $oldForm.height();
        var $newH = $newForm.height();
        $authForms.css("height",$oldH);
        $oldForm.fadeToggle($formChangeTime, function(){
            $authForms.animate({height: $newH}, $formChangeTime, function(){
                $newForm.fadeToggle($formChangeTime);
            });
        });
    }   
    
    $('.edit-background').each(function(){$(this).css("height",$(this).next().css("height"))})
    $('.edit-background').each(function(){$(this).css("width",$(this).next().css("width"))})
    $('.edit-background').each(function(){$(this).css("padding",$(this).next().css("padding"))})
    $('.edit-background').each(function(){$(this).css("margin",$(this).next().css("margin"))})


});