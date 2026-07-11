import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/shared/design_system/design_system.dart';

/// Golden/visual-regression tests (DS1.8's target). Baselines were
/// generated on Windows in the environment these were authored in --
/// Flutter golden tests are sensitive to platform font rendering, so these
/// baselines should be regenerated (`flutter test --update-goldens`) on
/// whatever CI runner actually executes .github/workflows/flutter-ci.yml
/// (ubuntu-latest) before relying on them there. This is standard Flutter
/// practice, not a sign anything here is wrong -- documented so the next
/// person doesn't mistake a legitimate re-baseline need for a bug.
void main() {
  Widget wrap(Widget child, {required Brightness brightness}) {
    return MaterialApp(
      theme: brightness == Brightness.light
          ? RevnaraTheme.light()
          : RevnaraTheme.dark(),
      home: Scaffold(
        body: Center(child: Padding(padding: const EdgeInsets.all(24), child: child)),
      ),
    );
  }

  for (final brightness in Brightness.values) {
    testWidgets('risk tier badges — ${brightness.name}', (tester) async {
      await tester.pumpWidget(
        wrap(
          Wrap(
            spacing: 8,
            children: [
              for (var tier = 0; tier <= 6; tier++)
                RevnaraRiskTierBadge(tier: tier),
            ],
          ),
          brightness: brightness,
        ),
      );

      await expectLater(
        find.byType(Wrap),
        matchesGoldenFile('goldens/risk_tier_badges_${brightness.name}.png'),
      );
    });

    testWidgets('buttons — ${brightness.name}', (tester) async {
      await tester.pumpWidget(
        wrap(
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              RevnaraButton(label: 'Primary', onPressed: () {}),
              const SizedBox(height: 8),
              RevnaraButton(
                label: 'Secondary',
                variant: RevnaraButtonVariant.secondary,
                onPressed: () {},
              ),
              const SizedBox(height: 8),
              RevnaraButton(
                label: 'Destructive',
                variant: RevnaraButtonVariant.destructive,
                onPressed: () {},
              ),
            ],
          ),
          brightness: brightness,
        ),
      );

      await expectLater(
        find.byType(Column),
        matchesGoldenFile('goldens/buttons_${brightness.name}.png'),
      );
    });
  }
}
