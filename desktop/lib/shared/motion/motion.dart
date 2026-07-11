import 'package:flutter/widgets.dart';

/// Reduced-motion support (DS1.7). Every animated widget in this design
/// system routes its duration through [RevnaraMotion.duration] rather than
/// using a [RevnaraDurations] constant directly -- a new animated component
/// that skips this is a code-review finding, not a style nitpick.
class RevnaraMotion {
  RevnaraMotion._();

  /// Returns [base] normally, or [Duration.zero] when the platform/OS has
  /// "reduce motion" enabled (`MediaQuery.disableAnimations`).
  static Duration duration(BuildContext context, Duration base) {
    return MediaQuery.of(context).disableAnimations ? Duration.zero : base;
  }

  /// Same as [duration], but returns a minimal non-zero duration instead of
  /// [Duration.zero] for widgets (e.g. [AnimatedSwitcher]) that behave
  /// oddly with a literal zero duration.
  static Duration minimal(BuildContext context, Duration base) {
    return MediaQuery.of(context).disableAnimations
        ? const Duration(milliseconds: 1)
        : base;
  }
}
