import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/shared/design_system/tokens.dart';

/// WCAG 2.x relative luminance / contrast ratio, per
/// https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
double _relativeLuminance(Color color) {
  double channel(double c) {
    return c <= 0.03928 ? c / 12.92 : math.pow((c + 0.055) / 1.055, 2.4).toDouble();
  }

  final r = channel(color.r);
  final g = channel(color.g);
  final b = channel(color.b);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

double _contrastRatio(Color a, Color b) {
  final la = _relativeLuminance(a);
  final lb = _relativeLuminance(b);
  final lighter = math.max(la, lb);
  final darker = math.min(la, lb);
  return (lighter + 0.05) / (darker + 0.05);
}

void main() {
  group('WCAG contrast: governance colors vs. white (light mode)', () {
    final colors = <String, Color>{
      'riskR0': RevnaraGovernanceColors.light.riskR0,
      'riskR1': RevnaraGovernanceColors.light.riskR1,
      'riskR2': RevnaraGovernanceColors.light.riskR2,
      'riskR3': RevnaraGovernanceColors.light.riskR3,
      'riskR4': RevnaraGovernanceColors.light.riskR4,
      'riskR5': RevnaraGovernanceColors.light.riskR5,
      'riskR6': RevnaraGovernanceColors.light.riskR6,
      'evidenceCited': RevnaraGovernanceColors.light.evidenceCited,
      'assumption': RevnaraGovernanceColors.light.assumption,
      'approvedBound': RevnaraGovernanceColors.light.approvedBound,
      'humanNativeOnly': RevnaraGovernanceColors.light.humanNativeOnly,
    };

    for (final entry in colors.entries) {
      test(
        '${entry.key} meets WCAG AA (>= 3.0, non-text/large-text threshold) against white',
        () {
          final ratio = _contrastRatio(entry.value, const Color(0xFFFFFFFF));
          expect(
            ratio,
            greaterThanOrEqualTo(3.0),
            reason:
                '${entry.key} (${entry.value}) has contrast $ratio against white',
          );
        },
      );
    }
  });

  group('WCAG contrast: governance colors vs. dark surface (dark mode)', () {
    // Common Material 3 dark surface tone.
    const darkSurface = Color(0xFF121212);

    final colors = <String, Color>{
      'riskR0': RevnaraGovernanceColors.dark.riskR0,
      'riskR1': RevnaraGovernanceColors.dark.riskR1,
      'riskR2': RevnaraGovernanceColors.dark.riskR2,
      'riskR3': RevnaraGovernanceColors.dark.riskR3,
      'riskR4': RevnaraGovernanceColors.dark.riskR4,
      'riskR5': RevnaraGovernanceColors.dark.riskR5,
      'riskR6': RevnaraGovernanceColors.dark.riskR6,
      'evidenceCited': RevnaraGovernanceColors.dark.evidenceCited,
      'assumption': RevnaraGovernanceColors.dark.assumption,
      'approvedBound': RevnaraGovernanceColors.dark.approvedBound,
      'humanNativeOnly': RevnaraGovernanceColors.dark.humanNativeOnly,
    };

    for (final entry in colors.entries) {
      test(
        '${entry.key} meets WCAG AA (>= 3.0) against dark surface',
        () {
          final ratio = _contrastRatio(entry.value, darkSurface);
          expect(
            ratio,
            greaterThanOrEqualTo(3.0),
            reason:
                '${entry.key} (${entry.value}) has contrast $ratio against $darkSurface',
          );
        },
      );
    }
  });
}
