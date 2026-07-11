# Component Inventory (DS1.6/DS1.8/DS1.9/DS1.10)

What exists in `desktop/lib/shared/design_system/` as of Sprint 1.5, and where to find it. Screens from Sprint 2 onward should use these rather than ad hoc styling (§2.6 baseline Definition of Done) — extend this file in the same PR as any new component.

## Foundations

| File | Provides |
|---|---|
| `tokens.dart` | `RevnaraColors` (seed colors), `RevnaraGovernanceColors` (theme extension: risk tiers, evidence/assumption, approved/bound, human-native), `RevnaraSpacing`, `RevnaraRadius` |
| `theme.dart` | `RevnaraTheme.light()` / `.dark()`, `context.governanceColors` extension |
| `layout/breakpoints.dart` | `RevnaraBreakpoint` (compact/medium/expanded), `RevnaraAdaptive` widget |
| `../motion/durations.dart`, `curves.dart`, `motion.dart`, `transitions.dart` | `RevnaraDurations`, `RevnaraCurves`, `RevnaraMotion.duration()` (reduced-motion aware), `revnaraPageTransition()`, `RevnaraStaggeredEntrance` |

## Components (`components/`)

| Widget | File | Notes |
|---|---|---|
| `RevnaraButton` | `buttons.dart` | primary / secondary / destructive variants |
| `RevnaraTextField`, `RevnaraSelectField<T>` | `inputs.dart` | Always sized `double.infinity` — parent controls width |
| `RevnaraCard` | `cards.dart` | |
| `RevnaraListRow` | `list_row.dart` | Used by every Sprint 6+ opportunity/proposal/approval list |
| `RevnaraStatusChip` | `badges.dart` | Generic primitive; also the pattern for Sprint 11's `PlatformCapability` status labels |
| `RevnaraRiskTierBadge` | `badges.dart` | R0–R6, per `docs/BDOS_Enforcement_Spec.md` |
| `RevnaraEvidenceBadge` | `badges.dart` | cited vs. assumption (Sprint 9) |
| `RevnaraApprovalBoundBadge` | `badges.dart` | Sprint 10 |
| `RevnaraHumanNativeBadge` | `badges.dart` | Sprint 11 |
| `RevnaraEmptyState` | `empty_state.dart` | |
| `RevnaraLoadingSkeleton` | `loading_skeleton.dart` | Shimmer; static in reduced-motion mode |
| `RevnaraToast` | `toast.dart` | `RevnaraToast.show(context, message, variant: ...)` |

## Reference layouts (`reference_layouts/`)

| Layout | File | Demonstrates |
|---|---|---|
| List/detail | `list_detail_reference.dart` | Single pane at compact width (list ↔ detail swap), side-by-side `Expanded` panes at medium/expanded — the pattern for opportunity/proposal/approval screens |
| Form | `form_reference.dart` | 1-column at compact, 2-column at medium/expanded via `Wrap` + fractional width — no fixed-pixel field width |

## Dev tools

- `desktop/lib/shared/dev/component_gallery.dart` — every component/state/animation in one screen, light/dark toggle, reachable at `/dev/gallery` (hidden route, never linked from normal navigation).

## Import convention

Screens import the barrel file:

```dart
import 'package:revnara/shared/design_system/design_system.dart';
```

not individual component files, so the whole system stays a single, versioned surface.
