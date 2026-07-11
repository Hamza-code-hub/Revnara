import 'package:flutter/material.dart';

/// Seed colors and governance-semantic palette. See docs/design/tokens.md
/// for the reasoning behind each value -- update that file in the same PR
/// as any change here.
class RevnaraColors {
  RevnaraColors._();

  /// Revnara Ink -- primary brand seed.
  static const Color seedPrimary = Color(0xFF1C4B5E);

  /// Evidence Gold -- secondary accent seed.
  static const Color seedSecondary = Color(0xFFC48A2E);
}

/// Fixed governance-semantic colors, exposed as a [ThemeExtension] so they
/// stay available via `Theme.of(context).extension<RevnaraGovernanceColors>()`
/// alongside the seed-derived [ColorScheme]. Unlike the [ColorScheme], these
/// are not regenerated per seed -- a risk badge must read the same
/// conceptually in light or dark mode, so light/dark values are chosen
/// explicitly rather than derived.
@immutable
class RevnaraGovernanceColors extends ThemeExtension<RevnaraGovernanceColors> {
  const RevnaraGovernanceColors({
    required this.riskR0,
    required this.riskR1,
    required this.riskR2,
    required this.riskR3,
    required this.riskR4,
    required this.riskR5,
    required this.riskR6,
    required this.evidenceCited,
    required this.assumption,
    required this.approvedBound,
    required this.humanNativeOnly,
  });

  final Color riskR0;
  final Color riskR1;
  final Color riskR2;
  final Color riskR3;
  final Color riskR4;
  final Color riskR5;
  final Color riskR6;
  final Color evidenceCited;
  final Color assumption;
  final Color approvedBound;
  final Color humanNativeOnly;

  /// Risk tiers R0-R6 in order, for anything that needs to iterate them
  /// (e.g. a legend) without hardcoding the tier -> color mapping again.
  List<Color> get riskScale =>
      [riskR0, riskR1, riskR2, riskR3, riskR4, riskR5, riskR6];

  static const RevnaraGovernanceColors light = RevnaraGovernanceColors(
    riskR0: Color(0xFF2E7D32),
    riskR1: Color(0xFF558B2F),
    // Darker than a typical "lime 800" -- the lighter tone failed the
    // WCAG contrast test against white (2.9:1, below the 3:1 minimum).
    riskR2: Color(0xFF6B6B14),
    // Darker amber than "amber 800" for the same reason (1.97:1 measured).
    riskR3: Color(0xFFA15C00),
    riskR4: Color(0xFFEF6C00),
    riskR5: Color(0xFFD84315),
    riskR6: Color(0xFFC62828),
    evidenceCited: Color(0xFF00796B),
    assumption: Color(0xFF6A4C93),
    approvedBound: Color(0xFF283593),
    humanNativeOnly: Color(0xFF546E7A),
  );

  static const RevnaraGovernanceColors dark = RevnaraGovernanceColors(
    riskR0: Color(0xFF66BB6A),
    riskR1: Color(0xFF9CCC65),
    riskR2: Color(0xFFD4D661),
    riskR3: Color(0xFFFFCA55),
    riskR4: Color(0xFFFFA040),
    riskR5: Color(0xFFFF7043),
    riskR6: Color(0xFFEF5350),
    evidenceCited: Color(0xFF4DB6AC),
    assumption: Color(0xFFB39DDB),
    approvedBound: Color(0xFF7986CB),
    humanNativeOnly: Color(0xFF90A4AE),
  );

  @override
  RevnaraGovernanceColors copyWith({
    Color? riskR0,
    Color? riskR1,
    Color? riskR2,
    Color? riskR3,
    Color? riskR4,
    Color? riskR5,
    Color? riskR6,
    Color? evidenceCited,
    Color? assumption,
    Color? approvedBound,
    Color? humanNativeOnly,
  }) {
    return RevnaraGovernanceColors(
      riskR0: riskR0 ?? this.riskR0,
      riskR1: riskR1 ?? this.riskR1,
      riskR2: riskR2 ?? this.riskR2,
      riskR3: riskR3 ?? this.riskR3,
      riskR4: riskR4 ?? this.riskR4,
      riskR5: riskR5 ?? this.riskR5,
      riskR6: riskR6 ?? this.riskR6,
      evidenceCited: evidenceCited ?? this.evidenceCited,
      assumption: assumption ?? this.assumption,
      approvedBound: approvedBound ?? this.approvedBound,
      humanNativeOnly: humanNativeOnly ?? this.humanNativeOnly,
    );
  }

  @override
  RevnaraGovernanceColors lerp(
    ThemeExtension<RevnaraGovernanceColors>? other,
    double t,
  ) {
    if (other is! RevnaraGovernanceColors) return this;
    return RevnaraGovernanceColors(
      riskR0: Color.lerp(riskR0, other.riskR0, t)!,
      riskR1: Color.lerp(riskR1, other.riskR1, t)!,
      riskR2: Color.lerp(riskR2, other.riskR2, t)!,
      riskR3: Color.lerp(riskR3, other.riskR3, t)!,
      riskR4: Color.lerp(riskR4, other.riskR4, t)!,
      riskR5: Color.lerp(riskR5, other.riskR5, t)!,
      riskR6: Color.lerp(riskR6, other.riskR6, t)!,
      evidenceCited: Color.lerp(evidenceCited, other.evidenceCited, t)!,
      assumption: Color.lerp(assumption, other.assumption, t)!,
      approvedBound: Color.lerp(approvedBound, other.approvedBound, t)!,
      humanNativeOnly:
          Color.lerp(humanNativeOnly, other.humanNativeOnly, t)!,
    );
  }
}

/// 4px-base spacing scale.
class RevnaraSpacing {
  RevnaraSpacing._();

  static const double xs = 4;
  static const double sm = 8;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 32;
  static const double xxl = 48;
  static const double xxxl = 64;
}

/// Corner radius scale.
class RevnaraRadius {
  RevnaraRadius._();

  static const double sm = 4;
  static const double md = 8;
  static const double lg = 16;
  static const double pill = 999;
}
