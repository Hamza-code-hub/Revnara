import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../shared/design_system/design_system.dart';

/// FE6.5: opportunity detail, including the client's research brief
/// (BE6.5b) -- fetched lazily via GET .../client, which generates and
/// persists the brief on first request if the client doesn't have one yet.
class OpportunityDetailScreen extends ConsumerStatefulWidget {
  const OpportunityDetailScreen({super.key, required this.opportunityId});

  final String opportunityId;

  @override
  ConsumerState<OpportunityDetailScreen> createState() => _OpportunityDetailScreenState();
}

class _OpportunityDetailScreenState extends ConsumerState<OpportunityDetailScreen> {
  Opportunity? _opportunity;
  Client? _client;
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
      final apiClient = ref.read(apiClientProvider);
      final opportunity = await apiClient.getOpportunity(organizationId, widget.opportunityId);
      Client? client;
      if (opportunity.clientId != null) {
        client = await apiClient.getOpportunityClient(organizationId, widget.opportunityId);
      }
      setState(() {
        _opportunity = opportunity;
        _client = client;
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
      appBar: AppBar(title: Text(_opportunity?.title ?? 'Opportunity')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? RevnaraEmptyState(
                  icon: Icons.error_outline,
                  title: 'Could not load opportunity',
                  message: _error,
                )
              : _buildDetail(context, _opportunity!),
    );
  }

  Widget _buildDetail(BuildContext context, Opportunity opportunity) {
    return ListView(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      children: [
        RevnaraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  RevnaraStatusChip(
                    label: opportunity.status,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(width: RevnaraSpacing.xs),
                  RevnaraStatusChip(
                    label: opportunity.safetyScreeningStatus,
                    color: opportunity.safetyScreeningStatus == 'screened_flagged'
                        ? Colors.red
                        : Colors.green,
                    icon: opportunity.safetyScreeningStatus == 'screened_flagged'
                        ? Icons.flag_outlined
                        : Icons.check_circle_outline,
                  ),
                ],
              ),
              if (opportunity.safetyScreeningFlags != null &&
                  opportunity.safetyScreeningFlags!.isNotEmpty) ...[
                const SizedBox(height: RevnaraSpacing.sm),
                Text(
                  'Flags: ${opportunity.safetyScreeningFlags!.join(', ')}',
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ],
              if (opportunity.description != null) ...[
                const SizedBox(height: RevnaraSpacing.md),
                Text('Description', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: RevnaraSpacing.xs),
                Text(opportunity.description!),
              ],
              if (opportunity.requirements != null) ...[
                const SizedBox(height: RevnaraSpacing.md),
                Text('Requirements', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: RevnaraSpacing.xs),
                Text(opportunity.requirements!),
              ],
              if (opportunity.budgetMin != null || opportunity.budgetMax != null) ...[
                const SizedBox(height: RevnaraSpacing.md),
                Text('Budget', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: RevnaraSpacing.xs),
                Text(
                  '${opportunity.budgetCurrency ?? ''} '
                  '${opportunity.budgetMin?.toStringAsFixed(0) ?? '?'} - '
                  '${opportunity.budgetMax?.toStringAsFixed(0) ?? '?'}',
                ),
              ],
            ],
          ),
        ),
        if (_client != null) ...[
          const SizedBox(height: RevnaraSpacing.md),
          RevnaraCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_client!.name, style: Theme.of(context).textTheme.titleMedium),
                if (_client!.industry != null || _client!.region != null)
                  Text(
                    [_client!.industry, _client!.region].where((s) => s != null).join(' • '),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                const SizedBox(height: RevnaraSpacing.sm),
                Text('Research brief', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: RevnaraSpacing.xs),
                Text(_client!.researchBrief ?? 'No prior history with this client yet.'),
              ],
            ),
          ),
        ],
      ],
    );
  }
}
