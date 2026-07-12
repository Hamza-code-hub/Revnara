import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../shared/design_system/design_system.dart';

Color _statusColor(BuildContext context, String status) {
  switch (status) {
    case 'won':
      return Colors.green;
    case 'lost':
    case 'disqualified':
      return Colors.red;
    case 'screening':
      return Colors.orange;
    default:
      return Theme.of(context).colorScheme.primary;
  }
}

/// FE6.6: the opportunity pipeline list -- every opportunity across all
/// three intake paths (manual, Upwork link, CSV import) lands here in one
/// place, since `status`/`safety_screening_status` are the same two
/// dimensions regardless of how the row was created.
class OpportunityListScreen extends ConsumerStatefulWidget {
  const OpportunityListScreen({super.key});

  @override
  ConsumerState<OpportunityListScreen> createState() => _OpportunityListScreenState();
}

class _OpportunityListScreenState extends ConsumerState<OpportunityListScreen> {
  List<Opportunity>? _opportunities;
  String? _error;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  Future<void> _load() async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    setState(() => _isLoading = true);
    try {
      final opportunities = await ref.read(apiClientProvider).listOpportunities(organizationId);
      setState(() {
        _opportunities = opportunities;
        _error = null;
      });
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Opportunities')),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.add),
        label: const Text('New opportunity'),
        onPressed: () async {
          await context.push('/opportunities/new');
          _load();
        },
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? RevnaraEmptyState(
                  icon: Icons.error_outline,
                  title: 'Could not load opportunities',
                  message: _error,
                )
              : RefreshIndicator(
                  onRefresh: _load,
                  child: (_opportunities ?? []).isEmpty
                      ? ListView(
                          children: const [
                            RevnaraEmptyState(
                              icon: Icons.inbox_outlined,
                              title: 'No opportunities yet',
                              message: 'Add one manually, paste an Upwork link, or import a CSV.',
                            ),
                          ],
                        )
                      : ListView(
                          padding: const EdgeInsets.all(RevnaraSpacing.md),
                          children: [
                            for (final opportunity in _opportunities!)
                              RevnaraCard(
                                padding: EdgeInsets.zero,
                                child: RevnaraListRow(
                                  title: opportunity.title,
                                  subtitle: opportunity.budgetMin != null
                                      ? '${opportunity.budgetCurrency ?? ''} ${opportunity.budgetMin?.toStringAsFixed(0)}-${opportunity.budgetMax?.toStringAsFixed(0)}'
                                      : null,
                                  trailing: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      if (opportunity.safetyScreeningStatus == 'screened_flagged')
                                        const Padding(
                                          padding: EdgeInsets.only(right: RevnaraSpacing.xs),
                                          child: RevnaraStatusChip(
                                            label: 'Flagged',
                                            color: Colors.red,
                                            icon: Icons.flag_outlined,
                                          ),
                                        ),
                                      RevnaraStatusChip(
                                        label: opportunity.status,
                                        color: _statusColor(context, opportunity.status),
                                      ),
                                    ],
                                  ),
                                  onTap: () async {
                                    await context.push('/opportunities/${opportunity.id}');
                                    _load();
                                  },
                                ),
                              ),
                          ],
                        ),
                ),
    );
  }
}
