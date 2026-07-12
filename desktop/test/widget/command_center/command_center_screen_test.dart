import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/features/command_center/command_center_screen.dart';

void main() {
  testWidgets(
      'shows a loading indicator rather than crashing when no active '
      'organization is set', (tester) async {
    // Same "no active organization" guard as every other Sprint 4-7
    // screen -- _load() returns early, so the dashboard stays in its
    // initial loading state rather than attempting a request or crashing.
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: CommandCenterScreen()),
      ),
    );
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.text('Dashboard'), findsOneWidget);
  });
}
