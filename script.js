// Frondworks archived pages (plumbers.html): close the mobile nav when a link is tapped.
(function () {
  var nav = document.querySelector('.nav-links');
  if (nav) {
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') nav.classList.remove('open');
    });
  }
})();
