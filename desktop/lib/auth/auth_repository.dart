import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'session.dart';

class AuthException implements Exception {
  AuthException(this.message);
  final String message;

  @override
  String toString() => message;
}

/// Sign-in/sign-out operations (FE2.1/FE2.2), separated from
/// [session.dart]'s state exposure so screens depend on a small,
/// testable surface rather than the raw Supabase client.
class AuthRepository {
  AuthRepository(this._client);

  final SupabaseClient _client;

  Future<void> signInWithPassword({
    required String email,
    required String password,
  }) async {
    try {
      await _client.auth.signInWithPassword(email: email, password: password);
    } on AuthApiException catch (e) {
      throw AuthException(e.message);
    }
  }

  Future<void> signOut() async {
    await _client.auth.signOut();
  }
}

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.watch(supabaseClientProvider));
});
