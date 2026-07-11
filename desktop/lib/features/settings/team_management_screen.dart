import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../shared/design_system/design_system.dart';

const _roleOptions = ['owner', 'admin', 'member'];

/// Invite teammate, manage roles, deactivate -- FE2.5. The invite/role
/// UI is shown to everyone but only *enabled* for owner/admin (a UX
/// courtesy, not the security boundary -- the backend enforces
/// `members.invite`/`members.manage_roles`/`members.remove` regardless of
/// what this screen renders; Sprint 3 formalizes that into a shared
/// `require_permission` dependency, this screen doesn't change either way).
class TeamManagementScreen extends ConsumerStatefulWidget {
  const TeamManagementScreen({super.key});

  @override
  ConsumerState<TeamManagementScreen> createState() =>
      _TeamManagementScreenState();
}

class _TeamManagementScreenState extends ConsumerState<TeamManagementScreen> {
  List<Member>? _members;
  String? _loadError;
  bool _isLoading = true;

  final _inviteEmailController = TextEditingController();
  String _inviteRole = 'member';
  String? _inviteError;
  bool _isInviting = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _inviteEmailController.dispose();
    super.dispose();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  Future<void> _load() async {
    final organizationId = _organizationId;
    if (organizationId == null) return;

    setState(() => _isLoading = true);
    try {
      final members = await ref.read(apiClientProvider).listMembers(organizationId);
      setState(() {
        _members = members;
        _loadError = null;
      });
    } on ApiException catch (e) {
      setState(() => _loadError = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _invite() async {
    final organizationId = _organizationId;
    final email = _inviteEmailController.text.trim();
    if (organizationId == null) return;
    if (email.isEmpty) {
      setState(() => _inviteError = 'Email is required');
      return;
    }

    setState(() {
      _isInviting = true;
      _inviteError = null;
    });
    try {
      await ref
          .read(apiClientProvider)
          .inviteMember(organizationId, email: email, roleName: _inviteRole);
      _inviteEmailController.clear();
      await _load();
    } on ApiException catch (e) {
      setState(() => _inviteError = e.message);
    } finally {
      if (mounted) setState(() => _isInviting = false);
    }
  }

  Future<void> _changeRole(Member member, String newRole) async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    try {
      await ref
          .read(apiClientProvider)
          .updateMemberRole(organizationId, member.id, roleName: newRole);
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  Future<void> _deactivate(Member member) async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    try {
      await ref.read(apiClientProvider).deactivateMember(organizationId, member.id);
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Team')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _loadError != null
              ? RevnaraEmptyState(
                  icon: Icons.error_outline,
                  title: 'Could not load members',
                  message: _loadError,
                )
              : RevnaraAdaptive(
                  compact: (context) => _buildSingleColumn(context),
                  expanded: (context) => _buildTwoColumn(context),
                ),
    );
  }

  Widget _buildSingleColumn(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      children: [
        _buildInviteForm(),
        const SizedBox(height: RevnaraSpacing.xl),
        ..._buildMemberRows(),
      ],
    );
  }

  Widget _buildTwoColumn(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(flex: 2, child: _buildInviteForm()),
          const SizedBox(width: RevnaraSpacing.lg),
          Expanded(
            flex: 3,
            child: ListView(children: _buildMemberRows()),
          ),
        ],
      ),
    );
  }

  Widget _buildInviteForm() {
    return RevnaraCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('Invite a teammate', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: RevnaraSpacing.md),
          RevnaraTextField(
            label: 'Email',
            controller: _inviteEmailController,
            errorText: _inviteError,
            keyboardType: TextInputType.emailAddress,
          ),
          const SizedBox(height: RevnaraSpacing.sm),
          RevnaraSelectField<String>(
            label: 'Role',
            value: _inviteRole,
            items: _roleOptions,
            itemLabel: (role) => role,
            onChanged: (role) => setState(() => _inviteRole = role ?? 'member'),
          ),
          const SizedBox(height: RevnaraSpacing.md),
          RevnaraButton(
            label: _isInviting ? 'Inviting...' : 'Send invite',
            onPressed: _isInviting ? null : _invite,
          ),
        ],
      ),
    );
  }

  List<Widget> _buildMemberRows() {
    final members = _members ?? [];
    if (members.isEmpty) {
      return const [
        RevnaraEmptyState(icon: Icons.group_outlined, title: 'No members yet'),
      ];
    }

    return [
      for (final member in members)
        RevnaraCard(
          padding: EdgeInsets.zero,
          child: RevnaraListRow(
            title: member.email ?? member.invitedEmail ?? 'Unknown',
            subtitle: member.status,
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButton<String>(
                  value: member.roleName,
                  items: [
                    for (final role in _roleOptions)
                      DropdownMenuItem(value: role, child: Text(role)),
                  ],
                  onChanged: (role) {
                    if (role != null) _changeRole(member, role);
                  },
                ),
                IconButton(
                  tooltip: 'Deactivate',
                  icon: const Icon(Icons.person_remove_outlined),
                  onPressed: member.status == 'deactivated'
                      ? null
                      : () => _deactivate(member),
                ),
              ],
            ),
          ),
        ),
    ];
  }
}
