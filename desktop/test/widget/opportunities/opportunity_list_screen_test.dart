import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/features/opportunities/opportunity_list_screen.dart';

void main() {
  testWidgets(
      'shows a loading indicator rather than crashing when no active '
      'organization is set', (tester) async {
    // Same "no active organization" guard as company_profile_screen_test.dart
    // -- _load() returns early, so the screen stays in its initial loading
    // state rather than attempting a request or crashing.
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: OpportunityListScreen()),
      ),
    );
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.text('Opportunities'), findsOneWidget);
    expect(find.text('New opportunity'), findsOneWidget);
  });
}
