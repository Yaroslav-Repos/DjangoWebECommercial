(function(){
  document.addEventListener('click', function(e){
    var btn = e.target.closest('.add-to-cart-btn');
    if (!btn) return;
    e.preventDefault();
    var form = btn.closest('form');
    if (!form) return;
    var data = new FormData(form);
    fetch(form.action, { method: 'POST', body: data, headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function(r){ return r.json(); })
      .then(function(js){
        if (js.ok) {
          // show simple toast
          var t = document.createElement('div'); t.className='toast'; t.innerText='Added to cart'; document.body.appendChild(t);
          setTimeout(function(){ t.remove(); }, 2000);
        } else {
          alert('Error adding to cart');
        }
      }).catch(function(){ alert('Network error'); });
  });
})();
