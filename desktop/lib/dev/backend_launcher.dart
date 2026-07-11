// Conditional export: native platforms (Windows/macOS/Linux/mobile) get
// the real dart:io-based implementation, web gets a no-op stub --
// `dart:io` does not compile for web targets at all, so this can't be a
// runtime branch (e.g. `if (!kIsWeb)`), it has to be this compile-time
// conditional export.
export 'backend_launcher_stub.dart' if (dart.library.io) 'backend_launcher_io.dart';
