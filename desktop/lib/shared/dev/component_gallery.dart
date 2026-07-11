import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/theme_mode_provider.dart';
import '../design_system/design_system.dart';
import '../design_system/reference_layouts/form_reference.dart';
import '../design_system/reference_layouts/list_detail_reference.dart';
import '../motion/transitions.dart';

/// Debug-only screen exercising every design-system component, state, and
/// animation (DS1.8) -- the target of Sprint 1.5's golden tests and the
/// place a design/TL review happens before Sprint 2 builds real screens.
/// Reachable via the hidden `/dev/gallery` route (never linked from normal
/// app navigation).
class ComponentGalleryScreen extends ConsumerWidget {
  const ComponentGalleryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Component Gallery'),
        actions: [
          IconButton(
            tooltip: 'Toggle light/dark',
            icon: Icon(
              themeMode == ThemeMode.dark
                  ? Icons.dark_mode
                  : Icons.light_mode,
            ),
            onPressed: () =>
                ref.read(themeModeProvider.notifier).toggle(),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(RevnaraSpacing.lg),
        children: const [
          _Section(title: 'Risk tiers (R0-R6)', child: _RiskTierRow()),
          _Section(title: 'Governance badges', child: _GovernanceBadgeRow()),
          _Section(title: 'Buttons', child: _ButtonRow()),
          _Section(title: 'Inputs', child: _InputColumn()),
          _Section(title: 'Cards', child: _CardExample()),
          _Section(title: 'List rows', child: _ListRowExample()),
          _Section(title: 'Empty state', child: _EmptyStateExample()),
          _Section(title: 'Loading skeleton', child: _SkeletonExample()),
          _Section(title: 'Toast', child: _ToastButtons()),
          _Section(
            title: 'List/detail reference layout (resize the window)',
            child: SizedBox(
              height: 320,
              child: ListDetailReference(),
            ),
          ),
          _Section(
            title: 'Form reference layout (resize the window)',
            child: SizedBox(height: 260, child: FormReference()),
          ),
          _Section(
            title: 'Staggered list entrance',
            child: _StaggeredExample(),
          ),
        ],
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: RevnaraSpacing.xl),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: RevnaraSpacing.sm),
          child,
        ],
      ),
    );
  }
}

class _RiskTierRow extends StatelessWidget {
  const _RiskTierRow();

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: RevnaraSpacing.sm,
      children: [
        for (var tier = 0; tier <= 6; tier++) RevnaraRiskTierBadge(tier: tier),
      ],
    );
  }
}

class _GovernanceBadgeRow extends StatelessWidget {
  const _GovernanceBadgeRow();

  @override
  Widget build(BuildContext context) {
    return const Wrap(
      spacing: RevnaraSpacing.sm,
      runSpacing: RevnaraSpacing.sm,
      children: [
        RevnaraEvidenceBadge(cited: true),
        RevnaraEvidenceBadge(cited: false),
        RevnaraApprovalBoundBadge(),
        RevnaraHumanNativeBadge(),
      ],
    );
  }
}

class _ButtonRow extends StatelessWidget {
  const _ButtonRow();

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: RevnaraSpacing.sm,
      children: [
        RevnaraButton(label: 'Primary', onPressed: () {}),
        RevnaraButton(
          label: 'Secondary',
          variant: RevnaraButtonVariant.secondary,
          onPressed: () {},
        ),
        RevnaraButton(
          label: 'Destructive',
          variant: RevnaraButtonVariant.destructive,
          onPressed: () {},
        ),
        const RevnaraButton(label: 'Disabled', onPressed: null),
      ],
    );
  }
}

class _InputColumn extends StatelessWidget {
  const _InputColumn();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        RevnaraTextField(label: 'Company name'),
        SizedBox(height: RevnaraSpacing.sm),
        RevnaraTextField(label: 'With error', errorText: 'This is required'),
      ],
    );
  }
}

class _CardExample extends StatelessWidget {
  const _CardExample();

  @override
  Widget build(BuildContext context) {
    return RevnaraCard(
      onTap: () {},
      child: const Text('Tappable card content'),
    );
  }
}

class _ListRowExample extends StatelessWidget {
  const _ListRowExample();

  @override
  Widget build(BuildContext context) {
    return RevnaraCard(
      padding: EdgeInsets.zero,
      child: RevnaraListRow(
        title: 'Acme Corp — Website redesign',
        subtitle: 'Qualified · \$18,000 estimated',
        trailing: const RevnaraRiskTierBadge(tier: 2),
        onTap: () {},
      ),
    );
  }
}

class _EmptyStateExample extends StatelessWidget {
  const _EmptyStateExample();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 200,
      child: RevnaraEmptyState(
        icon: Icons.inbox_outlined,
        title: 'No opportunities yet',
        message: 'Create one manually or import from a connected source.',
        action: RevnaraButton(label: 'Create opportunity', onPressed: () {}),
      ),
    );
  }
}

class _SkeletonExample extends StatelessWidget {
  const _SkeletonExample();

  @override
  Widget build(BuildContext context) {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        RevnaraLoadingSkeleton(height: 20),
        SizedBox(height: RevnaraSpacing.xs),
        RevnaraLoadingSkeleton(height: 16, width: 240),
      ],
    );
  }
}

class _ToastButtons extends StatelessWidget {
  const _ToastButtons();

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: RevnaraSpacing.sm,
      children: [
        RevnaraButton(
          label: 'Show info toast',
          variant: RevnaraButtonVariant.secondary,
          onPressed: () => RevnaraToast.show(context, 'This is an info toast'),
        ),
        RevnaraButton(
          label: 'Show success toast',
          variant: RevnaraButtonVariant.secondary,
          onPressed: () => RevnaraToast.show(
            context,
            'Approved and bound',
            variant: RevnaraToastVariant.success,
          ),
        ),
        RevnaraButton(
          label: 'Show error toast',
          variant: RevnaraButtonVariant.secondary,
          onPressed: () => RevnaraToast.show(
            context,
            'Something went wrong',
            variant: RevnaraToastVariant.error,
          ),
        ),
      ],
    );
  }
}

class _StaggeredExample extends StatelessWidget {
  const _StaggeredExample();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (var i = 0; i < 4; i++)
          RevnaraStaggeredEntrance(
            index: i,
            child: RevnaraCard(child: Text('Staggered item ${i + 1}')),
          ),
      ],
    );
  }
}
