import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/session.dart';
import 'models.dart';

/// Base URL is supplied at build/run time, e.g.
/// `flutter run --dart-define=API_BASE_URL=http://localhost:8000`.
/// Defaults to the local backend dev server so `flutter run` works out of the box.
const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000',
);

class ApiException implements Exception {
  ApiException(this.statusCode, this.message);
  final int? statusCode;
  final String message;

  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({
    Dio? dio,
    String? accessToken,
    String? organizationId,
    this.onForbidden,
  }) : _dio = dio ??
            Dio(BaseOptions(
              baseUrl: apiBaseUrl,
              headers: {
                if (accessToken != null) 'Authorization': 'Bearer $accessToken',
                'X-Organization-Id': ?organizationId,
              },
            ));

  final Dio _dio;

  /// FE3.1 global 403 handling: called with the server's error message
  /// whenever any request gets a 403, in addition to the request's own
  /// call site still receiving an [ApiException] it can show inline
  /// context for. This is what lets a single top-level listener
  /// (app/global_error_listener.dart) show a consistent "not authorized"
  /// toast without every screen needing to remember to handle 403
  /// specially itself.
  void Function(String message)? onForbidden;

  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get('/health');
      return response.statusCode == 200;
    } on DioException {
      return false;
    }
  }

  Future<OrganizationCreateResult> createOrganization(String name) async {
    final response = await _guarded(() => _dio.post('/organizations', data: {'name': name}));
    return OrganizationCreateResult.fromJson(response.data as Map<String, dynamic>);
  }

  Future<MeResponse> getMe() async {
    final response = await _guarded(() => _dio.get('/me'));
    return MeResponse.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<Workspace>> listWorkspaces() async {
    final response = await _guarded(() => _dio.get('/workspaces'));
    return (response.data as List)
        .map((e) => Workspace.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Member>> listMembers(String organizationId) async {
    final response =
        await _guarded(() => _dio.get('/organizations/$organizationId/members'));
    return (response.data as List)
        .map((e) => Member.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Member> inviteMember(
    String organizationId, {
    required String email,
    required String roleName,
  }) async {
    final response = await _guarded(() => _dio.post(
          '/organizations/$organizationId/invitations',
          data: {'email': email, 'role_name': roleName},
        ));
    return Member.fromJson(response.data as Map<String, dynamic>);
  }

  Future<Member> updateMemberRole(
    String organizationId,
    String memberId, {
    required String roleName,
  }) async {
    final response = await _guarded(() => _dio.patch(
          '/organizations/$organizationId/members/$memberId',
          data: {'role_name': roleName},
        ));
    return Member.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deactivateMember(String organizationId, String memberId) async {
    await _guarded(() => _dio.delete('/organizations/$organizationId/members/$memberId'));
  }

  // --- Sprint 4: Company Brain -------------------------------------------

  Future<Organization> getOrganizationProfile(String organizationId) async {
    final response = await _guarded(() => _dio.get('/organizations/$organizationId'));
    return Organization.fromJson(response.data as Map<String, dynamic>);
  }

  Future<Organization> updateOrganizationProfile(
    String organizationId, {
    String? description,
    String? industry,
    String? website,
    int? foundedYear,
  }) async {
    final response = await _guarded(() => _dio.patch(
          '/organizations/$organizationId',
          data: {
            'description': ?description,
            'industry': ?industry,
            'website': ?website,
            'founded_year': ?foundedYear,
          },
        ));
    return Organization.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<Skill>> listSkills(String organizationId) async {
    final response = await _guarded(() => _dio.get('/organizations/$organizationId/skills'));
    return (response.data as List)
        .map((e) => Skill.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Skill> createSkill(String organizationId, {required String name, String? category}) async {
    final response = await _guarded(() => _dio.post(
          '/organizations/$organizationId/skills',
          data: {'name': name, 'category': ?category},
        ));
    return Skill.fromJson(response.data as Map<String, dynamic>);
  }

  Future<Skill> updateSkill(
    String organizationId,
    String skillId, {
    String? name,
    String? category,
  }) async {
    final response = await _guarded(() => _dio.patch(
          '/organizations/$organizationId/skills/$skillId',
          data: {'name': ?name, 'category': ?category},
        ));
    return Skill.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteSkill(String organizationId, String skillId) async {
    await _guarded(() => _dio.delete('/organizations/$organizationId/skills/$skillId'));
  }

  Future<List<TeamMember>> listTeamMembers(String organizationId) async {
    final response =
        await _guarded(() => _dio.get('/organizations/$organizationId/team-members'));
    return (response.data as List)
        .map((e) => TeamMember.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<TeamMember> createTeamMember(
    String organizationId, {
    required String name,
    String? title,
    List<String> skillIds = const [],
  }) async {
    final response = await _guarded(() => _dio.post(
          '/organizations/$organizationId/team-members',
          data: {
            'name': name,
            'title': ?title,
            'skill_ids': skillIds,
          },
        ));
    return TeamMember.fromJson(response.data as Map<String, dynamic>);
  }

  Future<TeamMember> updateTeamMember(
    String organizationId,
    String teamMemberId, {
    String? name,
    String? title,
  }) async {
    final response = await _guarded(() => _dio.patch(
          '/organizations/$organizationId/team-members/$teamMemberId',
          data: {'name': ?name, 'title': ?title},
        ));
    return TeamMember.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteTeamMember(String organizationId, String teamMemberId) async {
    await _guarded(
        () => _dio.delete('/organizations/$organizationId/team-members/$teamMemberId'));
  }

  Future<List<PortfolioItem>> listPortfolioItems(String organizationId) async {
    final response =
        await _guarded(() => _dio.get('/organizations/$organizationId/portfolio-items'));
    return (response.data as List)
        .map((e) => PortfolioItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<PortfolioItem> createPortfolioItem(
    String organizationId, {
    required String title,
    String? classification,
  }) async {
    final response = await _guarded(() => _dio.post(
          '/organizations/$organizationId/portfolio-items',
          data: {'title': title, 'classification': ?classification},
        ));
    return PortfolioItem.fromJson(response.data as Map<String, dynamic>);
  }

  Future<PortfolioItem> updatePortfolioItem(
    String organizationId,
    String portfolioItemId, {
    String? title,
    String? classification,
  }) async {
    final response = await _guarded(() => _dio.patch(
          '/organizations/$organizationId/portfolio-items/$portfolioItemId',
          data: {'title': ?title, 'classification': ?classification},
        ));
    return PortfolioItem.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deletePortfolioItem(String organizationId, String portfolioItemId) async {
    await _guarded(
        () => _dio.delete('/organizations/$organizationId/portfolio-items/$portfolioItemId'));
  }

  Future<List<CaseStudy>> listCaseStudies(String organizationId) async {
    final response =
        await _guarded(() => _dio.get('/organizations/$organizationId/case-studies'));
    return (response.data as List)
        .map((e) => CaseStudy.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CaseStudy> createCaseStudy(
    String organizationId, {
    required String title,
    String? portfolioItemId,
    String? classification,
  }) async {
    final response = await _guarded(() => _dio.post(
          '/organizations/$organizationId/case-studies',
          data: {
            'title': title,
            'portfolio_item_id': ?portfolioItemId,
            'classification': ?classification,
          },
        ));
    return CaseStudy.fromJson(response.data as Map<String, dynamic>);
  }

  Future<CaseStudy> updateCaseStudy(
    String organizationId,
    String caseStudyId, {
    String? title,
    String? classification,
  }) async {
    final response = await _guarded(() => _dio.patch(
          '/organizations/$organizationId/case-studies/$caseStudyId',
          data: {'title': ?title, 'classification': ?classification},
        ));
    return CaseStudy.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteCaseStudy(String organizationId, String caseStudyId) async {
    await _guarded(
        () => _dio.delete('/organizations/$organizationId/case-studies/$caseStudyId'));
  }

  Future<List<CompanyFile>> listFiles(String organizationId) async {
    final response = await _guarded(() => _dio.get('/organizations/$organizationId/files'));
    return (response.data as List)
        .map((e) => CompanyFile.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<SignedUpload> createSignedUpload(
    String organizationId, {
    required String filename,
    String? contentType,
  }) async {
    final response = await _guarded(() => _dio.post(
          '/organizations/$organizationId/files/signed-upload',
          data: {'filename': filename, 'content_type': ?contentType},
        ));
    return SignedUpload.fromJson(response.data as Map<String, dynamic>);
  }

  Future<CompanyFile> confirmUpload(
    String organizationId,
    String fileId, {
    int? sizeBytes,
  }) async {
    final response = await _guarded(() => _dio.post(
          '/organizations/$organizationId/files/$fileId/confirm',
          data: {'size_bytes': ?sizeBytes},
        ));
    return CompanyFile.fromJson(response.data as Map<String, dynamic>);
  }

  Future<Response> _guarded(Future<Response> Function() request) async {
    try {
      return await request();
    } on DioException catch (e) {
      final detail = e.response?.data is Map
          ? (e.response?.data as Map)['detail']
          : e.message;
      final message = detail?.toString() ?? 'Request failed';

      if (e.response?.statusCode == 403) {
        onForbidden?.call(message);
      }

      throw ApiException(e.response?.statusCode, message);
    }
  }
}

final apiClientProvider = Provider<ApiClient>((ref) {
  final session = ref.watch(currentSessionProvider);
  final organizationId = ref.watch(activeOrganizationIdProvider);
  return ApiClient(
    accessToken: session?.accessToken,
    organizationId: organizationId,
    onForbidden: (message) =>
        ref.read(unauthorizedEventProvider.notifier).state = message,
  );
});

/// FE3.1: set (with a fresh message) every time any request anywhere
/// gets a 403. app/global_error_listener.dart shows a toast whenever
/// this changes -- a screen-crash-proof, consistent "not authorized"
/// state instead of each screen needing its own 403 handling.
final unauthorizedEventProvider = StateProvider<String?>((ref) => null);

/// The organization the app is currently operating in -- explicit state,
/// never inferred, mirroring the backend's X-Organization-Id requirement
/// (app/tenancy/middleware.py). Set once the user has at least one
/// membership (see MeResponse); switching organizations is out of scope
/// for Sprint 2 (single active org for now).
final activeOrganizationIdProvider = StateProvider<String?>((ref) => null);
