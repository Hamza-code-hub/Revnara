import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../auth/auth_repository.dart';
import '../../auth/membership_provider.dart';
import '../../shared/design_system/design_system.dart';

/// Placeholder authenticated landing screen (FE2.3) -- real Command
/// Center functionality (per docs/Revnara_Sprint_Development_Plan.md's
/// primary screens list) is built in a later sprint. This proves the
/// authenticated-route redirect works end to end and gives a real place
/// to reach the team management screen from.
class CommandCenterScreen extends ConsumerWidget {
  const CommandCenterScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final me = ref.watch(meProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Revnara'),
        actions: [
          IconButton(
            tooltip: 'Company profile',
            icon: const Icon(Icons.business_outlined),
            onPressed: () => context.go('/company/profile'),
          ),
          IconButton(
            tooltip: 'Team',
            icon: const Icon(Icons.group_outlined),
            onPressed: () => context.go('/settings/team'),
          ),
          IconButton(
            tooltip: 'Sign out',
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(authRepositoryProvider).signOut(),
          ),
        ],
      ),
      body: me.when(
        data: (data) {
          final activeMembership = data?.memberships
              .where((m) => m.status == 'active')
              .firstOrNull;
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  activeMembership?.organizationName ?? 'No organization',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: RevnaraSpacing.sm),
                Text('Signed in as ${data?.email ?? "unknown"}'),
                if (activeMembership != null) ...[
                  const SizedBox(height: RevnaraSpacing.sm),
                  RevnaraStatusChip(
                    label: activeMembership.roleName,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ],
              ],
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(child: Text('Failed to load: $error')),
      ),
    );
  }
}
