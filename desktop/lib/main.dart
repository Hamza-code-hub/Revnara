import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'app/app.dart';
import 'dev/backend_launcher.dart';

/// Only the Supabase *anon* key is ever configured client-side (Security
/// Invariant 1: no service-role key in Flutter). Supplied at build/run
/// time, matching the existing API_BASE_URL pattern:
/// `flutter run --dart-define=SUPABASE_URL=... --dart-define=SUPABASE_ANON_KEY=...`
const String _supabaseUrl = String.fromEnvironment('SUPABASE_URL');
const String _supabaseAnonKey = String.fromEnvironment('SUPABASE_ANON_KEY');

/// Escape hatch for the dev-only backend auto-start below:
/// `flutter run --dart-define=AUTO_START_BACKEND=false` to disable it
/// (e.g. if you're already running the backend yourself in another
/// terminal with different flags, or don't have Python set up locally).
const bool _autoStartBackend =
    bool.fromEnvironment('AUTO_START_BACKEND', defaultValue: true);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  if (kDebugMode && _autoStartBackend) {
    // Dev convenience only -- never in release builds. Fails soft (see
    // backend_launcher_io.dart): if the backend can't be found or
    // started, this just logs and the app continues exactly as it did
    // before this existed.
    await tryAutoStartBackend();
  }

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
