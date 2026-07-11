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
  }) : _dio = dio ??
            Dio(BaseOptions(
              baseUrl: apiBaseUrl,
              headers: {
                if (accessToken != null) 'Authorization': 'Bearer $accessToken',
                'X-Organization-Id': ?organizationId,
              },
            ));

  final Dio _dio;

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

  Future<Response> _guarded(Future<Response> Function() request) async {
    try {
      return await request();
    } on DioException catch (e) {
      final detail = e.response?.data is Map
          ? (e.response?.data as Map)['detail']
          : e.message;
      throw ApiException(e.response?.statusCode, detail?.toString() ?? 'Request failed');
    }
  }
}

final apiClientProvider = Provider<ApiClient>((ref) {
  final session = ref.watch(currentSessionProvider);
  final organizationId = ref.watch(activeOrganizationIdProvider);
  return ApiClient(accessToken: session?.accessToken, organizationId: organizationId);
});

/// The organization the app is currently operating in -- explicit state,
/// never inferred, mirroring the backend's X-Organization-Id requirement
/// (app/tenancy/middleware.py). Set once the user has at least one
/// membership (see MeResponse); switching organizations is out of scope
/// for Sprint 2 (single active org for now).
final activeOrganizationIdProvider = StateProvider<String?>((ref) => null);
