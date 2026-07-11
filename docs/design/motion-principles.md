# Motion Principles (DS1.4)

Implemented in `desktop/lib/shared/motion/`. Motion here is in service of clarity and the §2.7 60fps/no-dropped-frames budget, not decoration — every duration is short, every animation is a state signal.

## Durations (`RevnaraDurations`)

| Token | Value | Used for |
|---|---|---|
| `micro` | 150ms | Hover/press feedback, button state changes |
| `short` | 200ms | Small state changes (checkbox, toggle, badge appear) |
| `medium` | 300ms | Standard transitions, list-item state change |
| `long` | 400ms | Screen/page transitions |
| `staggerStep` | 40ms | Per-item delay in a list entrance stagger |

## Curves (`RevnaraCurves`)

| Token | Flutter curve | Used for |
|---|---|---|
| `standard` | `Curves.easeInOutCubic` | Default for most transitions |
| `enter` | `Curves.easeOutCubic` | Elements entering the screen |
| `exit` | `Curves.easeInCubic` | Elements leaving the screen |
| `emphasized` | `Curves.easeInOutCubicEmphasized` | The "approved"/"submitted" confirmation moment — a slightly more pronounced curve reserved for governance confirmations so they read as distinct from routine UI motion |

## Named moments

- **Page transition:** shared-axis/fade-through pattern applied consistently across every GoRouter route via `motion/transitions.dart` — `long` duration, `standard` curve.
- **List entrance:** each item fades/slides in with `staggerStep` delay per index, `medium` duration, `enter` curve — used by opportunity/proposal/approval lists from Sprint 7 onward.
- **Loading skeleton:** a continuous shimmer, not a discrete transition — see `components/loading_skeleton.dart`.
- **Approval/submission confirmation:** the one deliberately more expressive animation in the system (`emphasized` curve, `medium` duration) — reserved for the moment a governance action actually completes (Sprint 10/11 consume this), so it reads as a meaningful confirmation rather than routine UI feedback.

## Reduced motion (DS1.7)

Every animation in `motion/` is built through `RevnaraMotion.duration(context, token)`, which returns `Duration.zero` (or a minimal duration where zero would break the widget, e.g. `AnimatedSwitcher`) when `MediaQuery.of(context).disableAnimations` is true. This is a structural rule, not a per-widget opt-in — a new animated component that doesn't route its duration through this helper is a code-review finding.

## Performance discipline

Every animation is verified against §2.7's Flutter budget (sustained 60fps, no dropped frames) as part of Sprint 1.5's testing — see the component gallery, which is the target of that test. Motion durations above were chosen specifically to stay short enough that this is achievable without special-casing.
