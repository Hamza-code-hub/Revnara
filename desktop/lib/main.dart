import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'app/app.dart';

/// Only the Supabase *anon* key is ever configured client-side (Security
/// Invariant 1: no service-role key in Flutter). Supplied at build/run
/// time, matching the existing API_BASE_URL pattern:
/// `flutter run --dart-define=SUPABASE_URL=... --dart-define=SUPABASE_ANON_KEY=...`
const String _supabaseUrl = String.fromEnvironment('SUPABASE_URL');
const String _supabaseAnonKey = String.fromEnvironment('SUPABASE_ANON_KEY');

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  if (_supabaseUrl.isNotEmpty && _supabaseAnonKey.isNotEmpty) {
    // `publishableKey` accepts both a legacy anon key and a newer
    // publishable key -- `anonKey` is deprecated in supabase_flutter but
    // the env var name here stays SUPABASE_ANON_KEY since that's still
    // what most Supabase project dashboards label the value.
    await Supabase.initialize(url: _supabaseUrl, publishableKey: _supabaseAnonKey);
  }
  // If not configured, the app still boots (e.g. for `/dev/gallery` or
  // backend-only work) but auth screens will show a clear "not configured"
  // state rather than crashing -- see login_screen.dart.

  runApp(const ProviderScope(child: RevnaraApp()));
}
