import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/features/settings/login_screen.dart';

void main() {
  Future<void> pumpForm(WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: Scaffold(body: Center(child: LoginForm()))),
      ),
    );
  }

  testWidgets('submitting an empty form shows both required errors',
      (tester) async {
    await pumpForm(tester);

    await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
    await tester.pump();

    expect(find.text('Email is required'), findsOneWidget);
    expect(find.text('Password is required'), findsOneWidget);
  });

  testWidgets('entering only an email still shows the password error',
      (tester) async {
    await pumpForm(tester);

    await tester.enterText(find.widgetWithText(TextField, 'Email'), 'user@example.com');
    await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
    await tester.pump();

    expect(find.text('Email is required'), findsNothing);
    expect(find.text('Password is required'), findsOneWidget);
  });

  testWidgets(
      'entering both fields clears validation errors, and an unreachable '
      'Supabase surfaces as a form error rather than crashing', (tester) async {
    await pumpForm(tester);

    // Trigger errors first.
    await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
    await tester.pump();
    expect(find.text('Email is required'), findsOneWidget);

    await tester.enterText(find.widgetWithText(TextField, 'Email'), 'user@example.com');
    await tester.enterText(find.widgetWithText(TextField, 'Password'), 'hunter2');
    await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
    await tester.pump();

    expect(find.text('Email is required'), findsNothing);
    expect(find.text('Password is required'), findsNothing);

    // Supabase was never initialized in this test environment (no
    // Supabase.initialize() call, unlike main.dart) -- the sign-in
    // attempt fails, and per the fallback `catch` in login_screen.dart
    // that failure must surface as a readable form error, not an
    // unhandled exception that would fail this test outright.
    await tester.pump();
    expect(find.textContaining('Sign-in failed'), findsOneWidget);
  });
}
