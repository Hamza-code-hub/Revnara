# Revnara Visual Identity (DS1.1)

**Status:** No dedicated designer was available for Sprint 1.5 (per the sprint plan's own risk mitigation, this direction is scoped down to a defensible palette + type system rather than an open-ended brand exercise). Revisit depth once real customer feedback exists.

## Direction

Revnara's differentiator is governance — evidence, approvals, risk tiers, audit trails. The visual identity leans into that instead of generic SaaS gradients: an **ink + gold** pairing that reads as "official record" rather than "startup dashboard."

- **Primary — Revnara Ink** (`#1C4B5E`): a deep teal-navy. Authority and precision, not a generic blue.
- **Secondary — Evidence Gold** (`#C48A2E`): a warm, restrained gold used sparingly for "this is backed by evidence" moments (citation chips, verified badges) — evokes an official seal/stamp, tying directly to the product's evidence-grounding promise rather than being decorative.

Both are seed colors for Material 3's `ColorScheme.fromSeed`, which generates full, contrast-safe light/dark palettes from them — a defensible way to get a coherent, accessible scheme without a bespoke palette built swatch-by-swatch.

## Governance semantic colors

These exist because the product's core UI moments *are* governance states — a risk tier, an evidence citation, an assumption, a bound approval, a human-native requirement — and those should be immediately recognizable, not just labeled in text. See `tokens.md` for exact values.

| Concept | Color family | Why this hue |
|---|---|---|
| Risk tiers R0–R6 | Green → red, 7 steps | Standard low-to-high risk reading, no ambiguity |
| Evidence-cited claim | Teal | Distinct from risk scale; calm, "verified" |
| Assumption (unverified claim) | Violet | Distinct hue from both risk and evidence — deliberately neither "good" nor "bad," just "flagged" |
| Approved / bound (payload-hash-bound approval) | Indigo | Distinct from assumption's violet; reads as "locked in," pairs with a lock/shield icon in components |
| Human-native only | Slate/blue-grey | Deliberately muted, not alarming — this is a normal, expected state (per `docs/BDOS_Enforcement_Spec.md`), not an error |

## What this is not

Not a full brand system (no custom typeface, no illustration style, no logo work) — those are out of scope until there's a real design resource or customer feedback to design against. The default platform font (Roboto/system) is used deliberately rather than bundling a custom font for a v1 palette.
