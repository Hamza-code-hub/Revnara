import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/shared/design_system/theme.dart';
import 'package:revnara/shared/dev/component_gallery.dart';

/// Smoke test: the gallery (every component + reference layout + animation
/// in one screen) renders with no exceptions and the light/dark toggle
/// works. This is a lightweight proxy for §2.7's 60fps/no-dropped-frames
/// budget -- full frame-timing profiling needs `flutter drive` in profile
/// mode against a real device/emulator, out of scope for a unit test, and
/// tracked as a follow-up rather than approximated here.
///
/// Uses bounded `pump(duration)` calls rather than `pumpAndSettle()`: the
/// gallery includes a continuously-repeating shimmer animation
/// (RevnaraLoadingSkeleton), which would make pumpAndSettle wait forever.
Future<void> _pumpGallery(WidgetTester tester) async {
  await tester.pumpWidget(
    ProviderScope(
      child: MaterialApp(
        theme: RevnaraTheme.light(),
        darkTheme: RevnaraTheme.dark(),
        home: const ComponentGalleryScreen(),
      ),
    ),
  );
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 400));
}

void main() {
  testWidgets('component gallery renders with no exceptions', (tester) async {
    await _pumpGallery(tester);

    expect(tester.takeException(), isNull);
    expect(find.text('Component Gallery'), findsOneWidget);
  });

  testWidgets('theme toggle switches between light and dark', (tester) async {
    await _pumpGallery(tester);

    // themeModeProvider starts at ThemeMode.system (not dark), so the
    // gallery's icon -- which shows dark_mode only when the mode *is*
    // dark -- starts as light_mode.
    final toggle = find.byIcon(Icons.light_mode);
    expect(toggle, findsOneWidget);

    await tester.tap(toggle);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));

    expect(tester.takeException(), isNull);
    expect(find.byIcon(Icons.dark_mode), findsOneWidget);
  });
}
