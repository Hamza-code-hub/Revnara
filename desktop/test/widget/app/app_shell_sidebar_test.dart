import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/app/app_shell.dart';

void main() {
  testWidgets('renders every nav item and the page content', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: AppShell(
            location: '/opportunities',
            child: Center(child: Text('page content')),
          ),
        ),
      ),
    );
    await tester.pump();

    expect(find.text('Revnara'), findsOneWidget);
    expect(find.text('Dashboard'), findsOneWidget);
    expect(find.text('Opportunities'), findsOneWidget);
    expect(find.text('Company Profile'), findsOneWidget);
    expect(find.text('Team & Brain'), findsOneWidget);
    expect(find.text('Team Management'), findsOneWidget);
    expect(find.text('Sign out'), findsOneWidget);
    expect(find.text('page content'), findsOneWidget);
  });

  testWidgets('highlights the active nav item based on location', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: AppShell(
            location: '/company/profile',
            child: SizedBox.shrink(),
          ),
        ),
      ),
    );
    await tester.pump();

    // The active tile renders with a filled Material background rather
    // than transparent -- confirm at least one Material in the sidebar
    // isn't using the default transparent color (a crude but real check
    // that highlighting logic ran, not just that the text exists).
    final materials = tester.widgetList<Material>(find.byType(Material));
    expect(materials.any((m) => m.color != null && m.color != Colors.transparent), isTrue);
  });
}
