import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/features/opportunities/opportunity_intake_screen.dart';

void main() {
  testWidgets('renders all three intake tabs without crashing', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: OpportunityIntakeScreen()),
      ),
    );
    await tester.pump();

    expect(find.text('New opportunity'), findsOneWidget);
    expect(find.text('Manual'), findsOneWidget);
    expect(find.text('Upwork link'), findsOneWidget);
    expect(find.text('CSV import'), findsOneWidget);
  });

  testWidgets('switching to the Upwork link tab shows the human-native disclosure',
      (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: OpportunityIntakeScreen()),
      ),
    );
    await tester.pump();

    await tester.tap(find.text('Upwork link'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Revnara never'), findsOneWidget);
    expect(find.text('Listing URL'), findsOneWidget);
  });

  testWidgets('switching to the CSV import tab shows the paste box and required-column hint',
      (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: OpportunityIntakeScreen()),
      ),
    );
    await tester.pump();

    await tester.tap(find.text('CSV import'));
    await tester.pumpAndSettle();

    expect(find.text('CSV content'), findsOneWidget);
    expect(find.textContaining('Required column: title'), findsOneWidget);
  });

  testWidgets('submitting the manual form with no active organization does not crash',
      (tester) async {
    // No active org selected -- _submit() returns early (same guard as
    // every other Sprint 4-6 form), so tapping Create must not throw.
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: OpportunityIntakeScreen()),
      ),
    );
    await tester.pump();

    await tester.enterText(find.widgetWithText(TextField, 'Title'), 'Test opportunity');
    await tester.tap(find.text('Create opportunity'));
    await tester.pump();

    expect(find.text('New opportunity'), findsOneWidget);
  });
}
