# Brand Guidelines — DevHound

**Last Updated:** October 1, 2026
**Version:** 1.2.0

<p align="center">
  <img src="./assets/logo/husky-primary.svg" alt="DevHound logo: stylized husky head with triangular D-tag collar" width="200"/>
</p>

---

## Overview

DevHound is an open-source project with a distinctive husky mascot featuring a triangular collar tag bearing the letter **D**. These guidelines ensure consistent, respectful use of our branding across all contexts.

---

## Logo Description

### Official Logo Components

| Element | Description |
|---|---|
| **Mascot** | Stylized husky/Alaskan malamute head, front-facing, black-and-white line art |
| **Collar** | Triangular pendant tag hanging from neck, centered on chest area |
| **Letter Mark** | Capital **D** engraved on triangular collar tag, pointing downward |
| **Style** | Vector line art, high contrast black on white background |
| **Expression** | Alert, friendly, approachable canine face with forward-facing eyes |

### Logo Variants

| Variant | File | Use case |
|---|---|---|
| Primary (black) | [`husky-primary.svg`](./assets/logo/husky-primary.svg) | Light backgrounds |
| Dark mode (white) | [`husky-dark-mode.svg`](./assets/logo/husky-dark-mode.svg) | Dark backgrounds |
| Favicon | [`favicons/favicon-32x32.png`](./assets/logo/favicons/favicon-32x32.png) | Browser tabs |
| App icon | [`icons/app-icon-1024.png`](./assets/logo/icons/app-icon-1024.png) | Mobile / desktop app icons |
| Splash (16:9) | [`splash/devhound-splash-1920x1080.png`](./assets/logo/splash/devhound-splash-1920x1080.png) | Jellyfin / media-server splash screens |
| Social card | [`og-card.png`](./assets/logo/og-card.png) | Link previews (1200×630) |
| Sponsor badge | [`sponsor-badge.png`](./assets/logo/sponsor-badge.png) | Sponsor placements (200×200) |

All raster sizes are generated from the master vector (`husky-primary.svg`) — see [Regenerating assets](#regenerating-assets).

---

## Usage Rules

### ✅ Do

| Guideline | Specification |
|---|---|
| Use approved assets | Only use official logos from [`assets/logo/`](./assets/logo/) |
| Maintain contrast | Keep black-on-white or white-on-black for optimal legibility |
| Preserve proportions | Scale uniformly without distorting aspect ratio |
| Include clear space | Maintain minimum padding equal to the height of the **D** tag |
| Credit appropriately | Add "© DevHound Project" when used externally |
| Link to source | Include a link back to the project when displaying the logo online |

### ❌ Don't

| Violation | Why it's not allowed |
|---|---|
| Add colors to the husky | Original is monochrome; color changes alter brand identity |
| Remove or change the D tag | The **D** collar is the core identifying mark |
| Stretch or skew the logo | Distortion damages recognizability and professionalism |
| Use on busy backgrounds | Low contrast reduces visibility and clarity |
| Alter facial features | Eyes, nose, ears, and fur lines are protected design elements |
| Combine with other project logos | Prevents brand confusion and dilution |

---

## Clear Space Requirements

```
┌───────────────────────────────┐
│          ← clear space →      │
│        ╱‾‾╲                   │
│       │ ᐧᐧ │  eyes             │
│        ╲__╱   nose/mouth       │
│        │[D]│  ← collar tag     │
│                                │
└───────────────────────────────┘
```

**Minimum clearance around the entire logo:** equal to the height of the triangular **D** tag on the collar.

---

## Color Specifications

### Approved Color Palette

| Use case | Hex | RGB |
|---|---|---|
| Primary Black | `#000000` | `0, 0, 0` |
| Primary White | `#FFFFFF` | `255, 255, 255` |
| Accent Purple | `#6D4AFF` | `109, 74, 255` |
| Gray (fallback) | `#333333` | `51, 51, 51` |

### Acceptable Color Combinations

| Combination | Background | Foreground |
|---|---|---|
| Standard | White `#FFFFFF` | Black `#000000` |
| Dark mode | Black `#000000` | White `#FFFFFF` |
| Accent highlight | White | Purple `#6D4AFF`, secondary elements only |
| Grayscale print | White | Gray `#333333`, for low-res output only |

The husky mark itself should remain strictly black-and-white. Accent purple may be used for surrounding UI elements but should never fill the husky silhouette.

---

## File Formats & Sizing

| Purpose | Format | Dimensions | Path |
|---|---|---|---|
| Primary logo | SVG | Scalable | `assets/logo/husky-primary.svg` |
| Dark mode logo | SVG | Scalable | `assets/logo/husky-dark-mode.svg` |
| Website favicon | PNG | 32×32, 16×16 | `assets/logo/favicons/` |
| App icon | PNG | 1024 / 512 / 256 / 128 / 64 / 32 / 16 | `assets/logo/icons/` |
| Social media card | PNG | 1200×630 | `assets/logo/og-card.png` |
| Sponsor badge | PNG | 200×200 | `assets/logo/sponsor-badge.png` |

### Verifying assets

```bash
devhound brand
```

Checks that every required asset exists, SVGs are valid and under 250 KB, the splash is 16:9, and the two official vector marks still match `assets/logo/CHECKSUMS.sha256`. If you change the logo on purpose, run `devhound brand --update-checksums` and record it in the changelog.

### Design tokens

CSS variables and JSON tokens live in [`tokens/`](./tokens/). Accent purple is for UI chrome around the mascot, never for filling the husky.

### Regenerating assets

All raster assets are derived from a single vector trace of the master artwork. To rebuild them after editing the source:

```bash
python3 scripts/render.py
```

This reads `assets/logo/husky-primary.svg`, re-renders every PNG size listed above at 4× supersampling, and writes the dark-mode SVG variant. No network access or external SVG renderer is required.

---

## Trademark & Protected Elements

The following are the identifying design elements of the DevHound project:

1. **Husky mascot design** — the specific facial structure, fur lines, and front-facing angle
2. **Triangular D-tag collar** — the pendant with capital **D** letter
3. **"DevHound"** — project name and wordmark
4. **Combined logo lockup** — husky head + project name arrangement

### Not protected (fair use)

- Generic husky dog images without the D-tag collar
- The letter **D** alone
- Common canine mascot concepts in general

---

## Derivative Works Policy

### Community forks & related projects

| Requirement | Action |
|---|---|
| Distinguish your mark | Replace or modify the **D**-tag collar to something distinct |
| Avoid name confusion | Don't use "DevHound" as your own project's name |
| Add a disclaimer | State "Not affiliated with the official DevHound project" |
| Let us know | Open an issue or discussion describing your changes |

### Acceptable modifications

- Changing the collar tag letter (D → your own initial)
- Slightly altering the facial expression, if the overall style stays distinct from ours
- Removing the collar entirely

### Discouraged

- Using the exact logo for an unrelated commercial product
- Selling merchandise with the unmodified logo
- Implying endorsement by the DevHound project without confirming with maintainers first

---

## Accessibility Guidelines

### Alt text

Always include descriptive alt text when embedding the logo:

```html
<img src="/assets/logo/husky-primary.svg"
     alt="DevHound logo: stylized husky head with triangular D-tag collar">
```

### Color contrast

| Context | Minimum ratio | Recommended |
|---|---|---|
| Text on logo background | 4.5:1 | 7:1 |
| Logo on page background | 3:1 | 4.5:1 |
| Interactive elements (buttons) | 3:1 | 4.5:1 |

### Motion

- ❌ No rapid flashing or strobing
- ❌ No continuous rotation
- ✅ Subtle fade-in/out transitions are fine

---

## Examples of Correct Usage

| Scenario | Implementation |
|---|---|
| Website header | Centered black husky logo on white navigation bar |
| GitHub README | Logo in top-left corner with "DevHound" text beside it |
| Presentation slide | Logo in bottom-right footer with clear space |
| T-shirt design | Large centered logo with adequate margin around edges |

### Avoid

| Scenario | Problem |
|---|---|
| Colored husky with a gradient fill | Alters the mark |
| Husky over a busy photo background | Poor legibility, no clear space |
| Horizontally stretched logo | Damaged proportions |
| D-tag removed "for a simpler look" | Loses the identifying element |

---

## Provenance

`assets/reference/source-scan.png` is the original scanned artwork the vector trace (`husky-primary.svg`) was built from. `assets/reference/reference-photo.jpg` is a photo of the real dog that inspired the mascot design. Neither file is a brand asset — don't use them in place of the logo files in `assets/logo/`.

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| 1.0.0 | 2026-08-05 | Initial release |
| 1.1.0 | 2026-08-05 | Added true vector trace of the mascot, dark-mode variant, full icon/favicon set, OG card, asset regeneration script; fixed formatting |
| 1.2.0 | 2026-10-01 | Added Jellyfin splash (16:9 PNG), design tokens, official-mark checksums (`devhound brand`), moved guidelines from README to BRAND.md |

---

## Related Documentation

- [`FUNDING.json`](./FUNDING.json) — funding configuration
- [`README.md`](./README.md) — project overview and toolkit
- [`PRIVACY.md`](./PRIVACY.md) — privacy guarantees
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — how to contribute
- [`GOVERNANCE.md`](./GOVERNANCE.md) — project governance model
- [`LICENSE`](./LICENSE) — license terms

---

**Questions or concerns?** Open an issue on this repository.
