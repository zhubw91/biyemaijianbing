$(document).ready(function () {
        var scntDiv = $('#p_scents');
        var i = $('#p_scents p').size() + 1;
        $('#addScnt').click(function() {
                if(i <= 10) 
                {
                        scntDiv.append('<p><input type="text" class="p_scnt" size="20" name="choice' + i +'" value=""/><a href="#">Remove</a></p>');
                        i++;
                        j = 1
                        scntDiv.children().each(function() {
                                $(this).children(".p_scnt").attr('name','choice'+j);
                                j++;
                        });
                        return false;
                }
        });
        
        $('#p_scents').click(function() { 
                if( $(event.target).is('a') && i > 3 ) {
                        $(event.target).parents('p').remove();
                        i--;
                }
                 return false;
        });
});
