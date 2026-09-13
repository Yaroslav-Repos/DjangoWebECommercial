(function($){
  $(function(){
    $('.catalog-toggle').on('click', function(){
      var drawer = $('.catalog-drawer');
      drawer.toggle();
      $(this).attr('aria-expanded', drawer.is(':visible'));
    });
  });
})(jQuery);
