import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/shared/design_system/components/loading_skeleton.dart';
import 'package:revnara/shared/motion/durations.dart';
import 'package:revnara/shared/motion/motion.dart';

/// DS1.7: every animation must respect `MediaQuery.disableAnimations`.
/// This tests the shared helper directly -- the structural rule is that
/// every animated widget routes through it (§2.6 baseline DoD), so a
/// correct helper plus code review covers the rest; this test is the
/// helper's own regression anchor.
void main() {
  testWidgets('RevnaraMotion.duration returns the base duration normally',
      (tester) async {
    late Duration resolved;

    await tester.pumpWidget(
      MediaQuery(
        data: const MediaQueryData(disableAnimations: false),
        child: Builder(
          builder: (context) {
            resolved = RevnaraMotion.duration(context, RevnaraDurations.long);
            return const SizedBox.shrink();
          },
        ),
      ),
    );

    expect(resolved, RevnaraDurations.long);
  });

  testWidgets(
      'RevnaraMotion.duration collapses to zero when reduce-motion is on',
      (tester) async {
    late Duration resolved;

    await tester.pumpWidget(
      MediaQuery(
        data: const MediaQueryData(disableAnimations: true),
        child: Builder(
          builder: (context) {
            resolved = RevnaraMotion.duration(context, RevnaraDurations.long);
            return const SizedBox.shrink();
          },
        ),
      ),
    );

    expect(resolved, Duration.zero);
  });

  testWidgets('RevnaraMotion.minimal never returns literal zero',
      (tester) async {
    late Duration resolved;

    await tester.pumpWidget(
      MediaQuery(
        data: const MediaQueryData(disableAnimations: true),
        child: Builder(
          builder: (context) {
            resolved = RevnaraMotion.minimal(context, RevnaraDurations.long);
            return const SizedBox.shrink();
          },
        ),
      ),
    );

    expect(resolved, isNot(Duration.zero));
    expect(resolved.inMilliseconds, lessThan(RevnaraDurations.long.inMilliseconds));
  });

  testWidgets(
      'RevnaraLoadingSkeleton renders a static container (no shimmer '
      'AnimatedBuilder) when reduce-motion is on', (tester) async {
    await tester.pumpWidget(
      const MediaQuery(
        data: MediaQueryData(disableAnimations: true),
        child: MaterialApp(
          home: Scaffold(body: RevnaraLoadingSkeleton()),
        ),
      ),
    );

    // Scoped to the skeleton's own subtree -- Scaffold/MaterialApp have
    // their own unrelated AnimatedBuilder widgets in the ambient tree, so
    // an unscoped find.byType would false-positive/negative on those.
    final withinSkeleton = find.descendant(
      of: find.byType(RevnaraLoadingSkeleton),
      matching: find.byType(AnimatedBuilder),
    );
    expect(withinSkeleton, findsNothing);
    expect(
      find.descendant(
        of: find.byType(RevnaraLoadingSkeleton),
        matching: find.byType(Container),
      ),
      findsOneWidget,
    );
  });

  testWidgets(
      'RevnaraLoadingSkeleton shimmers (AnimatedBuilder present) with '
      'motion enabled', (tester) async {
    await tester.pumpWidget(
      const MediaQuery(
        data: MediaQueryData(disableAnimations: false),
        child: MaterialApp(
          home: Scaffold(body: RevnaraLoadingSkeleton()),
        ),
      ),
    );

    expect(
      find.descendant(
        of: find.byType(RevnaraLoadingSkeleton),
        matching: find.byType(AnimatedBuilder),
      ),
      findsOneWidget,
    );
  });
}
