import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/api/api_client.dart';
import 'package:revnara/app/global_error_listener.dart';

void main() {
  testWidgets('shows a toast when unauthorizedEventProvider is set',
      (tester) async {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const MaterialApp(
          home: Scaffold(
            body: GlobalErrorListener(child: Text('screen content')),
          ),
        ),
      ),
    );

    expect(find.text('screen content'), findsOneWidget);
    expect(find.text('Missing permission: members.invite'), findsNothing);

    container.read(unauthorizedEventProvider.notifier).state =
        'Missing permission: members.invite';
    await tester.pump();

    expect(find.text('Missing permission: members.invite'), findsOneWidget);
  });

  testWidgets('a second identical 403 message re-triggers the toast',
      (tester) async {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const MaterialApp(
          home: Scaffold(
            body: GlobalErrorListener(child: SizedBox.shrink()),
          ),
        ),
      ),
    );

    container.read(unauthorizedEventProvider.notifier).state = 'Forbidden';
    await tester.pump();
    expect(find.text('Forbidden'), findsOneWidget);

    // Let the microtask reset unauthorizedEventProvider back to null.
    await tester.pump();
    // Dismiss the first toast so the second is unambiguous to find.
    await tester.pump(const Duration(seconds: 5));

    container.read(unauthorizedEventProvider.notifier).state = 'Forbidden';
    await tester.pump();
    expect(find.text('Forbidden'), findsOneWidget);
  });
}
