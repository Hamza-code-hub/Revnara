import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../shared/design_system/design_system.dart';

/// FE4.3: private file uploads for the company brain.
///
/// Drives the real backend flow (POST .../files/signed-upload then POST
/// .../files/{id}/confirm) end to end -- verified for real against a live
/// Supabase project (Sprint 4 follow-up), including an actual PUT of file
/// bytes to the signed URL. This widget itself still takes a filename
/// directly rather than opening a native file picker (`file_picker`
/// package integration is separate follow-up work), so it confirms
/// immediately after requesting the signed URL instead of performing a
/// real PUT from Flutter -- the backend-controlled half of the flow
/// (tenant-scoped path construction, file metadata, RLS) is exercised
/// either way.
class CompanyFileUploadWidget extends ConsumerStatefulWidget {
  const CompanyFileUploadWidget({super.key});

  @override
  ConsumerState<CompanyFileUploadWidget> createState() =>
      _CompanyFileUploadWidgetState();
}

class _CompanyFileUploadWidgetState
    extends ConsumerState<CompanyFileUploadWidget> {
  List<CompanyFile>? _files;
  String? _error;
  bool _isLoading = true;
  bool _isUploading = false;
  final _filenameController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _filenameController.dispose();
    super.dispose();
  }

  String? get _organizationId => ref.read(activeOrganizationIdProvider);

  Future<void> _load() async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    setState(() => _isLoading = true);
    try {
      final files = await ref.read(apiClientProvider).listFiles(organizationId);
      setState(() {
        _files = files;
        _error = null;
      });
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _delete(CompanyFile file) async {
    final organizationId = _organizationId;
    if (organizationId == null) return;
    try {
      await ref.read(apiClientProvider).deleteFile(organizationId, file.id);
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    }
  }

  Future<void> _upload() async {
    final organizationId = _organizationId;
    final filename = _filenameController.text.trim();
    if (organizationId == null || filename.isEmpty) return;

    setState(() => _isUploading = true);
    try {
      final apiClient = ref.read(apiClientProvider);
      final signedUpload =
          await apiClient.createSignedUpload(organizationId, filename: filename);
      // No real Supabase Storage bytes to PUT in this environment -- see
      // this widget's class docstring. Confirming here still proves the
      // full metadata/tenant-scoping half of the flow end to end.
      await apiClient.confirmUpload(organizationId, signedUpload.fileId);
      _filenameController.clear();
      await _load();
    } on ApiException catch (e) {
      if (mounted) RevnaraToast.show(context, e.message, variant: RevnaraToastVariant.error);
    } finally {
      if (mounted) setState(() => _isUploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return RevnaraEmptyState(
          icon: Icons.error_outline, title: 'Could not load files', message: _error);
    }

    final files = _files ?? [];
    return ListView(
      padding: const EdgeInsets.all(RevnaraSpacing.md),
      children: [
        RevnaraCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              RevnaraTextField(label: 'File name', controller: _filenameController),
              const SizedBox(height: RevnaraSpacing.sm),
              RevnaraButton(
                label: _isUploading ? 'Uploading...' : 'Upload',
                icon: Icons.upload_file_outlined,
                onPressed: _isUploading ? null : _upload,
              ),
            ],
          ),
        ),
        const SizedBox(height: RevnaraSpacing.md),
        if (files.isEmpty)
          const RevnaraEmptyState(icon: Icons.folder_outlined, title: 'No files yet'),
        for (final file in files)
          RevnaraCard(
            padding: EdgeInsets.zero,
            child: RevnaraListRow(
              title: file.originalFilename,
              subtitle: file.status,
              leading: const Icon(Icons.insert_drive_file_outlined),
              trailing: IconButton(
                tooltip: 'Delete',
                icon: const Icon(Icons.delete_outline),
                onPressed: () => _delete(file),
              ),
            ),
          ),
      ],
    );
  }
}
