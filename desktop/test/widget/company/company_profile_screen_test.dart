import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/features/company/company_profile_screen.dart';

void main() {
  testWidgets(
      'shows a loading indicator rather than crashing when no active '
      'organization is set', (tester) async {
    // activeOrganizationIdProvider defaults to null (no active org selected
    // yet) -- _load() returns early in that case, matching every other
    // Sprint 4 screen's guard, so the screen should stay in its initial
    // loading state rather than attempting a request or crashing.
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: CompanyProfileScreen()),
      ),
    );
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.text('Company profile'), findsOneWidget);
  });
}
