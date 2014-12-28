$(function(){
    // alert('loc.js')
    
    $('select[name$=-at]').live('change', function(ev){
        console.log('changed');
    });
    
    $('.add-row a').live('click', function(ev){
        console.log('added');
    });
})
