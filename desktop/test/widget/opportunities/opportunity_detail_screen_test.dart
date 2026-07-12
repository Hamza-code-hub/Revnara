import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/features/opportunities/opportunity_detail_screen.dart';

void main() {
  testWidgets(
      'shows a loading indicator rather than crashing when no active '
      'organization is set', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: OpportunityDetailScreen(opportunityId: 'does-not-matter'),
        ),
      ),
    );
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
