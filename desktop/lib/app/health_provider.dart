import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

/// Sprint 1 scope: a simple reachability check used to show a dev-mode
/// banner if the local backend isn't running. Not used for anything
/// beyond local developer feedback.
final backendHealthProvider = FutureProvider<bool>((ref) async {
  final client = ref.watch(apiClientProvider);
  return client.checkHealth();
});
