var maxImgCnt = 5;

function add_image(){
  var ul = document.getElementById("image_list");
  var imgCnt = $('#image_list ul').size();
  if (imgCnt < maxImgCnt) {
    var li = document.createElement("li");

    // another ul to put input file an ddel into one line
    var in_ul = document.createElement("ul");
    in_ul.setAttribute("class","forum-info");

    // input li
    var input_li = document.createElement("li");
    var new_input = document.createElement("INPUT");
    new_input.setAttribute("type", "file");
    new_input.setAttribute("name", "up_image_list");
    new_input.setAttribute("accept", ".png, .jpg, .jpeg, .gif");
    input_li.appendChild(new_input);
    in_ul.appendChild(input_li);

    // del li
    var del_li = document.createElement("li");
    var del_link = document.createElement('a');
    var del_t = document.createTextNode("del");  
    del_link.setAttribute('class','del-img')
    del_link.appendChild(del_t); 
    del_link.addEventListener('click', function(){
    	this.parentNode.parentNode.parentNode.parentNode.removeChild(this.parentNode.parentNode.parentNode);
  	});
    del_li.appendChild(del_link);
    in_ul.appendChild(del_li);

    li.appendChild(in_ul);
    ul.appendChild(li);
  }
}

function change_plain_text(){
  var plain_text_btn = document.getElementById('plain-text-checked');
  plain_text_btn.checked = plain_text_btn.checked ? false: true;
  var plain_text_div = document.getElementById('plain-text-div');
  var preview_btn = document.getElementById('preview-btn');
  var font_tag_btn = document.getElementsByName('font-tag-btn');
  if (plain_text_btn.checked == true){
    if (plain_text_div.title == 'reply-topic'){
      plain_text_div.setAttribute('class','btn btn-primary btn-text-font-plain');
    }else if(plain_text_div.title == 'post-topic'){
      plain_text_div.setAttribute('class','btn btn-primary btn-font-plain space-left');
    }
    preview_btn.setAttribute("disabled",true);
    preview_btn.setAttribute("data-target","");
    for( font_tag in font_tag_btn ){
      font_tag_btn[font_tag].setAttribute("style","display:none");
    }
  }else{
    if (plain_text_div.title == 'reply-topic'){
      plain_text_div.setAttribute('class','btn btn-primary btn-text-font');
    }else if(plain_text_div.title == 'post-topic'){
      plain_text_div.setAttribute('class','btn btn-primary btn-font space-left');
    }
    preview_btn.removeAttribute("disabled");
    preview_btn.setAttribute("data-target","#preview-post-modal");
    for( font_tag in font_tag_btn ){
      font_tag_btn[font_tag].removeAttribute("style");
    }
  }
}


function text_font(tag_name, ele_id){
  var test_body = document.getElementById(ele_id);
  var start = test_body.selectionStart;
  var finish = test_body.selectionEnd;
  if(finish > start){
    test_body.value = test_body.value.substring(0, start) + change_text(tag_name, test_body.value.substring(start, finish))+ test_body.value.substring(finish);
  }else{
    test_body.value = change_text(tag_name,test_body.value)
  }
  var sel = test_body.value.substring(start, finish);
}

function change_text(tag_name, text){
  return "<"+tag_name+">"+text+"</"+tag_name+">"
}


$(document).ready(function () {
  $('a[data-target=#comment-modal]').click(function () {
    var myNameId = $(this).data('id');
    $("#postId").val( myNameId );
  });

  $('a[data-target=#preview-post-modal]').click(function () {
    var url = $(this).data('url');
    var post_text = document.getElementById($(this).data('text-id')).value;
    $.post(url, {post_text: post_text})
      .done(function(data) {
        document.getElementById("post-font-text").innerHTML = data['post_text'];
      })
  });

  function getCookie(name) {  
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
  }
  var csrftoken = getCookie('csrftoken');
  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  });

}); 


