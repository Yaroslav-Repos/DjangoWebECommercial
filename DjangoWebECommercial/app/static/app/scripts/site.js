(function($){
  $(function(){
    $('.catalog-toggle').on('click', function(){
      var drawer = $('.catalog-drawer');
      drawer.toggle();
      $(this).attr('aria-expanded', drawer.is(':visible'));
    });

    $('.catalog-tree').on('mouseenter focusin', '[data-menu-category]', function(){
      var item = $(this).closest('li');
      if (item.data('loaded') || item.data('loading')) {
        return;
      }

      item.data('loading', true);
      $.getJSON(item.data('subcategories-url'))
        .done(function(data) {
          var submenu = item.children('.submenu');
          $.each(data.children || [], function(_, child) {
            $('<li>').append(
              $('<a>', {
                href: '/category/' + encodeURIComponent(child.slug) + '/',
                text: child.name
              })
            ).appendTo(submenu);
          });
          if (data.children && data.children.length) {
            submenu.removeAttr('hidden');
          } else {
            submenu.remove();
          }
          item.data('loaded', true);
        })
        .always(function() {
          item.data('loading', false);
        });
    });
  });
})(jQuery);
