import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:revnara/shared/design_system/reference_layouts/form_reference.dart';
import 'package:revnara/shared/design_system/reference_layouts/list_detail_reference.dart';

/// DS1.10's regression anchor: reference layouts reflow at compact, medium,
/// and expanded widths with no overflow -- the concrete test for "no
/// fixed-size scrollable container standing in for content that should
/// adapt" (§11 Master DoD, UI/Motion/Performance).
void main() {
  Future<void> pumpAtWidth(
    WidgetTester tester,
    double width,
    Widget child,
  ) async {
    tester.view.physicalSize = Size(width, 900) * tester.view.devicePixelRatio;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: SizedBox(height: 600, child: child)),
      ),
    );
    await tester.pumpAndSettle();
  }

  group('ListDetailReference', () {
    for (final width in [375.0, 800.0, 1440.0]) {
      testWidgets('renders with no overflow at ${width}px', (tester) async {
        await pumpAtWidth(tester, width, const ListDetailReference());
        expect(tester.takeException(), isNull);
      });
    }

    testWidgets('compact width shows a single pane (no divider)',
        (tester) async {
      await pumpAtWidth(tester, 375, const ListDetailReference());
      expect(find.byType(VerticalDivider), findsNothing);
      expect(find.text('Sample item 1'), findsOneWidget);
    });

    testWidgets('expanded width shows list and detail panes at once',
        (tester) async {
      await pumpAtWidth(tester, 1440, const ListDetailReference());
      expect(find.byType(VerticalDivider), findsOneWidget);
      // Both the list (item text) and the empty detail placeholder are
      // visible simultaneously -- proof the two panes render side by side
      // rather than one replacing the other.
      expect(find.text('Sample item 1'), findsOneWidget);
      expect(find.text('Select an item'), findsOneWidget);
    });

    testWidgets('compact width: selecting an item swaps to a detail pane '
        'with a back affordance', (tester) async {
      await pumpAtWidth(tester, 375, const ListDetailReference());
      await tester.tap(find.text('Sample item 1'));
      await tester.pumpAndSettle();

      expect(find.text('Back to list'), findsOneWidget);
      expect(find.text('Sample item 2'), findsNothing);
    });
  });

  group('FormReference', () {
    for (final width in [375.0, 800.0, 1440.0]) {
      testWidgets('renders with no overflow at ${width}px', (tester) async {
        await pumpAtWidth(tester, width, const FormReference());
        expect(tester.takeException(), isNull);
      });
    }

    testWidgets('compact width stacks fields in a single column',
        (tester) async {
      await pumpAtWidth(tester, 375, const FormReference());

      final firstNameTop =
          tester.getTopLeft(find.widgetWithText(TextField, 'First name'));
      final lastNameTop =
          tester.getTopLeft(find.widgetWithText(TextField, 'Last name'));

      // Single column: stacked fields have the same x, different y.
      expect(firstNameTop.dx, closeTo(lastNameTop.dx, 1));
      expect(firstNameTop.dy, lessThan(lastNameTop.dy));
    });

    testWidgets('expanded width arranges fields in two columns',
        (tester) async {
      await pumpAtWidth(tester, 1440, const FormReference());

      final firstNameTop =
          tester.getTopLeft(find.widgetWithText(TextField, 'First name'));
      final lastNameTop =
          tester.getTopLeft(find.widgetWithText(TextField, 'Last name'));

      // Two columns: fields on the same row have the same y, different x.
      expect(firstNameTop.dy, closeTo(lastNameTop.dy, 1));
      expect(firstNameTop.dx, lessThan(lastNameTop.dx));
    });
  });
}
