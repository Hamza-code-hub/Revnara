import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../auth/membership_provider.dart';
import '../../shared/design_system/design_system.dart';

/// Shown when a signed-in user has no active organization membership yet
/// -- exercises POST /organizations from the UI. Not a named Sprint 2 task
/// ID on its own, but a necessary consequence of one: without this screen
/// a freshly signed-in user with zero memberships would have nowhere to
/// go, since every other screen requires an active organization.
class CreateOrganizationScreen extends ConsumerStatefulWidget {
  const CreateOrganizationScreen({super.key});

  @override
  ConsumerState<CreateOrganizationScreen> createState() =>
      _CreateOrganizationScreenState();
}

class _CreateOrganizationScreenState
    extends ConsumerState<CreateOrganizationScreen> {
  final _nameController = TextEditingController();
  String? _error;
  bool _isSubmitting = false;

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      setState(() => _error = 'Organization name is required');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).createOrganization(name);
      ref.invalidate(meProvider); // re-fetch memberships -> router redirects
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 400),
          child: Padding(
            padding: const EdgeInsets.all(RevnaraSpacing.lg),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'Set up your organization',
                  style: Theme.of(context).textTheme.headlineSmall,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: RevnaraSpacing.sm),
                Text(
                  'This creates your workspace and makes you the owner.',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: RevnaraSpacing.xl),
                RevnaraTextField(
                  label: 'Organization name',
                  controller: _nameController,
                  errorText: _error,
                ),
                const SizedBox(height: RevnaraSpacing.lg),
                RevnaraButton(
                  label: _isSubmitting ? 'Creating...' : 'Create organization',
                  onPressed: _isSubmitting ? null : _submit,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
