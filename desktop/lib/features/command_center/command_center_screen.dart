import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../auth/membership_provider.dart';
import '../../shared/design_system/design_system.dart';

/// FE2.3's authenticated landing screen, now a real dashboard rather than
/// the Sprint 2 placeholder -- every number here comes from a real API
/// call (opportunity/team/skill/portfolio counts), not decorative fake
/// data. Deliberately does NOT try to show cost/agent-quality/system
/// health widgets -- that data doesn't exist until Sprint 14's agents
/// actually run and produce it (docs/Revnara_Sprint_Development_Plan.md's
/// `dashboard_screen.dart` task); a chart with no real data behind it
/// would just be decoration.
class CommandCenterScreen extends ConsumerStatefulWidget {
  const CommandCenterScreen({super.key});

  @override
  ConsumerState<CommandCenterScreen> createState() => _CommandCenterScreenState();
}

class _CommandCenterScreenState extends ConsumerState<CommandCenterScreen> {
  List<Opportunity>? _opportunities;
  int? _teamMemberCount;
  int? _skillCount;
  int? _portfolioItemCount;
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
      final results = await Future.wait([
        apiClient.listOpportunities(organizationId),
        apiClient.listTeamMembers(organizationId),
        apiClient.listSkills(organizationId),
        apiClient.listPortfolioItems(organizationId),
      ]);
      setState(() {
        _opportunities = results[0] as List<Opportunity>;
        _teamMemberCount = (results[1] as List).length;
        _skillCount = (results[2] as List).length;
        _portfolioItemCount = (results[3] as List).length;
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
    final me = ref.watch(meProvider);
    final activeMembership =
        me.valueOrNull?.memberships.where((m) => m.status == 'active').firstOrNull;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            icon: const Icon(Icons.refresh),
            onPressed: _isLoading ? null : _load,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? RevnaraEmptyState(
                  icon: Icons.error_outline,
                  title: 'Could not load your dashboard',
                  message: _error,
                )
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    padding: const EdgeInsets.all(RevnaraSpacing.lg),
                    children: [
                      Text(
                        'Welcome back${me.valueOrNull?.email != null ? ', ${me.valueOrNull!.email}' : ''}',
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                      const SizedBox(height: RevnaraSpacing.xs),
                      Row(
                        children: [
                          Text(
                            activeMembership?.organizationName ?? 'No organization',
                            style: Theme.of(context).textTheme.bodyLarge,
                          ),
                          if (activeMembership != null) ...[
                            const SizedBox(width: RevnaraSpacing.sm),
                            RevnaraStatusChip(
                              label: activeMembership.roleName,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: RevnaraSpacing.xl),
                      _StatGrid(
                        opportunities: _opportunities ?? [],
                        teamMemberCount: _teamMemberCount ?? 0,
                        skillCount: _skillCount ?? 0,
                        portfolioItemCount: _portfolioItemCount ?? 0,
                      ),
                      const SizedBox(height: RevnaraSpacing.xl),
                      Text('Pipeline by status', style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: RevnaraSpacing.sm),
                      _PipelineBreakdown(opportunities: _opportunities ?? []),
                      const SizedBox(height: RevnaraSpacing.xl),
                      Text('Quick actions', style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: RevnaraSpacing.sm),
                      Wrap(
                        spacing: RevnaraSpacing.sm,
                        runSpacing: RevnaraSpacing.sm,
                        children: [
                          RevnaraButton(
                            label: 'New opportunity',
                            icon: Icons.add,
                            onPressed: () => context.push('/opportunities/new'),
                          ),
                          RevnaraButton(
                            label: 'Invite team member',
                            icon: Icons.person_add_outlined,
                            variant: RevnaraButtonVariant.secondary,
                            onPressed: () => context.go('/settings/team'),
                          ),
                          RevnaraButton(
                            label: 'Edit company profile',
                            icon: Icons.business_outlined,
                            variant: RevnaraButtonVariant.secondary,
                            onPressed: () => context.go('/company/profile'),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
    );
  }
}

class _StatGrid extends StatelessWidget {
  const _StatGrid({
    required this.opportunities,
    required this.teamMemberCount,
    required this.skillCount,
    required this.portfolioItemCount,
  });

  final List<Opportunity> opportunities;
  final int teamMemberCount;
  final int skillCount;
  final int portfolioItemCount;

  @override
  Widget build(BuildContext context) {
    final flaggedCount =
        opportunities.where((o) => o.safetyScreeningStatus == 'screened_flagged').length;

    return Wrap(
      spacing: RevnaraSpacing.md,
      runSpacing: RevnaraSpacing.md,
      children: [
        _StatCard(
          icon: Icons.inbox_outlined,
          value: '${opportunities.length}',
          label: 'Opportunities',
          color: Theme.of(context).colorScheme.primary,
          onTap: () => context.go('/opportunities'),
        ),
        _StatCard(
          icon: Icons.flag_outlined,
          value: '$flaggedCount',
          label: 'Flagged for review',
          color: flaggedCount > 0 ? Colors.red : Theme.of(context).colorScheme.onSurfaceVariant,
          onTap: () => context.go('/opportunities'),
        ),
        _StatCard(
          icon: Icons.group_outlined,
          value: '$teamMemberCount',
          label: 'Team members',
          color: Theme.of(context).colorScheme.secondary,
          onTap: () => context.go('/company/brain'),
        ),
        _StatCard(
          icon: Icons.star_border,
          value: '$skillCount',
          label: 'Skills tracked',
          color: Theme.of(context).colorScheme.secondary,
          onTap: () => context.go('/company/brain'),
        ),
        _StatCard(
          icon: Icons.work_outline,
          value: '$portfolioItemCount',
          label: 'Portfolio items',
          color: Theme.of(context).colorScheme.secondary,
          onTap: () => context.go('/company/brain'),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.icon,
    required this.value,
    required this.label,
    required this.color,
    this.onTap,
  });

  final IconData icon;
  final String value;
  final String label;
  final Color color;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 190,
      child: RevnaraCard(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: RevnaraSpacing.sm),
            Text(
              value,
              style: Theme.of(context)
                  .textTheme
                  .headlineMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: RevnaraSpacing.xs),
            Text(
              label,
              style: Theme.of(context)
                  .textTheme
                  .bodySmall
                  ?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
            ),
          ],
        ),
      ),
    );
  }
}

class _PipelineBreakdown extends StatelessWidget {
  const _PipelineBreakdown({required this.opportunities});

  final List<Opportunity> opportunities;

  static const _statusOrder = [
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

  @override
  Widget build(BuildContext context) {
    if (opportunities.isEmpty) {
      return const RevnaraEmptyState(
        icon: Icons.inbox_outlined,
        title: 'No opportunities yet',
      );
    }

    final counts = <String, int>{};
    for (final opportunity in opportunities) {
      counts[opportunity.status] = (counts[opportunity.status] ?? 0) + 1;
    }

    return Wrap(
      spacing: RevnaraSpacing.sm,
      runSpacing: RevnaraSpacing.sm,
      children: [
        for (final status in _statusOrder)
          if (counts[status] != null)
            RevnaraStatusChip(
              label: '$status: ${counts[status]}',
              color: switch (status) {
                'won' => Colors.green,
                'lost' || 'disqualified' => Colors.red,
                'screening' => Colors.orange,
                _ => Theme.of(context).colorScheme.primary,
              },
            ),
      ],
    );
  }
}
