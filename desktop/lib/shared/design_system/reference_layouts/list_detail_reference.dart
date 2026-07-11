import 'package:flutter/material.dart';

import '../components/list_row.dart';
import '../layout/breakpoints.dart';
import '../tokens.dart';

/// Reference list/detail layout (DS1.10) -- the pattern every Sprint 6+
/// opportunity/proposal/approval screen builds on. Demonstrates the rule
/// this sprint exists to enforce: no fixed-size scrollable panel standing
/// in for content that should adapt.
///
/// - Compact: single pane. Selecting an item swaps the list for the detail
///   (with a back affordance), rather than shrinking both into a cramped
///   fixed-width split.
/// - Medium/expanded: list and detail side by side, both sized with
///   [Expanded] -- proportions adapt continuously with window width, they
///   are never a hardcoded pixel split.
class ListDetailReference extends StatefulWidget {
  const ListDetailReference({super.key});

  @override
  State<ListDetailReference> createState() => _ListDetailReferenceState();
}

class _ListDetailReferenceState extends State<ListDetailReference> {
  int? _selected;

  static final _items = List.generate(6, (i) => 'Sample item ${i + 1}');

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final breakpoint = RevnaraBreakpoint.fromWidth(constraints.maxWidth);

        final list = _buildList(context);
        final detail = _buildDetail(context);

        if (breakpoint.isCompact) {
          return _selected == null ? list : detail;
        }

        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(flex: 2, child: list),
            const VerticalDivider(width: 1),
            Expanded(flex: 3, child: detail),
          ],
        );
      },
    );
  }

  Widget _buildList(BuildContext context) {
    return ListView.builder(
      itemCount: _items.length,
      itemBuilder: (context, index) => RevnaraListRow(
        title: _items[index],
        subtitle: 'Reference row subtitle',
        onTap: () => setState(() => _selected = index),
      ),
    );
  }

  Widget _buildDetail(BuildContext context) {
    if (_selected == null) {
      return const Center(child: Text('Select an item'));
    }
    return Padding(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (RevnaraBreakpoint.of(context).isCompact)
            TextButton.icon(
              onPressed: () => setState(() => _selected = null),
              icon: const Icon(Icons.arrow_back),
              label: const Text('Back to list'),
            ),
          Text(
            _items[_selected!],
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: RevnaraSpacing.sm),
          const Text('Detail content adapts to the space it is given.'),
        ],
      ),
    );
  }
}
