import 'package:flutter/material.dart';

import '../components/buttons.dart';
import '../components/inputs.dart';
import '../layout/breakpoints.dart';
import '../tokens.dart';

/// Reference form layout (DS1.10). Single column at compact width;
/// two-column at medium/expanded -- fields group with [Wrap] sized by
/// fraction of available width, never a fixed pixel field width.
class FormReference extends StatelessWidget {
  const FormReference({super.key});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final breakpoint = RevnaraBreakpoint.fromWidth(constraints.maxWidth);
        final columns = breakpoint.isCompact ? 1 : 2;
        // Subtract the SingleChildScrollView's own horizontal padding below
        // -- the available width for the Wrap's children is narrower than
        // constraints.maxWidth by that padding, and missing this caused
        // fields to overflow their row and wrap early even at expanded
        // width (caught by the adaptive-layout test, not by eye).
        final availableWidth = constraints.maxWidth - (RevnaraSpacing.md * 2);
        final fieldWidth =
            (availableWidth - (RevnaraSpacing.md * (columns - 1))) / columns;

        return SingleChildScrollView(
          padding: const EdgeInsets.all(RevnaraSpacing.md),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: RevnaraSpacing.md,
                runSpacing: RevnaraSpacing.md,
                children: [
                  SizedBox(
                    width: fieldWidth,
                    child: const RevnaraTextField(label: 'First name'),
                  ),
                  SizedBox(
                    width: fieldWidth,
                    child: const RevnaraTextField(label: 'Last name'),
                  ),
                  SizedBox(
                    width: fieldWidth,
                    child: const RevnaraTextField(label: 'Email'),
                  ),
                  SizedBox(
                    width: fieldWidth,
                    child: const RevnaraTextField(label: 'Role'),
                  ),
                ],
              ),
              const SizedBox(height: RevnaraSpacing.lg),
              RevnaraButton(label: 'Submit', onPressed: () {}),
            ],
          ),
        );
      },
    );
  }
}
