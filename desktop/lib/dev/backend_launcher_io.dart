import 'dart:io';

/// Base URL used for the readiness check -- mirrors api_client.dart's
/// `apiBaseUrl` default/override exactly (kept as its own constant here,
/// not imported from api_client.dart, since this file runs before
/// ProviderScope/Riverpod exist and should have no dependency on the rest
/// of the app).
const String _apiBaseUrl =
    String.fromEnvironment('API_BASE_URL', defaultValue: 'http://127.0.0.1:8000');

/// Dev-only convenience: auto-starts the FastAPI backend when `flutter
/// run` starts, so a developer doesn't need a second terminal running
/// `uvicorn` by hand. Never used in release builds (gated by kDebugMode
/// in main.dart) and never on mobile, where a locally-run Python backend
/// makes no sense.
///
/// Every step here fails soft: if anything goes wrong (backend/ not
/// found, Python missing, port already in use by something else), this
/// prints a message and the app continues -- exactly as it did before
/// this existed, just without the second manual terminal.
Future<void> tryAutoStartBackend() async {
  if (Platform.isAndroid || Platform.isIOS) return;

  if (await _isBackendHealthy()) {
    stdout.writeln('[dev] Backend already running at $_apiBaseUrl -- not starting another one.');
    return;
  }

  final backendDir = _findBackendDirectory();
  if (backendDir == null) {
    stdout.writeln(
      '[dev] Could not locate a sibling backend/ directory (looked for '
      'backend/pyproject.toml walking up from ${Directory.current.path}) '
      '-- skipping backend auto-start.',
    );
    return;
  }

  final pythonExecutable = _resolvePythonExecutable(backendDir);
  stdout.writeln(
    '[dev] Starting backend: $pythonExecutable -m uvicorn app.main:app '
    '--reload (cwd: ${backendDir.path})',
  );

  try {
    await Process.start(
      pythonExecutable,
      ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000'],
      workingDirectory: backendDir.path,
      mode: ProcessStartMode.detached,
    );
    stdout.writeln(
      '[dev] Backend launching in the background -- give it a few seconds '
      'to become ready (the app shows a banner if it isn\'t up yet).',
    );
  } catch (e) {
    stdout.writeln('[dev] Failed to auto-start the backend: $e');
  }
}

Future<bool> _isBackendHealthy() async {
  final client = HttpClient()..connectionTimeout = const Duration(milliseconds: 500);
  try {
    final request = await client
        .getUrl(Uri.parse('$_apiBaseUrl/health'))
        .timeout(const Duration(seconds: 1));
    final response = await request.close().timeout(const Duration(seconds: 1));
    return response.statusCode == 200;
  } catch (_) {
    return false;
  } finally {
    client.close(force: true);
  }
}

/// Walks up from the current working directory looking for `backend/`
/// (identified by `backend/pyproject.toml`, not just the folder name, so
/// an unrelated "backend" directory elsewhere doesn't match). `flutter
/// run` sets the working directory to the Flutter project root
/// (`desktop/`), so this is normally found one level up on the first try
/// -- the walk-up exists so this still works if invoked from elsewhere.
Directory? _findBackendDirectory() {
  var dir = Directory.current;
  for (var i = 0; i < 5; i++) {
    final candidate = Directory('${dir.path}/backend');
    if (File('${candidate.path}/pyproject.toml').existsSync()) {
      return candidate;
    }
    final parent = dir.parent;
    if (parent.path == dir.path) break;
    dir = parent;
  }
  return null;
}

String _resolvePythonExecutable(Directory backendDir) {
  final windowsVenvPython = File('${backendDir.path}/.venv/Scripts/python.exe');
  if (windowsVenvPython.existsSync()) return windowsVenvPython.path;

  final unixVenvPython = File('${backendDir.path}/.venv/bin/python');
  if (unixVenvPython.existsSync()) return unixVenvPython.path;

  // No venv found -- fall back to whatever Python is on PATH, which will
  // fail loudly (caught above) if the backend's dependencies aren't
  // installed globally.
  return Platform.isWindows ? 'python' : 'python3';
}
