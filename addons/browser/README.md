# DevHound Secret Check (browser, local-only)

Select text (or scan the page) and see whether it contains hardcoded secrets. Useful before pasting code into a chat, ticket or pull request.

## Install

Chrome / Edge / Brave: `chrome://extensions` → enable **Developer mode** → **Load unpacked** → choose `addons/browser`.

## Privacy by construction

- Permissions: only `activeTab` and `scripting`. It reads the page **only when you click a button**. No host permissions, no background script, no content scripts.
- The extension's Content Security Policy sets `connect-src 'none'`, so the browser itself blocks any network request from it.
- Matched values are never displayed or stored; results show the rule, line and column.
- A test fails the build if the manifest gains permissions or the code uses `fetch`, `XMLHttpRequest`, `innerHTML` or similar.
- `rules.js` is generated from the Python scanner (`python3 scripts/gen_browser_rules.py`), and 17 Node tests check both agree on shared cases.

"No secrets found" is not proof of safety; the scanner only knows common formats.

Status: logic is tested under Node; not yet loaded in a real browser. Firefox needs a `browser_specific_settings` entry before it will load this manifest.
