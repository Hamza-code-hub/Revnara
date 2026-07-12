import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'app/app.dart';
import 'auth/session.dart';
import 'dev/backend_launcher.dart';

/// Only the Supabase *anon* key is ever configured client-side (Security
/// Invariant 1: no service-role key in Flutter). Normally supplied at
/// build/run time: `flutter run --dart-define=SUPABASE_URL=... --dart-define=SUPABASE_ANON_KEY=...`
const String _supabaseUrl = String.fromEnvironment('SUPABASE_URL');
const String _supabaseAnonKey = String.fromEnvironment('SUPABASE_ANON_KEY');

/// Dev convenience: if a plain `flutter run -d windows` (no --dart-define
/// flags at all) was used, fall back to reading the same gitignored
/// `dart_define.local.json` the VS Code launch config passes via
/// `--dart-define-from-file`, straight off disk at startup. Debug-only
/// (kDebugMode) -- a release build should never silently read an
/// arbitrary local file for its config. Fails soft to empty values if
/// the file doesn't exist (e.g. a machine that never set it up), same
/// "not configured" fallback screen as today.
Future<Map<String, String>> _loadLocalDartDefineFallback() async {
  try {
    final file = File('dart_define.local.json');
    if (!await file.exists()) return {};
    final decoded = jsonDecode(await file.readAsString()) as Map<String, dynamic>;
    return decoded.map((key, value) => MapEntry(key, value.toString()));
  } catch (_) {
    return {};
  }
}

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

  var supabaseUrl = _supabaseUrl;
  var supabaseAnonKey = _supabaseAnonKey;
  if (kDebugMode && (supabaseUrl.isEmpty || supabaseAnonKey.isEmpty)) {
    final fallback = await _loadLocalDartDefineFallback();
    supabaseUrl = supabaseUrl.isNotEmpty ? supabaseUrl : (fallback['SUPABASE_URL'] ?? '');
    supabaseAnonKey =
        supabaseAnonKey.isNotEmpty ? supabaseAnonKey : (fallback['SUPABASE_ANON_KEY'] ?? '');
  }

  if (supabaseUrl.isNotEmpty && supabaseAnonKey.isNotEmpty) {
    // `publishableKey` accepts both a legacy anon key and a newer
    // publishable key -- `anonKey` is deprecated in supabase_flutter but
    // the env var name here stays SUPABASE_ANON_KEY since that's still
    // what most Supabase project dashboards label the value.
    await Supabase.initialize(url: supabaseUrl, publishableKey: supabaseAnonKey);
    // Only flip this after initialize() actually succeeds -- session.dart's
    // isSupabaseConfigured is what every screen checks, not whether a URL
    // string happened to be non-empty.
    isSupabaseConfigured = true;
  }
  // If not configured, the app still boots (e.g. for `/dev/gallery` or
  // backend-only work) but auth screens will show a clear "not configured"
  // state rather than crashing -- see login_screen.dart.

  runApp(const ProviderScope(child: RevnaraApp()));
}
