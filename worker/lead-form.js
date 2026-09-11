/**
 * Frondworks lead-form handler — Cloudflare Worker.
 *
 * Free tier covers 100,000 requests/day, so this costs $0 at our volume.
 * The worker itself can't send email natively, so it fans out to:
 *   1. Discord webhook  -> instant lead alert on your phone (free, no new accounts)
 *   2. Resend API       -> email notification (free tier: 3,000 emails/mo, optional)
 *
 * Deploy (DNS is on Cloudflare, site on GitHub Pages):
 *   The contact form POSTs same-origin to frondworks.com/api/lead, which a
 *   Workers Route sends to this worker. (CORS headers are also present so the
 *   workers.dev URL keeps working as a fallback.)
 *   1. Deploy: python3 worker/deploy.py   (uses the stored Cloudflare credential)
 *   2. Set the Discord secret (dashboard: Workers & Pages -> frondworks-leads ->
 *      Settings -> Variables and Secrets -> add secret DISCORD_WEBHOOK_URL)
 *      Discord: Server Settings -> Integrations -> Webhooks -> New Webhook
 *   3. (optional) Add secrets RESEND_API_KEY and LEAD_EMAIL for email alerts.
 *      Resend "from" domain needs one DNS TXT record to verify frondworks.com.
 */

const MAX_LEN = 200;

// CORS: the contact form lives on frondworks.com and POSTs here via fetch.
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

function clean(v) {
  return (v ?? '').toString().trim().slice(0, MAX_LEN);
}

function validEmail(e) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e);
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json', ...CORS },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // CORS preflight for the contact form on frondworks.com.
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS });
    }

    if (url.pathname !== '/api/lead') {
      return new Response('Not found', { status: 404, headers: CORS });
    }
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    let data = {};
    try {
      const ct = request.headers.get('content-type') || '';
      if (ct.includes('application/json')) {
        data = await request.json();
      } else {
        const fd = await request.formData();
        data = Object.fromEntries(fd.entries());
      }
    } catch {
      return json({ ok: false, error: 'bad-request' }, 400);
    }

    // Honeypot: bots fill hidden fields; humans never see it.
    if (clean(data.company_website)) {
      return json({ ok: true }); // pretend success, drop silently
    }

    const lead = {
      name: clean(data.name),
      company: clean(data.company),
      phone: clean(data.phone),
      email: clean(data.email).toLowerCase(),
      website: clean(data.website),
      area: clean(data.area),
      trade: clean(data.trade),
      message: clean(data.message),
      at: new Date().toISOString(),
    };

    if (!lead.name || !lead.company || !validEmail(lead.email) || !lead.area) {
      return json({ ok: false, error: 'missing-fields' }, 400);
    }

    const tasks = [];

    // 1) Instant Discord alert — free, no email account needed.
    if (env.DISCORD_WEBHOOK_URL) {
      const fields = [
        { name: 'Name', value: lead.name, inline: true },
        { name: 'Company', value: lead.company, inline: true },
        { name: 'Trade', value: lead.trade || '—', inline: true },
        { name: 'Phone', value: lead.phone || '—', inline: true },
        { name: 'Email', value: lead.email, inline: true },
        { name: 'Service area', value: lead.area, inline: true },
        { name: 'Website', value: lead.website || '—', inline: true },
      ];
      if (lead.message) fields.push({ name: 'Notes', value: lead.message });
      tasks.push(
        fetch(env.DISCORD_WEBHOOK_URL, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({
            embeds: [
              {
                title: '🔧 New Maps audit request',
                color: 0xe8632a,
                fields,
                timestamp: lead.at,
              },
            ],
          }),
        }).catch(() => {})
      );
    }

    // 2) Email notification via Resend (optional).
    if (env.RESEND_API_KEY && env.LEAD_EMAIL) {
      tasks.push(
        fetch('https://api.resend.com/emails', {
          method: 'POST',
          headers: {
            authorization: `Bearer ${env.RESEND_API_KEY}`,
            'content-type': 'application/json',
          },
          body: JSON.stringify({
            from: 'Frondworks <leads@frondworks.com>',
            to: [env.LEAD_EMAIL],
            subject: `New audit request: ${lead.company}`,
            text: [
              `Name: ${lead.name}`,
              `Company: ${lead.company}`,
              `Trade: ${lead.trade || '—'}`,
              `Phone: ${lead.phone || '—'}`,
              `Email: ${lead.email}`,
              `Website: ${lead.website || '—'}`,
              `Service area: ${lead.area}`,
              `Notes: ${lead.message || '—'}`,
              `Received: ${lead.at}`,
            ].join('\n'),
          }),
        }).catch(() => {})
      );
    }

    await Promise.all(tasks);
    return json({ ok: true });
  },
};
