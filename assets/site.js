// Frondworks: send the contact form with fetch so visitors stay on the page.
// Without JS the form still posts normally to /api/lead.
(function () {
  var form = document.getElementById('audit-form');
  if (!form) return;
  var started = document.getElementById('form_started');
  if (started && !started.value) started.value = String(Date.now());
  if (!window.fetch) return;
  var status = document.getElementById('form-status');
  var btn = form.querySelector('button[type="submit"]');
  function show(msg) { if (status) status.textContent = msg; }
  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    if (btn) btn.disabled = true;
    show('Sending...');
    fetch(form.getAttribute('action'), { method: 'POST', body: new FormData(form) })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (d && d.ok) {
          form.innerHTML = '<p class="sent"><strong>Thanks, your message was sent.</strong> We will reply by email.</p>';
        } else if (d && d.error === 'missing-fields') {
          show('Please fill in your name, product or topic, email, and where you are based.');
          if (btn) btn.disabled = false;
        } else { throw new Error('bad response'); }
      })
      .catch(function () {
        show('Something went wrong. Please email hello@frondworks.com instead.');
        if (btn) btn.disabled = false;
      });
  });
})();
