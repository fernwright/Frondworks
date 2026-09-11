// Frondworks — minimal progressive enhancement.
// 1. Close the mobile nav when a link is tapped.
// 2. Intercept the placeholder contact form so it doesn't navigate anywhere
//    until it's wired to a real form service.

(function () {
  // Close mobile menu on link click
  var nav = document.querySelector('.nav-links');
  if (nav) {
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') nav.classList.remove('open');
    });
  }

  // Lead form: POSTs to the Cloudflare Worker at /api/lead.
  // If the worker isn't deployed yet (or the request fails), fall back
  // to asking the visitor to email directly — never a dead end.
  var form = document.getElementById('audit-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var status = document.getElementById('form-status');
      var btn = form.querySelector('button[type="submit"]');
      function show(msg) {
        if (status) {
          status.style.display = 'block';
          status.textContent = msg;
        }
      }
      if (btn) btn.disabled = true;
      show('Sending…');
      fetch(form.getAttribute('action'), { method: 'POST', body: new FormData(form) })
        .then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function (d) {
          if (d && d.ok) {
            form.innerHTML = '<div style="padding:24px 0"><h3>Request received.</h3><p>We\u2019ll pull your Google Maps audit and reply within one business day.</p></div>';
          } else if (d && d.error === 'missing-fields') {
            show('Please fill in your name, company, email, and service area.');
            if (btn) btn.disabled = false;
          } else {
            throw new Error('bad response');
          }
        })
        .catch(function () {
          show('Something went wrong sending that \u2014 please email hello@frondworks.com directly and we\u2019ll take it from there.');
          if (btn) btn.disabled = false;
        });
    });
  }
})();
