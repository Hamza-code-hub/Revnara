import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:revnara/app/app.dart';

void main() {
  testWidgets('App boots to the placeholder login screen', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: RevnaraApp()));
    await tester.pumpAndSettle();

    expect(find.text('Revnara — sign in (Sprint 2)'), findsOneWidget);
  });
}
