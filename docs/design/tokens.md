# Design Tokens (DS1.2)

Implemented in `desktop/lib/shared/design_system/tokens.dart`. This file documents the values and the reasoning; the code is the source of truth if the two ever drift — update this file in the same PR as any token change.

## Color

### Seed colors (feed Material 3's `ColorScheme.fromSeed`)

| Token | Value | Role |
|---|---|---|
| `seedPrimary` (Revnara Ink) | `#1C4B5E` | Primary brand seed — light/dark `ColorScheme` generated from this |
| `seedSecondary` (Evidence Gold) | `#C48A2E` | Secondary accent seed |

`ColorScheme.fromSeed` generates the full role set (`primary`, `onPrimary`, `primaryContainer`, `surface`, `error`, etc.) for both light and dark mode from these two seeds — this is what M3 uses to guarantee WCAG-AA-safe contrast between a color and its `on*` counterpart, so we get accessible pairs without hand-picking every shade.

### Governance semantic colors (`RevnaraGovernanceColors` theme extension)

Fixed values, not seed-derived, because these need to stay visually distinct from each other and from the base `ColorScheme` regardless of theme — a risk badge must read the same conceptually in light or dark mode.

| Token | Light value | Dark value | Used for |
|---|---|---|---|
| `riskR0` | `#2E7D32` | `#66BB6A` | Risk tier R0 (automatic) |
| `riskR1` | `#558B2F` | `#9CCC65` | Risk tier R1 |
| `riskR2` | `#6B6B14` | `#D4D661` | Risk tier R2 (darkened from an initial `#9E9D24` -- measured 2.9:1 against white, below the 3:1 minimum) |
| `riskR3` | `#A15C00` | `#FFCA55` | Risk tier R3 (darkened from an initial `#F9A825` -- measured 1.97:1 against white) |
| `riskR4` | `#EF6C00` | `#FFA040` | Risk tier R4 |
| `riskR5` | `#D84315` | `#FF7043` | Risk tier R5 |
| `riskR6` | `#C62828` | `#EF5350` | Risk tier R6 (highest) |
| `evidenceCited` | `#00796B` | `#4DB6AC` | Claim backed by a citation |
| `assumption` | `#6A4C93` | `#B39DDB` | Claim marked as an assumption, not evidence-backed |
| `approvedBound` | `#283593` | `#7986CB` | Approval bound to payload hash / policy version |
| `humanNativeOnly` | `#546E7A` | `#90A4AE` | Action requires a human, native to the platform |

Dark-mode values are lightened/desaturated from the light-mode base (not simply the same hex) specifically so they retain adequate contrast against a dark surface — verified by the automated contrast test in Sprint 1.5's test suite, not just eyeballed.

## Typography

Material 3's default type scale (`display`/`headline`/`title`/`body`/`label`, each in large/medium/small), using the platform default font (Roboto/system) — no custom typeface bundled yet (see `brand-identity.md`). `theme.dart` applies `RevnaraGovernanceColors`-aware emphasis (e.g. `labelSmall` + a semantic color) for badges rather than defining new type styles per component.

## Spacing (`RevnaraSpacing`)

4px base unit, matching Material's spacing grid:

| Token | Value |
|---|---|
| `xs` | 4 |
| `sm` | 8 |
| `md` | 16 |
| `lg` | 24 |
| `xl` | 32 |
| `xxl` | 48 |
| `xxxl` | 64 |

## Radius (`RevnaraRadius`)

| Token | Value |
|---|---|
| `sm` | 4 |
| `md` | 8 |
| `lg` | 16 |
| `pill` | 999 |

## Elevation

Uses Material 3's standard elevation levels (0/1/3/6/8/12dp) directly via `ThemeData`'s surface tint — not re-tokenized, since M3's elevation-via-surface-tint approach (rather than shadow depth) is already the accessible, theme-aware default.

## Breakpoints (DS1.9 — see `layout/breakpoints.md` note in component-inventory.md)

| Token | Range | Class |
|---|---|---|
| `compact` | < 600px | Phone-class |
| `medium` | 600–1024px | Tablet / split-view |
| `expanded` | > 1024px | Desktop |

Matches Material 3's window size classes so Sprint 15.5's mobile targets fall into the same system rather than needing a separate one.
