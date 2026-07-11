import 'package:dio/dio.dart';

/// Base URL is supplied at build/run time, e.g.
/// `flutter run --dart-define=API_BASE_URL=http://localhost:8000`.
/// Defaults to the local backend dev server so `flutter run` works out of the box.
const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000',
);

class ApiClient {
  ApiClient({Dio? dio}) : _dio = dio ?? Dio(BaseOptions(baseUrl: apiBaseUrl));

  final Dio _dio;

  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get('/health');
      return response.statusCode == 200;
    } on DioException {
      return false;
    }
  }
}
