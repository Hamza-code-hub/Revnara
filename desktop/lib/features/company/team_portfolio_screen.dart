import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../shared/design_system/design_system.dart';
import 'file_upload_widget.dart';
import 'knowledge_search_widget.dart';

const _classificationOptions = ['public', 'confidential'];

/// Shared edit-dialog helper: a small form with one text field per entry
/// in [initialValues] (keyed by field label), returning the edited values
/// on Save or null on Cancel. Used by every tab below's list-row `onTap`
/// so update (not just create/delete) is reachable from the app, per
/// Sprint 4's Definition of Done ("fully CRUD-able from the app").
Future<Map<String, String>?> _showEditDialog(
  BuildContext context, {
  required String dialogTitle,
  required Map<String, String> initialValues,
}) async {
  final controllers = {
    for (final entry in initialValues.entries)
      entry.key: TextEditingController(text: entry.value),
  };
  final result = await showDialog<Map<String, String>>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(dialogTitle),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          for (final label in controllers.keys)
            Padding(
              padding: const EdgeInsets.only(bottom: RevnaraSpacing.sm),
              child: RevnaraTextField(label: label, controller: controllers[label]),
            ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(
            context,
            {for (final entry in controllers.entries) entry.key: entry.value.text.trim()},
          ),
          child: const Text('Save'),
        ),
      ],
    ),
  );
  for (final controller in controllers.values) {
    controller.dispose();
  }
  return result;
}

/// Same idea as [_showEditDialog] but for the two entities whose editable
/// fields are a title plus a classification dropdown (portfolio items,
/// case studies) rather than two plain text fields.
Future<(String, String)?> _showTitleClassificationEditDialog(
  BuildContext context, {
  required String dialogTitle,
  required String initialTitle,
  required String initialClassification,
}) async {
  final titleController = TextEditingController(text: initialTitle);
  var classification = initialClassification;

  final result = await showDialog<(String, String)>(
    context: context,
    builder: (context) => StatefulBuilder(
      builder: (context, setDialogState) => AlertDialog(
        title: Text(dialogTitle),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            RevnaraTextField(label: 'Title', controller: titleController),
            const SizedBox(height: RevnaraSpacing.sm),
            RevnaraSelectField<String>(
              label: 'Classification',
              value: classification,
              items: _classificationOptions,
              itemLabel: (c) => c,
              onChanged: (c) => setDialogState(() => classification = c ?? classification),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () =>
                Navigator.pop(context, (titleController.text.trim(), classification)),
            child: const Text('Save'),
          ),
        ],
      ),
    ),
  );
  titleController.dispose();
  return result;
}

/// FE4.2: team/skills inventory + portfolio/case-study library --
/// BE4.1/BE4.2's four new entities, one tab each, plus a Files tab for
/// BE4.3/BE4.4's upload flow (see file_upload_widget.dart), plus a
/// debug-only search preview tab (FE5.1, see knowledge_search_widget.dart)
/// that never appears in release builds.
class TeamPortfolioScreen extends StatelessWidget {
  const TeamPortfolioScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final tabs = <Tab>[
      const Tab(text: 'Team'),
      const Tab(text: 'Skills'),
      const Tab(text: 'Portfolio'),
      const Tab(text: 'Case studies'),
      const Tab(text: 'Files'),
      if (kDebugMode) const Tab(text: 'Search (debug)'),
    ];
    final views = <Widget>[
      const _TeamTab(),
      const _SkillsTab(),
      const _PortfolioTab(),
      const _CaseStudiesTab(),
      const CompanyFileUploadWidget(),
      if (kDebugMode) const KnowledgeSearchWidget(),
    ];

    return DefaultTabController(
      length: tabs.length,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Team & portfolio'),
          bottom: TabBar(isScrollable: true, tabs: tabs),
        ),
        body: TabBarView(children: views),
      ),
    );
  }
}

class _SkillsTab extends ConsumerStatefulWidget {
  const _SkillsTab();

  @override
  ConsumerState<_SkillsTab> createState() => _SkillsTabState();
}

class _SkillsTabState extends ConsumerState<_SkillsTab> {
  List<Skill>? _skills;
  String? _error;
  bool _isLoading = true;
  final _nameController = TextEditingController();
  final _categoryController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _categoryController.dispose();
    super.dispose();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  Future<void> _load() async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    setState(() => _isLoading = true);
    try {
      final skills = await ref.read(apiClientProvider).listSkills(organizationId);
      setState(() {
        _skills = skills;
        _error = null;
      });
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _create() async {
    final organizationId = _organizationId;
    final name = _nameController.text.trim();
    if (organizationId == null || name.isEmpty) return;
    try {
      await ref.read(apiClientProvider).createSkill(
            organizationId,
            name: name,
            category: _categoryController.text.trim().isEmpty
                ? null
                : _categoryController.text.trim(),
          );
      _nameController.clear();
      _categoryController.clear();
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  Future<void> _delete(Skill skill) async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    try {
      await ref.read(apiClientProvider).deleteSkill(organizationId, skill.id);
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  Future<void> _edit(Skill skill) async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    final values = await _showEditDialog(
      context,
      dialogTitle: 'Edit skill',
      initialValues: {'Name': skill.name, 'Category': skill.category ?? ''},
    );
    if (values == null) return;
    try {
      await ref.read(apiClientProvider).updateSkill(
            organizationId,
            skill.id,
            name: values['Name'],
            category: values['Category'],
          );
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return RevnaraEmptyState(icon: Icons.error_outline, title: 'Could not load skills', message: _error);
    }

    final skills = _skills ?? [];
    return ListView(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      children: [
        RevnaraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              RevnaraTextField(label: 'Skill name', controller: _nameController),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraTextField(label: 'Category (optional)', controller: _categoryController),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraButton(label: 'Add skill', onPressed: _create),
            ],
          ),
        ),
        const SizedBox(height: RevnaraSpacing.md),
        if (skills.isEmpty)
          const RevnaraEmptyState(icon: Icons.star_outline, title: 'No skills yet'),
        for (final skill in skills)
          RevnaraCard(
            padding: EdgeInsets.zero,
            child: RevnaraListRow(
              title: skill.name,
              subtitle: skill.category,
              onTap: () => _edit(skill),
              trailing: IconButton(
                tooltip: 'Delete',
                icon: const Icon(Icons.delete_outline),
                onPressed: () => _delete(skill),
              ),
            ),
          ),
      ],
    );
  }
}

class _TeamTab extends ConsumerStatefulWidget {
  const _TeamTab();

  @override
  ConsumerState<_TeamTab> createState() => _TeamTabState();
}

class _TeamTabState extends ConsumerState<_TeamTab> {
  List<TeamMember>? _members;
  String? _error;
  bool _isLoading = true;
  final _nameController = TextEditingController();
  final _titleController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _titleController.dispose();
    super.dispose();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  Future<void> _load() async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    setState(() => _isLoading = true);
    try {
      final members = await ref.read(apiClientProvider).listTeamMembers(organizationId);
      setState(() {
        _members = members;
        _error = null;
      });
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _create() async {
    final organizationId = _organizationId;
    final name = _nameController.text.trim();
    if (organizationId == null || name.isEmpty) return;
    try {
      await ref.read(apiClientProvider).createTeamMember(
            organizationId,
            name: name,
            title: _titleController.text.trim().isEmpty ? null : _titleController.text.trim(),
          );
      _nameController.clear();
      _titleController.clear();
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  Future<void> _delete(TeamMember member) async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    try {
      await ref.read(apiClientProvider).deleteTeamMember(organizationId, member.id);
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  Future<void> _edit(TeamMember member) async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    final values = await _showEditDialog(
      context,
      dialogTitle: 'Edit team member',
      initialValues: {'Name': member.name, 'Title': member.title ?? ''},
    );
    if (values == null) return;
    try {
      await ref.read(apiClientProvider).updateTeamMember(
            organizationId,
            member.id,
            name: values['Name'],
            title: values['Title'],
          );
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return RevnaraEmptyState(
          icon: Icons.error_outline, title: 'Could not load team members', message: _error);
    }

    final members = _members ?? [];
    return ListView(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      children: [
        RevnaraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              RevnaraTextField(label: 'Name', controller: _nameController),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraTextField(label: 'Title (optional)', controller: _titleController),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraButton(label: 'Add team member', onPressed: _create),
            ],
          ),
        ),
        const SizedBox(height: RevnaraSpacing.md),
        if (members.isEmpty)
          const RevnaraEmptyState(icon: Icons.people_outline, title: 'No team members yet'),
        for (final member in members)
          RevnaraCard(
            padding: EdgeInsets.zero,
            child: RevnaraListRow(
              title: member.name,
              subtitle: [
                if (member.title != null) member.title!,
                if (member.skills.isNotEmpty) member.skills.map((s) => s.name).join(', '),
              ].join(' • '),
              onTap: () => _edit(member),
              trailing: IconButton(
                tooltip: 'Remove',
                icon: const Icon(Icons.delete_outline),
                onPressed: () => _delete(member),
              ),
            ),
          ),
      ],
    );
  }
}

class _PortfolioTab extends ConsumerStatefulWidget {
  const _PortfolioTab();

  @override
  ConsumerState<_PortfolioTab> createState() => _PortfolioTabState();
}

class _PortfolioTabState extends ConsumerState<_PortfolioTab> {
  List<PortfolioItem>? _items;
  String? _error;
  bool _isLoading = true;
  final _titleController = TextEditingController();
  String _classification = 'public';

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  Future<void> _load() async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    setState(() => _isLoading = true);
    try {
      final items = await ref.read(apiClientProvider).listPortfolioItems(organizationId);
      setState(() {
        _items = items;
        _error = null;
      });
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _create() async {
    final organizationId = _organizationId;
    final title = _titleController.text.trim();
    if (organizationId == null || title.isEmpty) return;
    try {
      await ref.read(apiClientProvider).createPortfolioItem(
            organizationId,
            title: title,
            classification: _classification,
          );
      _titleController.clear();
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  Future<void> _delete(PortfolioItem item) async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    try {
      await ref.read(apiClientProvider).deletePortfolioItem(organizationId, item.id);
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  Future<void> _edit(PortfolioItem item) async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    final result = await _showTitleClassificationEditDialog(
      context,
      dialogTitle: 'Edit portfolio item',
      initialTitle: item.title,
      initialClassification: item.classification ?? 'public',
    );
    if (result == null) return;
    final (title, classification) = result;
    try {
      await ref.read(apiClientProvider).updatePortfolioItem(
            organizationId,
            item.id,
            title: title,
            classification: classification,
          );
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return RevnaraEmptyState(
          icon: Icons.error_outline, title: 'Could not load portfolio items', message: _error);
    }

    final items = _items ?? [];
    return ListView(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      children: [
        RevnaraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              RevnaraTextField(label: 'Title', controller: _titleController),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraSelectField<String>(
                label: 'Classification',
                value: _classification,
                items: _classificationOptions,
                itemLabel: (c) => c,
                onChanged: (c) => setState(() => _classification = c ?? 'public'),
              ),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraButton(label: 'Add portfolio item', onPressed: _create),
            ],
          ),
        ),
        const SizedBox(height: RevnaraSpacing.md),
        if (items.isEmpty)
          const RevnaraEmptyState(icon: Icons.work_outline, title: 'No portfolio items yet'),
        for (final item in items)
          RevnaraCard(
            padding: EdgeInsets.zero,
            child: RevnaraListRow(
              title: item.title,
              subtitle: item.classification,
              onTap: () => _edit(item),
              trailing: IconButton(
                tooltip: 'Delete',
                icon: const Icon(Icons.delete_outline),
                onPressed: () => _delete(item),
              ),
            ),
          ),
      ],
    );
  }
}

class _CaseStudiesTab extends ConsumerStatefulWidget {
  const _CaseStudiesTab();

  @override
  ConsumerState<_CaseStudiesTab> createState() => _CaseStudiesTabState();
}

class _CaseStudiesTabState extends ConsumerState<_CaseStudiesTab> {
  List<CaseStudy>? _caseStudies;
  String? _error;
  bool _isLoading = true;
  final _titleController = TextEditingController();
  String _classification = 'public';

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  Future<void> _load() async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    setState(() => _isLoading = true);
    try {
      final caseStudies = await ref.read(apiClientProvider).listCaseStudies(organizationId);
      setState(() {
        _caseStudies = caseStudies;
        _error = null;
      });
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _create() async {
    final organizationId = _organizationId;
    final title = _titleController.text.trim();
    if (organizationId == null || title.isEmpty) return;
    try {
      await ref.read(apiClientProvider).createCaseStudy(
            organizationId,
            title: title,
            classification: _classification,
          );
      _titleController.clear();
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  Future<void> _delete(CaseStudy caseStudy) async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    try {
      await ref.read(apiClientProvider).deleteCaseStudy(organizationId, caseStudy.id);
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  Future<void> _edit(CaseStudy caseStudy) async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    final result = await _showTitleClassificationEditDialog(
      context,
      dialogTitle: 'Edit case study',
      initialTitle: caseStudy.title,
      initialClassification: caseStudy.classification ?? 'public',
    );
    if (result == null) return;
    final (title, classification) = result;
    try {
      await ref.read(apiClientProvider).updateCaseStudy(
            organizationId,
            caseStudy.id,
            title: title,
            classification: classification,
          );
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return RevnaraEmptyState(
          icon: Icons.error_outline, title: 'Could not load case studies', message: _error);
    }

    final caseStudies = _caseStudies ?? [];
    return ListView(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      children: [
        RevnaraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              RevnaraTextField(label: 'Title', controller: _titleController),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraSelectField<String>(
                label: 'Classification',
                value: _classification,
                items: _classificationOptions,
                itemLabel: (c) => c,
                onChanged: (c) => setState(() => _classification = c ?? 'public'),
              ),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraButton(label: 'Add case study', onPressed: _create),
            ],
          ),
        ),
        const SizedBox(height: RevnaraSpacing.md),
        if (caseStudies.isEmpty)
          const RevnaraEmptyState(icon: Icons.article_outlined, title: 'No case studies yet'),
        for (final caseStudy in caseStudies)
          RevnaraCard(
            padding: EdgeInsets.zero,
            child: RevnaraListRow(
              title: caseStudy.title,
              subtitle: caseStudy.classification,
              onTap: () => _edit(caseStudy),
              trailing: IconButton(
                tooltip: 'Delete',
                icon: const Icon(Icons.delete_outline),
                onPressed: () => _delete(caseStudy),
              ),
            ),
          ),
      ],
    );
  }
}
