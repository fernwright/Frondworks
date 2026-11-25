// Frondworks: send the contact form with fetch so visitors stay on the page.
// Without JS the form still posts normally to /api/lead, but Turnstile needs JS.
// TURNSTILE_SITEKEY is filled after the widget is created; leave blank until then.
(function () {
  var TURNSTILE_SITEKEY = '0x4AAAAAAGRnXPNFpsu-YFxn';
  var form = document.getElementById('audit-form');
  if (!form) return;
  var started = document.getElementById('form_started');
  if (started && !started.value) started.value = String(Date.now());

  var widgetId;
  function renderTurnstile() {
    var el = document.getElementById('contact-turnstile');
    if (!el || !TURNSTILE_SITEKEY || !window.turnstile) return;
    if (widgetId !== undefined) return;
    widgetId = window.turnstile.render(el, {
      sitekey: TURNSTILE_SITEKEY,
      action: 'contact'
    });
  }
  window.onContactTurnstileLoad = renderTurnstile;
  renderTurnstile();

  if (!window.fetch) return;
  var status = document.getElementById('form-status');
  var btn = form.querySelector('button[type="submit"]');
  function show(msg) { if (status) status.textContent = msg; }
  function resetTurnstile() {
    if (widgetId !== undefined && window.turnstile) {
      window.turnstile.reset(widgetId);
    }
  }
  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    if (btn) btn.disabled = true;
    show('Sending...');
    fetch(form.getAttribute('action'), { method: 'POST', body: new FormData(form) })
      .then(function (r) { return r.json().then(function (d) { return { r: r, d: d }; }).catch(function () { return { r: r, d: {} }; }); })
      .then(function (res) {
        var d = res.d;
        if (d && d.ok) {
          form.innerHTML = '<p class="sent"><strong>Thanks, your message was sent.</strong> We will reply by email.</p>';
        } else if (d && d.error === 'missing-fields') {
          show('Please fill in your name, product or topic, email, and where you are based.');
          resetTurnstile();
          if (btn) btn.disabled = false;
        } else if (d && d.error === 'turnstile-failed') {
          show(d.message || 'Please complete the verification and try again.');
          resetTurnstile();
          if (btn) btn.disabled = false;
        } else { throw new Error('bad response'); }
      })
      .catch(function () {
        show('Something went wrong. Please email hello@frondworks.com instead.');
        resetTurnstile();
        if (btn) btn.disabled = false;
      });
  });
})();
