import 'package:flutter/material.dart';

import 'tokens.dart';

/// Light/dark [ThemeData] built from [RevnaraColors]' seeds plus the fixed
/// [RevnaraGovernanceColors] extension (DS1.3). This is the only place
/// `ThemeData` is constructed -- screens and components read from
/// `Theme.of(context)`, never build their own colors/styles inline.
class RevnaraTheme {
  RevnaraTheme._();

  static ThemeData light() => _build(Brightness.light);

  static ThemeData dark() => _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: RevnaraColors.seedPrimary,
      secondary: RevnaraColors.seedSecondary,
      brightness: brightness,
    );

    final governanceColors = brightness == Brightness.light
        ? RevnaraGovernanceColors.light
        : RevnaraGovernanceColors.dark;

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: colorScheme,
      extensions: [governanceColors],
      cardTheme: CardThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(RevnaraRadius.md),
        ),
      ),
      chipTheme: ChipThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(RevnaraRadius.pill),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(RevnaraRadius.sm),
        ),
      ),
    );
  }
}

/// Convenience accessor: `context.governanceColors`.
extension GovernanceColorsExtension on BuildContext {
  RevnaraGovernanceColors get governanceColors =>
      Theme.of(this).extension<RevnaraGovernanceColors>()!;
}
