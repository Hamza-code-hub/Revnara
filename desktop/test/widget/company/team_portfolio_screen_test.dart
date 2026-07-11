import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/features/company/team_portfolio_screen.dart';

void main() {
  testWidgets('renders all five tabs without crashing', (tester) async {
    // Same "no active organization" guard as company_profile_screen_test.dart
    // -- every tab's _load() returns early, so each tab renders its loading
    // state rather than attempting a request.
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: TeamPortfolioScreen()),
      ),
    );
    await tester.pump();

    expect(find.text('Team & portfolio'), findsOneWidget);
    expect(find.text('Team'), findsOneWidget);
    expect(find.text('Skills'), findsOneWidget);
    expect(find.text('Portfolio'), findsOneWidget);
    expect(find.text('Case studies'), findsOneWidget);
    expect(find.text('Files'), findsOneWidget);
  });

  testWidgets('switching tabs does not crash', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: TeamPortfolioScreen()),
      ),
    );
    await tester.pump();

    await tester.tap(find.text('Skills'));
    await tester.pump();
    await tester.tap(find.text('Files'));
    await tester.pump();

    expect(find.text('Files'), findsOneWidget);
  });
}
