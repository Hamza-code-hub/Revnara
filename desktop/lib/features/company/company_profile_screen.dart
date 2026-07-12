import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../shared/design_system/design_system.dart';

/// FE4.1: edit the tenant's company profile -- fields live directly on
/// Organization (see backend/app/organizations/models.py's Sprint 4
/// comment for why there's no separate company_profiles table).
class CompanyProfileScreen extends ConsumerStatefulWidget {
  const CompanyProfileScreen({super.key});

  @override
  ConsumerState<CompanyProfileScreen> createState() =>
      _CompanyProfileScreenState();
}

class _CompanyProfileScreenState extends ConsumerState<CompanyProfileScreen> {
  final _descriptionController = TextEditingController();
  final _industryController = TextEditingController();
  final _websiteController = TextEditingController();
  final _foundedYearController = TextEditingController();

  bool _isLoading = true;
  bool _isSaving = false;
  String? _loadError;
  String? _saveError;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    _industryController.dispose();
    _websiteController.dispose();
    _foundedYearController.dispose();
    super.dispose();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  Future<void> _load() async {
    final organizationId = _organizationId;
    if (organizationId == null) return;

    setState(() => _isLoading = true);
    try {
      final organization =
          await ref.read(apiClientProvider).getOrganizationProfile(organizationId);
      _descriptionController.text = organization.description ?? '';
      _industryController.text = organization.industry ?? '';
      _websiteController.text = organization.website ?? '';
      _foundedYearController.text = organization.foundedYear?.toString() ?? '';
      setState(() => _loadError = null);
    } on ApiException catch (e) {
      setState(() => _loadError = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _save() async {
    final organizationId = _organizationId;
    if (organizationId == null) return;

    setState(() {
      _isSaving = true;
      _saveError = null;
    });
    try {
      await ref.read(apiClientProvider).updateOrganizationProfile(
            organizationId,
            description: _descriptionController.text.trim(),
            industry: _industryController.text.trim(),
            website: _websiteController.text.trim(),
            foundedYear: int.tryParse(_foundedYearController.text.trim()),
          );
      if (mounted) {
        RevnaraToast.show(
          context,
          'Company profile saved',
          variant: RevnaraToastVariant.success,
        );
      }
    } on ApiException catch (e) {
      setState(() => _saveError = e.message);
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Company profile')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _loadError != null
              ? RevnaraEmptyState(
                  icon: Icons.error_outline,
                  title: 'Could not load company profile',
                  message: _loadError,
                )
              : Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 480),
                    child: ListView(
                      padding: const EdgeInsets.all(RevnaraSpacing.lg),
                      children: [
                        RevnaraCard(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              RevnaraTextField(
                                label: 'Description',
                                controller: _descriptionController,
                              ),
                              const SizedBox(height: RevnaraSpacing.sm),
                              RevnaraTextField(
                                label: 'Industry',
                                controller: _industryController,
                              ),
                              const SizedBox(height: RevnaraSpacing.sm),
                              RevnaraTextField(
                                label: 'Website',
                                controller: _websiteController,
                              ),
                              const SizedBox(height: RevnaraSpacing.sm),
                              RevnaraTextField(
                                label: 'Founded year',
                                controller: _foundedYearController,
                                keyboardType: TextInputType.number,
                                errorText: _saveError,
                              ),
                              const SizedBox(height: RevnaraSpacing.md),
                              RevnaraButton(
                                label: _isSaving ? 'Saving...' : 'Save',
                                onPressed: _isSaving ? null : _save,
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
    );
  }
}
