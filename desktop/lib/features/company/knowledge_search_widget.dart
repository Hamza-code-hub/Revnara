import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../shared/design_system/design_system.dart';

/// FE5.1: debug-only "Company Brain search preview" widget -- lets QA
/// enter a query and see matched chunks with their source, to sanity-check
/// retrieval quality and tenant isolation. Not a customer-facing feature
/// (see team_portfolio_screen.dart's `kDebugMode` gate on this tab).
class KnowledgeSearchWidget extends ConsumerStatefulWidget {
  const KnowledgeSearchWidget({super.key});

  @override
  ConsumerState<KnowledgeSearchWidget> createState() => _KnowledgeSearchWidgetState();
}

class _KnowledgeSearchWidgetState extends ConsumerState<KnowledgeSearchWidget> {
  final _queryController = TextEditingController();
  List<KnowledgeSearchResult>? _results;
  String? _error;
  bool _isSearching = false;

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  Future<void> _search() async {
    final organizationId = _organizationId;
    final query = _queryController.text.trim();
    if (organizationId == null || query.isEmpty) return;

    setState(() {
      _isSearching = true;
      _error = null;
    });
    try {
      final results =
          await ref.read(apiClientProvider).searchKnowledge(organizationId, query: query);
      setState(() => _results = results);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isSearching = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final results = _results ?? [];
    return ListView(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      children: [
        RevnaraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Debug: Company Brain search preview',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraTextField(
                label: 'Query',
                controller: _queryController,
                errorText: _error,
              ),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraButton(
                label: _isSearching ? 'Searching...' : 'Search',
                icon: Icons.search,
                onPressed: _isSearching ? null : _search,
              ),
            ],
          ),
        ),
        const SizedBox(height: RevnaraSpacing.md),
        if (_results != null && results.isEmpty)
          const RevnaraEmptyState(icon: Icons.search_off, title: 'No matching chunks'),
        for (final result in results)
          RevnaraCard(
            padding: EdgeInsets.zero,
            child: RevnaraListRow(
              title: result.chunkText,
              subtitle:
                  '${result.sourceType} • ${result.classification ?? 'public'} • distance ${result.distance.toStringAsFixed(4)}',
            ),
          ),
      ],
    );
  }
}
