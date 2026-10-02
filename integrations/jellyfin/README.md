# Jellyfin theme and splash

## Install (about 2 minutes, no plugin needed)

1. **Splash:** Dashboard → **Branding** → **Upload Custom Image** → choose `splash.png` (16:9, 1920×1080, full husky with the D tag visible). Keep **Enable the splash screen image** on.
2. **Theme:** open `custom.css`, copy everything, and paste it into **Custom CSS code** on the same page. Save.
3. Hard-refresh the page (Jellyfin caches CSS).

## Choose a variant

| File | Third-party requests | Notes |
|---|---|---|
| `custom.css` | **None** (default) | Brand accent, glass header/drawer, cards, buttons, scrollbar. |
| `custom-with-monochromic.css` | Loads a stylesheet from `cdn.jsdelivr.net` on every page view | Adds the Monochromic base theme. Exposes visitor IPs to the CDN. |

## Troubleshooting

- **A style doesn't apply:** Jellyfin class names change between versions. Inspect the element and swap the selector (`.btnPlay`, `.skinHeader`, `.mainDrawer`, `.navMenuOption-selected` are the likely ones).
- **Scrolling stutters on a phone:** delete the first rule block (the `backdrop-filter` glass), it's the heaviest.
- **Splash upload rejected:** use the PNG, not an SVG. A 3840×2160 version is in `assets/logo/splash/`.
- Native TV apps ignore custom CSS; this applies to web and browser-based clients.

The husky mark itself stays black and white. Accent purple is for the interface around it ([BRAND.md](../../BRAND.md)).
