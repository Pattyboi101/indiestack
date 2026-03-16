(function() {
  'use strict';

  // Map SaaS domains to IndieStack search queries
  const SAAS_MAP = {
    'analytics.google.com': { query: 'analytics', name: 'Google Analytics' },
    'google.com/analytics': { query: 'analytics', name: 'Google Analytics' },
    'mailchimp.com': { query: 'email marketing', name: 'Mailchimp' },
    'zendesk.com': { query: 'customer support', name: 'Zendesk' },
    'intercom.com': { query: 'customer support', name: 'Intercom' },
    'hubspot.com': { query: 'crm', name: 'HubSpot' },
    'salesforce.com': { query: 'crm', name: 'Salesforce' },
    'mixpanel.com': { query: 'analytics', name: 'Mixpanel' },
    'amplitude.com': { query: 'analytics', name: 'Amplitude' },
    'datadog.com': { query: 'monitoring', name: 'Datadog' },
    'auth0.com': { query: 'auth', name: 'Auth0' },
    'typeform.com': { query: 'forms', name: 'Typeform' },
    'calendly.com': { query: 'scheduling', name: 'Calendly' },
    'stripe.com': { query: 'payments', name: 'Stripe' },
    'figma.com': { query: 'design', name: 'Figma' },
    'notion.so': { query: 'project management', name: 'Notion' },
    'airtable.com': { query: 'project management', name: 'Airtable' },
    'sendgrid.com': { query: 'email', name: 'SendGrid' },
    'twilio.com': { query: 'api tools', name: 'Twilio' },
    'hotjar.com': { query: 'feedback', name: 'Hotjar' },
    'freshdesk.com': { query: 'customer support', name: 'Freshdesk' },
  };

  // Find which SaaS we're on
  const host = window.location.hostname.replace('www.', '');
  const path = window.location.pathname;
  let match = null;

  for (const [domain, info] of Object.entries(SAAS_MAP)) {
    if (host.includes(domain.split('/')[0]) && (domain.includes('/') ? path.includes(domain.split('/')[1]) : true)) {
      match = info;
      break;
    }
  }

  if (!match) return;

  // Check if user dismissed this suggestion recently
  const dismissKey = 'indiestack_dismissed_' + match.name.replace(/\s/g, '_');
  if (localStorage.getItem(dismissKey)) {
    const dismissed = parseInt(localStorage.getItem(dismissKey));
    if (Date.now() - dismissed < 7 * 24 * 60 * 60 * 1000) return; // 7 days
  }

  // Fetch alternatives from IndieStack API
  fetch('https://indiestack.ai/api/tools/search?q=' + encodeURIComponent(match.query) + '&limit=3')
    .then(r => r.json())
    .then(data => {
      if (!data.tools || data.tools.length === 0) return;

      // Build suggestion card
      const container = document.createElement('div');
      container.id = 'indiestack-suggestion';
      container.innerHTML = `
        <div class="indiestack-header">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00D4F5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
          <span>Indie alternatives to ${match.name}</span>
          <button class="indiestack-close" title="Dismiss">&times;</button>
        </div>
        <div class="indiestack-tools">
          ${data.tools.map(t => `
            <a href="${t.indiestack_url || ('https://indiestack.ai/tool/' + t.slug)}" target="_blank" rel="noopener" class="indiestack-tool">
              <strong>${t.name}</strong>
              <span>${t.tagline || ''}</span>
            </a>
          `).join('')}
        </div>
        <a href="https://indiestack.ai/alternatives/${match.name.toLowerCase().replace(/\s+/g, '-')}" target="_blank" rel="noopener" class="indiestack-more">
          See all alternatives on IndieStack →
        </a>
      `;

      document.body.appendChild(container);

      // Dismiss handler
      container.querySelector('.indiestack-close').addEventListener('click', function() {
        container.remove();
        localStorage.setItem(dismissKey, Date.now().toString());
      });

      // Slide in after 2 seconds
      setTimeout(function() {
        container.classList.add('indiestack-visible');
      }, 2000);
    })
    .catch(function() {
      // Silent fail — don't bother users if API is down
    });
})();
