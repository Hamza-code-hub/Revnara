import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../shared/design_system/design_system.dart';

/// FE6.1/FE6.3/FE6.4: the three opportunity intake paths in one screen --
/// manual entry, pasting an Upwork listing link, and importing a CSV batch.
/// All three funnel into the same backend service.create_opportunity path
/// (and the same deterministic safety screening), so they're presented as
/// tabs of one intake flow rather than separate screens.
class OpportunityIntakeScreen extends ConsumerStatefulWidget {
  const OpportunityIntakeScreen({super.key});

  @override
  ConsumerState<OpportunityIntakeScreen> createState() => _OpportunityIntakeScreenState();
}

class _OpportunityIntakeScreenState extends ConsumerState<OpportunityIntakeScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('New opportunity'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Manual'),
            Tab(text: 'Upwork link'),
            Tab(text: 'CSV import'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          _ManualIntakeForm(),
          _UpworkLinkIntakeForm(),
          _CsvImportForm(),
        ],
      ),
    );
  }
}

class _ManualIntakeForm extends ConsumerStatefulWidget {
  const _ManualIntakeForm();

  @override
  ConsumerState<_ManualIntakeForm> createState() => _ManualIntakeFormState();
}

class _ManualIntakeFormState extends ConsumerState<_ManualIntakeForm> {
  final _titleController = TextEditingController();
  final _clientNameController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _requirementsController = TextEditingController();
  final _budgetMinController = TextEditingController();
  final _budgetMaxController = TextEditingController();
  final _budgetCurrencyController = TextEditingController(text: 'USD');

  bool _isSaving = false;
  String? _error;

  @override
  void dispose() {
    _titleController.dispose();
    _clientNameController.dispose();
    _descriptionController.dispose();
    _requirementsController.dispose();
    _budgetMinController.dispose();
    _budgetMaxController.dispose();
    _budgetCurrencyController.dispose();
    super.dispose();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  Future<void> _submit() async {
    final organizationId = _organizationId;
    final title = _titleController.text.trim();
    if (organizationId == null || title.isEmpty) return;

    setState(() {
      _isSaving = true;
      _error = null;
    });
    try {
      final opportunity = await ref.read(apiClientProvider).createOpportunity(
            organizationId,
            title: title,
            description: _descriptionController.text.trim().isEmpty
                ? null
                : _descriptionController.text.trim(),
            requirements: _requirementsController.text.trim().isEmpty
                ? null
                : _requirementsController.text.trim(),
            budgetMin: double.tryParse(_budgetMinController.text.trim()),
            budgetMax: double.tryParse(_budgetMaxController.text.trim()),
            budgetCurrency: _budgetCurrencyController.text.trim().isEmpty
                ? null
                : _budgetCurrencyController.text.trim(),
            clientName: _clientNameController.text.trim().isEmpty
                ? null
                : _clientNameController.text.trim(),
          );
      if (mounted) {
        RevnaraToast.show(
          context,
          opportunity.safetyScreeningStatus == 'screened_flagged'
              ? 'Opportunity created -- flagged for review'
              : 'Opportunity created',
          variant: opportunity.safetyScreeningStatus == 'screened_flagged'
              ? RevnaraToastVariant.error
              : RevnaraToastVariant.success,
        );
        Navigator.of(context).pop();
      }
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      children: [
        RevnaraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              RevnaraTextField(label: 'Title', controller: _titleController),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraTextField(label: 'Client name', controller: _clientNameController),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraTextField(
                label: 'Description',
                controller: _descriptionController,
                maxLines: 3,
              ),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraTextField(
                label: 'Requirements',
                controller: _requirementsController,
                maxLines: 3,
              ),
              const SizedBox(height: RevnaraSpacing.sm),
              Row(
                children: [
                  Expanded(
                    child: RevnaraTextField(
                      label: 'Budget min',
                      controller: _budgetMinController,
                      keyboardType: TextInputType.number,
                    ),
                  ),
                  const SizedBox(width: RevnaraSpacing.sm),
                  Expanded(
                    child: RevnaraTextField(
                      label: 'Budget max',
                      controller: _budgetMaxController,
                      keyboardType: TextInputType.number,
                    ),
                  ),
                  const SizedBox(width: RevnaraSpacing.sm),
                  Expanded(
                    child: RevnaraTextField(
                      label: 'Currency',
                      controller: _budgetCurrencyController,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: RevnaraSpacing.md),
              RevnaraButton(
                label: _isSaving ? 'Creating...' : 'Create opportunity',
                onPressed: _isSaving ? null : _submit,
              ),
              if (_error != null) ...[
                const SizedBox(height: RevnaraSpacing.sm),
                Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _UpworkLinkIntakeForm extends ConsumerStatefulWidget {
  const _UpworkLinkIntakeForm();

  @override
  ConsumerState<_UpworkLinkIntakeForm> createState() => _UpworkLinkIntakeFormState();
}

class _UpworkLinkIntakeFormState extends ConsumerState<_UpworkLinkIntakeForm> {
  final _urlController = TextEditingController();
  final _titleController = TextEditingController();
  final _clientNameController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _budgetMinController = TextEditingController();
  final _budgetMaxController = TextEditingController();
  final _budgetCurrencyController = TextEditingController(text: 'USD');

  bool _isSaving = false;
  String? _error;

  @override
  void dispose() {
    _urlController.dispose();
    _titleController.dispose();
    _clientNameController.dispose();
    _descriptionController.dispose();
    _budgetMinController.dispose();
    _budgetMaxController.dispose();
    _budgetCurrencyController.dispose();
    super.dispose();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  Future<void> _submit() async {
    final organizationId = _organizationId;
    final url = _urlController.text.trim();
    final title = _titleController.text.trim();
    if (organizationId == null || url.isEmpty || title.isEmpty) return;

    setState(() {
      _isSaving = true;
      _error = null;
    });
    try {
      final opportunity = await ref.read(apiClientProvider).importOpportunityLink(
            organizationId,
            url: url,
            title: title,
            description: _descriptionController.text.trim().isEmpty
                ? null
                : _descriptionController.text.trim(),
            budgetMin: double.tryParse(_budgetMinController.text.trim()),
            budgetMax: double.tryParse(_budgetMaxController.text.trim()),
            budgetCurrency: _budgetCurrencyController.text.trim().isEmpty
                ? null
                : _budgetCurrencyController.text.trim(),
            clientName: _clientNameController.text.trim().isEmpty
                ? null
                : _clientNameController.text.trim(),
          );
      if (mounted) {
        RevnaraToast.show(
          context,
          opportunity.safetyScreeningStatus == 'screened_flagged'
              ? 'Opportunity imported -- flagged for review'
              : 'Opportunity imported',
          variant: opportunity.safetyScreeningStatus == 'screened_flagged'
              ? RevnaraToastVariant.error
              : RevnaraToastVariant.success,
        );
        Navigator.of(context).pop();
      }
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      children: [
        RevnaraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Paste a link to a job posting (e.g. Upwork). Revnara never '
                'visits the link or automates the platform on your behalf -- '
                'you stay in full control of every submission.',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraTextField(label: 'Listing URL', controller: _urlController),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraTextField(label: 'Title', controller: _titleController),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraTextField(label: 'Client name', controller: _clientNameController),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraTextField(
                label: 'Description',
                controller: _descriptionController,
                maxLines: 3,
              ),
              const SizedBox(height: RevnaraSpacing.sm),
              Row(
                children: [
                  Expanded(
                    child: RevnaraTextField(
                      label: 'Budget min',
                      controller: _budgetMinController,
                      keyboardType: TextInputType.number,
                    ),
                  ),
                  const SizedBox(width: RevnaraSpacing.sm),
                  Expanded(
                    child: RevnaraTextField(
                      label: 'Budget max',
                      controller: _budgetMaxController,
                      keyboardType: TextInputType.number,
                    ),
                  ),
                  const SizedBox(width: RevnaraSpacing.sm),
                  Expanded(
                    child: RevnaraTextField(
                      label: 'Currency',
                      controller: _budgetCurrencyController,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: RevnaraSpacing.md),
              RevnaraButton(
                label: _isSaving ? 'Importing...' : 'Import link',
                onPressed: _isSaving ? null : _submit,
              ),
              if (_error != null) ...[
                const SizedBox(height: RevnaraSpacing.sm),
                Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _CsvImportForm extends ConsumerStatefulWidget {
  const _CsvImportForm();

  @override
  ConsumerState<_CsvImportForm> createState() => _CsvImportFormState();
}

class _CsvImportFormState extends ConsumerState<_CsvImportForm> {
  final _csvController = TextEditingController(
    text: 'title,description,requirements,budget_min,budget_max,budget_currency,client_name\n',
  );

  bool _isImporting = false;
  String? _error;
  CsvImportResult? _result;

  @override
  void dispose() {
    _csvController.dispose();
    super.dispose();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  Future<void> _submit() async {
    final organizationId = _organizationId;
    final csvContent = _csvController.text;
    if (organizationId == null || csvContent.trim().isEmpty) return;

    setState(() {
      _isImporting = true;
      _error = null;
      _result = null;
    });
    try {
      final result = await ref
          .read(apiClientProvider)
          .importOpportunitiesCsv(organizationId, csvContent: csvContent);
      setState(() => _result = result);
      if (mounted) {
        RevnaraToast.show(
          context,
          '${result.created.length} imported, ${result.errors.length} row error(s)',
          variant: result.errors.isEmpty
              ? RevnaraToastVariant.success
              : RevnaraToastVariant.error,
        );
      }
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isImporting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      children: [
        RevnaraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Paste CSV content below. Required column: title. Optional: '
                'description, requirements, budget_min, budget_max, '
                'budget_currency, client_name. Malformed rows are reported '
                'individually -- valid rows still import.',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraTextField(
                label: 'CSV content',
                controller: _csvController,
                maxLines: 8,
              ),
              const SizedBox(height: RevnaraSpacing.md),
              RevnaraButton(
                label: _isImporting ? 'Importing...' : 'Import CSV',
                icon: Icons.upload_file_outlined,
                onPressed: _isImporting ? null : _submit,
              ),
              if (_error != null) ...[
                const SizedBox(height: RevnaraSpacing.sm),
                Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              ],
            ],
          ),
        ),
        if (_result != null) ...[
          const SizedBox(height: RevnaraSpacing.md),
          if (_result!.created.isNotEmpty)
            RevnaraCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Created (${_result!.created.length})',
                      style: Theme.of(context).textTheme.titleSmall),
                  for (final opportunity in _result!.created)
                    Text('• ${opportunity.title} (${opportunity.status})'),
                ],
              ),
            ),
          if (_result!.errors.isNotEmpty) ...[
            const SizedBox(height: RevnaraSpacing.sm),
            RevnaraCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Row errors (${_result!.errors.length})',
                      style: Theme.of(context).textTheme.titleSmall),
                  for (final rowError in _result!.errors)
                    Text('• Row ${rowError.rowNumber}: ${rowError.error}'),
                ],
              ),
            ),
          ],
        ],
      ],
    );
  }
}
