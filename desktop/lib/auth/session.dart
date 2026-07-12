import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

/// Set by main.dart immediately after a successful `Supabase.initialize()`
/// call -- exposed here so any screen can show a clear "not configured"
/// state instead of a cryptic Supabase internal error when neither a
/// --dart-define nor the dart_define.local.json fallback provided real
/// credentials (e.g. someone running just `flutter run` for `/dev/gallery`
/// work without setting up a Supabase project yet).
///
/// Deliberately NOT a compile-time `bool.hasEnvironment` check anymore --
/// that only detected --dart-define, so it stayed false (showing the
/// "not configured" screen) even after main.dart's runtime fallback had
/// already initialized Supabase successfully from dart_define.local.json,
/// a real bug caught by actually running `flutter run -d windows` with no
/// flags and watching the screen it produced, not just checking the logs.
/// Stays false under `flutter test` (main() never runs there), so
/// LoginForm's own tests are unaffected -- see its docstring.
bool isSupabaseConfigured = false;

/// Wraps the Supabase Flutter SDK's auth session (FE2.1). Session
/// persistence/secure storage is handled by supabase_flutter itself --
/// this does not re-implement token storage, only exposes the current
/// state to the rest of the app as a Riverpod stream.
///
/// Security Invariant 1-3 (never store the service-role key or any
/// backend secret client-side): only the Supabase *anon* key is ever
/// configured client-side (main.dart), and the session token this
/// exposes is the user's own short-lived Supabase Auth JWT, not a
/// backend/service credential.
final supabaseClientProvider = Provider<SupabaseClient>((ref) {
  return Supabase.instance.client;
});

/// Streams every auth state change (sign in, sign out, token refresh).
/// Empty stream when Supabase isn't configured, rather than throwing.
final authStateProvider = StreamProvider<AuthState>((ref) {
  if (!isSupabaseConfigured) return const Stream.empty();
  return ref.watch(supabaseClientProvider).auth.onAuthStateChange;
});

/// The current session, or null if signed out (or Supabase isn't
/// configured). Convenience derived from [authStateProvider] so screens
/// don't need to unwrap AuthState.
final currentSessionProvider = Provider<Session?>((ref) {
  if (!isSupabaseConfigured) return null;
  final authState = ref.watch(authStateProvider);
  return authState.valueOrNull?.session ?? Supabase.instance.client.auth.currentSession;
});

final isAuthenticatedProvider = Provider<bool>((ref) {
  return ref.watch(currentSessionProvider) != null;
});
