(function($){
  $(function(){
    $('.catalog-toggle').on('click', function(){
      $('.catalog-drawer').toggle();
    });
    // AJAX load children on hover (desktop) or click (mobile)
    $('.catalog-tree > li > a').on('mouseenter click', function(e){
      var href = $(this).attr('href') || '';
      var parts = href.split('/').filter(Boolean);
      var slug = parts.length ? parts.pop() : '';
      if (!slug) return;
      var $li = $(this).closest('li');
      if ($li.data('loaded')) return;
      $.get('/ajax/subcategories/'+slug+'/', function(data){
        if (data.children && data.children.length) {
          var ul = $('<ul class="submenu"/>');
          data.children.forEach(function(ch){
            ul.append('<li><a href="/category/'+ch.slug+'/">'+ch.name+'</a></li>');
          });
          $li.append(ul);
          $li.data('loaded', true);
        }
        // if products returned, append preview area
        if (data.products && data.products.length) {
          var preview = $('<div class="mega-preview"/>');
          data.products.forEach(function(p){
            var el = $('<div class="preview-item"/>');
            el.append('<a href="/product/'+p.slug+'/">' + (p.image? '<img src="'+p.image+'" style="width:80px;height:80px;object-fit:cover;"/>':'' ) + '<div>'+p.name+'</div><div>'+p.price+'</div></a>');
            preview.append(el);
          });
          $li.append(preview);
        }
      });
    });
    // keep dropdown-submenu behavior from prior script
    $(document).on('click', '.dropdown-submenu > a', function(e){
      var $submenu = $(this).next('.dropdown-menu');
      if ($submenu.length) {
        e.preventDefault();
        e.stopPropagation();
        $('.dropdown-submenu .dropdown-menu').not($submenu).hide();
        $submenu.toggle();
      }
    });
    // infinite scroll/load more handler placeholder: handled per-page via inline script
  });
})(jQuery);
