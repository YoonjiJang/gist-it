$(function(){
    $( '#try-it' ).click(function(){
        $( '#try-it-modal' ).modal( 'show' );
        return false;
    });

    $modal = $( '#try-it-modal' );
    $input = $modal.find('input');
    $script = $modal.find('.script');
    $output = $modal.find('.output');

    $modal.find('form').on('submit', function(e){
      event.preventDefault();
        load();
    });
    $modal.bind('show', function(){
        if (!$output.children().length) {
            load();
        }
    });
    $modal.bind('shown', function(){
        $input.focus().select();
    });

    function load(){
        var url = $input.val();
        $output.text("");
        if (url === "") {
            $output.addClass('alert alert-warning').text("Enter a GitHub URL");
            return;
        }
        var regex = /^https?\:\/\/(www\.)?github.com\/(.+)$/i;
        url = GIST_IT_BASE + '/github/' + regex.exec(url)[2];
        $script.empty().append(
            $( '<pre class="prettyprint lang-html" />' ).text('<script src="' + url + '">\n</script>')
        );
        $output.removeClass('alert alert-warning alert-error').text("Loading...");
        prettyPrint();
        $.getJSON(url, { 'test': 'json' }, function(data){
            $output.html(data.html);
            prettyPrint();
        }).error(function(response){
            $output.addClass('alert alert-error').text(response.responseText);
        });
    }
});
