import 'package:flutter/animation.dart';

/// Named animation curves. See docs/design/motion-principles.md.
class RevnaraCurves {
  RevnaraCurves._();

  static const Curve standard = Curves.easeInOutCubic;
  static const Curve enter = Curves.easeOutCubic;
  static const Curve exit = Curves.easeInCubic;

  /// Reserved for the "approved"/"submitted" governance confirmation moment
  /// (Sprint 10/11) -- deliberately more expressive than [standard] so it
  /// reads as a meaningful confirmation, not routine UI feedback.
  static const Curve emphasized = Curves.easeInOutCubicEmphasized;
}
