import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../shared/design_system/design_system.dart';

const _allStatuses = [
  'intake',
  'screening',
  'qualifying',
  'qualified',
  'matched',
  'proposing',
  'approved',
  'submitted',
  'won',
  'lost',
  'disqualified',
];

Color _riskColor(String risk) {
  switch (risk) {
    case 'low':
      return Colors.green;
    case 'medium':
      return Colors.orange;
    default:
      return Colors.red;
  }
}

/// FE6.5/FE7.2/FE7.2b: opportunity detail -- client research brief
/// (BE6.5b), qualification score with an expandable "why" panel reading
/// from explainability_records (BE7.2), team match recommendation with
/// delivery risk, and override controls for both (BE7.6) that always show
/// an "adjusted by" indicator wherever a human has corrected the AI
/// output, never hiding that trail in an audit log only a developer would
/// check.
class OpportunityDetailScreen extends ConsumerStatefulWidget {
  const OpportunityDetailScreen({super.key, required this.opportunityId});

  final String opportunityId;

  @override
  ConsumerState<OpportunityDetailScreen> createState() => _OpportunityDetailScreenState();
}

class _OpportunityDetailScreenState extends ConsumerState<OpportunityDetailScreen> {
  Opportunity? _opportunity;
  Client? _client;
  QualificationResult? _qualification;
  ExplainabilityRecord? _qualificationExplainability;
  List<OverrideRecord> _qualificationOverrides = [];
  TeamMatchResult? _teamMatch;
  ExplainabilityRecord? _teamMatchExplainability;
  List<OverrideRecord> _teamMatchOverrides = [];
  List<TeamMember> _teamMembers = [];

  String? _error;
  bool _isLoading = true;
  bool _isQualifying = false;
  bool _isMatchingTeam = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  String _teamMemberName(String id) {
    final member = _teamMembers.where((m) => m.id == id).firstOrNull;
    return member?.name ?? id;
  }

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
      final teamMembers = await apiClient.listTeamMembers(organizationId);
      final qualification =
          await apiClient.getQualificationResult(organizationId, widget.opportunityId);
      final qualificationExplainability = qualification == null
          ? null
          : await apiClient.getQualificationExplainability(organizationId, widget.opportunityId);
      final qualificationOverrides = qualification == null
          ? <OverrideRecord>[]
          : await apiClient.listQualificationOverrides(organizationId, widget.opportunityId);
      final teamMatch = await apiClient.getTeamMatchResult(organizationId, widget.opportunityId);
      final teamMatchExplainability = teamMatch == null
          ? null
          : await apiClient.getTeamMatchExplainability(organizationId, widget.opportunityId);
      final teamMatchOverrides = teamMatch == null
          ? <OverrideRecord>[]
          : await apiClient.listTeamMatchOverrides(organizationId, widget.opportunityId);

      setState(() {
        _opportunity = opportunity;
        _client = client;
        _teamMembers = teamMembers;
        _qualification = qualification;
        _qualificationExplainability = qualificationExplainability;
        _qualificationOverrides = qualificationOverrides;
        _teamMatch = teamMatch;
        _teamMatchExplainability = teamMatchExplainability;
        _teamMatchOverrides = teamMatchOverrides;
        _error = null;
      });
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _changeStatus() async {
    final organizationId = _organizationId;
    if (organizationId == null || _opportunity == null) return;
    final newStatus = await _showStatusDialog(context, current: _opportunity!.status);
    if (newStatus == null) return;

    try {
      await ref
          .read(apiClientProvider)
          .updateOpportunityStatus(organizationId, widget.opportunityId, newStatus: newStatus);
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  Future<void> _qualify() async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    setState(() => _isQualifying = true);
    try {
      await ref.read(apiClientProvider).qualifyOpportunity(organizationId, widget.opportunityId);
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    } finally {
      if (mounted) setState(() => _isQualifying = false);
    }
  }

  Future<void> _matchTeam() async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    setState(() => _isMatchingTeam = true);
    try {
      await ref
          .read(apiClientProvider)
          .matchTeamForOpportunity(organizationId, widget.opportunityId);
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    } finally {
      if (mounted) setState(() => _isMatchingTeam = false);
    }
  }

  Future<void> _overrideQualification() async {
    final organizationId = _organizationId;
    if (organizationId == null || _qualification == null) return;
    final result = await _showQualificationOverrideDialog(context, current: _qualification!.score);
    if (result == null) return;

    try {
      await ref.read(apiClientProvider).overrideQualification(
            organizationId,
            widget.opportunityId,
            score: result.$1,
            reason: result.$2,
          );
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  Future<void> _overrideTeamMatch() async {
    final organizationId = _organizationId;
    if (organizationId == null || _teamMatch == null) return;
    final result = await _showTeamMatchOverrideDialog(
      context,
      teamMembers: _teamMembers,
      current: _teamMatch!.recommendedTeamMemberIds,
    );
    if (result == null) return;

    try {
      await ref.read(apiClientProvider).overrideTeamMatch(
            organizationId,
            widget.opportunityId,
            recommendedTeamMemberIds: result.$1,
            reason: result.$2,
          );
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
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
                  const Spacer(),
                  TextButton(onPressed: _changeStatus, child: const Text('Change status')),
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
        const SizedBox(height: RevnaraSpacing.md),
        _buildQualificationCard(context),
        const SizedBox(height: RevnaraSpacing.md),
        _buildTeamMatchCard(context),
      ],
    );
  }

  Widget _buildQualificationCard(BuildContext context) {
    final qualification = _qualification;
    final latestOverride = _qualificationOverrides.firstOrNull;

    return RevnaraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('Qualification', style: Theme.of(context).textTheme.titleMedium),
              const Spacer(),
              RevnaraButton(
                label: _isQualifying
                    ? 'Qualifying...'
                    : qualification == null
                        ? 'Qualify'
                        : 'Re-qualify',
                variant: RevnaraButtonVariant.secondary,
                onPressed: _isQualifying ? null : _qualify,
              ),
            ],
          ),
          if (qualification == null)
            const Padding(
              padding: EdgeInsets.only(top: RevnaraSpacing.xs),
              child: Text('Not yet qualified.'),
            )
          else ...[
            const SizedBox(height: RevnaraSpacing.sm),
            Row(
              children: [
                Text('${qualification.score}/100',
                    style: Theme.of(context).textTheme.headlineSmall),
                const Spacer(),
                TextButton(
                  onPressed: _overrideQualification,
                  child: const Text('Override score'),
                ),
              ],
            ),
            if (latestOverride != null)
              Text(
                'Adjusted by a reviewer: ${latestOverride.originalValue} → '
                '${latestOverride.newValue} -- ${latestOverride.reason}',
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(fontStyle: FontStyle.italic),
              ),
            if (qualification.missingInfo.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: RevnaraSpacing.xs),
                child: Text(
                  'Missing info: ${qualification.missingInfo.join('; ')}',
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            ExpansionTile(
              title: const Text('Why this score?'),
              tilePadding: EdgeInsets.zero,
              childrenPadding: EdgeInsets.zero,
              children: [
                for (final reason in qualification.reasons)
                  Padding(
                    padding: const EdgeInsets.only(bottom: RevnaraSpacing.xs),
                    child: Text('• $reason'),
                  ),
                if (qualification.evidence.isNotEmpty) ...[
                  Text('Evidence', style: Theme.of(context).textTheme.labelMedium),
                  for (final evidence in qualification.evidence) Text('• $evidence'),
                ],
                if (_qualificationExplainability != null)
                  Padding(
                    padding: const EdgeInsets.only(top: RevnaraSpacing.xs),
                    child: Text(
                      'Confidence: '
                      '${(_qualificationExplainability!.confidence * 100).toStringAsFixed(0)}%',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildTeamMatchCard(BuildContext context) {
    final teamMatch = _teamMatch;
    final latestOverride = _teamMatchOverrides.firstOrNull;

    return RevnaraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('Team match', style: Theme.of(context).textTheme.titleMedium),
              const Spacer(),
              RevnaraButton(
                label: _isMatchingTeam
                    ? 'Matching...'
                    : teamMatch == null
                        ? 'Match team'
                        : 'Re-match',
                variant: RevnaraButtonVariant.secondary,
                onPressed: _isMatchingTeam ? null : _matchTeam,
              ),
            ],
          ),
          if (teamMatch == null)
            const Padding(
              padding: EdgeInsets.only(top: RevnaraSpacing.xs),
              child: Text('No team match yet.'),
            )
          else ...[
            const SizedBox(height: RevnaraSpacing.sm),
            Row(
              children: [
                RevnaraStatusChip(
                  label: '${teamMatch.deliveryRisk} risk',
                  color: _riskColor(teamMatch.deliveryRisk),
                ),
                const Spacer(),
                TextButton(onPressed: _overrideTeamMatch, child: const Text('Override team')),
              ],
            ),
            const SizedBox(height: RevnaraSpacing.xs),
            if (teamMatch.recommendedTeamMemberIds.isEmpty)
              const Text('No team member recommended.')
            else
              Text(
                'Recommended: ${teamMatch.recommendedTeamMemberIds.map(_teamMemberName).join(', ')}',
              ),
            if (teamMatch.estimatedWeeklyCost != null)
              Text(
                'Estimated weekly cost: ${teamMatch.estimatedCostCurrency ?? ''} '
                '${teamMatch.estimatedWeeklyCost!.toStringAsFixed(0)}',
              ),
            if (latestOverride != null)
              Text(
                'Adjusted by a reviewer -- ${latestOverride.reason}',
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(fontStyle: FontStyle.italic),
              ),
            if (teamMatch.gaps.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: RevnaraSpacing.xs),
                child: Text(
                  'Skill gaps: ${teamMatch.gaps.join(', ')}',
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            ExpansionTile(
              title: const Text('Why this recommendation?'),
              tilePadding: EdgeInsets.zero,
              childrenPadding: EdgeInsets.zero,
              children: [
                for (final reason in teamMatch.reasons)
                  Padding(
                    padding: const EdgeInsets.only(bottom: RevnaraSpacing.xs),
                    child: Text('• $reason'),
                  ),
                if (teamMatch.evidence.isNotEmpty) ...[
                  Text('Evidence', style: Theme.of(context).textTheme.labelMedium),
                  for (final evidence in teamMatch.evidence) Text('• $evidence'),
                ],
                if (_teamMatchExplainability != null)
                  Padding(
                    padding: const EdgeInsets.only(top: RevnaraSpacing.xs),
                    child: Text(
                      'Confidence: '
                      '${(_teamMatchExplainability!.confidence * 100).toStringAsFixed(0)}%',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

Future<String?> _showStatusDialog(BuildContext context, {required String current}) {
  var selected = current;
  return showDialog<String>(
    context: context,
    builder: (context) => StatefulBuilder(
      builder: (context, setDialogState) => AlertDialog(
        title: const Text('Change status'),
        content: RevnaraSelectField<String>(
          label: 'New status',
          value: selected,
          items: _allStatuses,
          itemLabel: (s) => s,
          onChanged: (value) => setDialogState(() => selected = value ?? selected),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () => Navigator.pop(context, selected),
            child: const Text('Save'),
          ),
        ],
      ),
    ),
  );
}

Future<(int, String)?> _showQualificationOverrideDialog(
  BuildContext context, {
  required int current,
}) {
  final scoreController = TextEditingController(text: current.toString());
  final reasonController = TextEditingController();
  return showDialog<(int, String)>(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text('Override qualification score'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          RevnaraTextField(
            label: 'New score (0-100)',
            controller: scoreController,
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: RevnaraSpacing.sm),
          RevnaraTextField(
            label: 'Reason (required)',
            controller: reasonController,
            maxLines: 3,
          ),
        ],
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton(
          onPressed: () {
            final score = int.tryParse(scoreController.text.trim());
            final reason = reasonController.text.trim();
            if (score == null || reason.isEmpty) return;
            Navigator.pop(context, (score, reason));
          },
          child: const Text('Save'),
        ),
      ],
    ),
  );
}

Future<(List<String>, String)?> _showTeamMatchOverrideDialog(
  BuildContext context, {
  required List<TeamMember> teamMembers,
  required List<String> current,
}) {
  final selected = {...current};
  final reasonController = TextEditingController();
  return showDialog<(List<String>, String)>(
    context: context,
    builder: (context) => StatefulBuilder(
      builder: (context, setDialogState) => AlertDialog(
        title: const Text('Override team selection'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              for (final member in teamMembers)
                CheckboxListTile(
                  title: Text(member.name),
                  value: selected.contains(member.id),
                  onChanged: (checked) => setDialogState(() {
                    if (checked ?? false) {
                      selected.add(member.id);
                    } else {
                      selected.remove(member.id);
                    }
                  }),
                ),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraTextField(
                label: 'Reason (required)',
                controller: reasonController,
                maxLines: 3,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              final reason = reasonController.text.trim();
              if (reason.isEmpty) return;
              Navigator.pop(context, (selected.toList(), reason));
            },
            child: const Text('Save'),
          ),
        ],
      ),
    ),
  );
}
