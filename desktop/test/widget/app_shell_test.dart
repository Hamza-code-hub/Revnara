import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:revnara/app/app.dart';

void main() {
  testWidgets(
      'App boots to the login screen, showing the "not configured" state '
      'when no Supabase dart-defines are supplied (as in this test run)',
      (tester) async {
    await tester.pumpWidget(const ProviderScope(child: RevnaraApp()));
    await tester.pumpAndSettle();

    expect(find.text('Supabase is not configured'), findsOneWidget);
  });
}
