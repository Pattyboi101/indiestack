# IndieStack Browser Extension

Discover indie alternatives when visiting big SaaS products.

## Install (Development)

1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select this `extension/` directory

## How it works

When you visit a known SaaS site (Google Analytics, Mailchimp, etc.), the extension
shows a small notification with indie alternatives from IndieStack's catalog.

You can also click the extension icon to search IndieStack directly.

## Build for production

The extension uses Manifest V3 and has no build step. To publish:
1. Create placeholder icons in `icons/` (16x16, 48x48, 128x128 PNG)
2. Zip the directory
3. Upload to Chrome Web Store

## Supported SaaS sites

Google Analytics, Mailchimp, Zendesk, Intercom, HubSpot, Salesforce,
Mixpanel, Amplitude, Datadog, Auth0, Typeform, Calendly, Stripe (docs),
Figma, Notion, Airtable, SendGrid, Twilio, Hotjar, Freshdesk
