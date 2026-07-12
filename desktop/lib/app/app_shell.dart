import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../auth/auth_repository.dart';
import '../auth/membership_provider.dart';
import '../shared/design_system/design_system.dart';
import 'theme_mode_provider.dart';

class _NavItem {
  const _NavItem({required this.icon, required this.label, required this.route});

  final IconData icon;
  final String label;
  final String route;
}

const _navItems = [
  _NavItem(icon: Icons.dashboard_outlined, label: 'Dashboard', route: '/command-center'),
  _NavItem(icon: Icons.inbox_outlined, label: 'Opportunities', route: '/opportunities'),
  _NavItem(icon: Icons.business_outlined, label: 'Company Profile', route: '/company/profile'),
  _NavItem(icon: Icons.workspaces_outlined, label: 'Team & Brain', route: '/company/brain'),
  _NavItem(icon: Icons.group_outlined, label: 'Team Management', route: '/settings/team'),
];

/// FE-wide persistent navigation shell -- wraps every authenticated
/// top-level screen (via GoRouter's ShellRoute, see router.dart) in a
/// sidebar so navigation doesn't rely on each screen carrying its own ad
/// hoc AppBar icon buttons. Deliberately excludes focused sub-flows
/// (opportunity create/detail) -- those stay full-screen outside the
/// shell, a common desktop pattern (list views get persistent nav,
/// create/detail flows get full focus).
class AppShell extends ConsumerWidget {
  const AppShell({super.key, required this.child, required this.location});

  final Widget child;
  final String location;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _Sidebar(location: location),
          const VerticalDivider(width: 1),
          Expanded(child: child),
        ],
      ),
    );
  }
}

class _Sidebar extends ConsumerWidget {
  const _Sidebar({required this.location});

  final String location;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final me = ref.watch(meProvider);
    final themeMode = ref.watch(themeModeProvider);
    final activeMembership =
        me.valueOrNull?.memberships.where((m) => m.status == 'active').firstOrNull;

    return Container(
      width: 264,
      color: theme.colorScheme.surfaceContainerLow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(
              RevnaraSpacing.lg,
              RevnaraSpacing.xl,
              RevnaraSpacing.lg,
              RevnaraSpacing.md,
            ),
            child: Row(
              children: [
                Icon(Icons.shield_outlined, color: theme.colorScheme.primary, size: 28),
                const SizedBox(width: RevnaraSpacing.sm),
                Text(
                  'Revnara',
                  style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),
          if (activeMembership != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: RevnaraSpacing.md),
              child: RevnaraCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      activeMembership.organizationName,
                      style: theme.textTheme.titleSmall,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: RevnaraSpacing.xs),
                    RevnaraStatusChip(
                      label: activeMembership.roleName,
                      color: theme.colorScheme.primary,
                    ),
                  ],
                ),
              ),
            ),
          const SizedBox(height: RevnaraSpacing.md),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(horizontal: RevnaraSpacing.sm),
              children: [
                for (final item in _navItems)
                  _SidebarNavTile(item: item, isActive: location.startsWith(item.route)),
              ],
            ),
          ),
          const Divider(height: 1),
          ListTile(
            leading: Icon(
              themeMode == ThemeMode.dark ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
            ),
            title: Text(themeMode == ThemeMode.dark ? 'Light mode' : 'Dark mode'),
            onTap: () => ref.read(themeModeProvider.notifier).toggle(),
          ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Sign out'),
            onTap: () => ref.read(authRepositoryProvider).signOut(),
          ),
          const SizedBox(height: RevnaraSpacing.sm),
        ],
      ),
    );
  }
}

class _SidebarNavTile extends StatelessWidget {
  const _SidebarNavTile({required this.item, required this.isActive});

  final _NavItem item;
  final bool isActive;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final foreground =
        isActive ? theme.colorScheme.onPrimaryContainer : theme.colorScheme.onSurfaceVariant;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Material(
        color: isActive ? theme.colorScheme.primaryContainer : Colors.transparent,
        borderRadius: BorderRadius.circular(RevnaraRadius.md),
        child: InkWell(
          borderRadius: BorderRadius.circular(RevnaraRadius.md),
          onTap: () => context.go(item.route),
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: RevnaraSpacing.md,
              vertical: RevnaraSpacing.sm,
            ),
            child: Row(
              children: [
                Icon(item.icon, size: 20, color: foreground),
                const SizedBox(width: RevnaraSpacing.sm),
                Expanded(
                  child: Text(
                    item.label,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: foreground,
                      fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
