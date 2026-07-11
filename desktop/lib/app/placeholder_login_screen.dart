import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'health_provider.dart';

/// Placeholder only — replaced by the real Supabase Auth login screen
/// in Sprint 2 (`features/settings/login_screen.dart` per the sprint plan).
class PlaceholderLoginScreen extends ConsumerWidget {
  const PlaceholderLoginScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final healthCheck = ref.watch(backendHealthProvider);

    return Scaffold(
      body: Column(
        children: [
          healthCheck.when(
            data: (isHealthy) => isHealthy
                ? const SizedBox.shrink()
                : _DevModeBanner(message: 'Backend unreachable at startup.'),
            loading: () => const SizedBox.shrink(),
            error: (error, stackTrace) =>
                const _DevModeBanner(message: 'Backend unreachable at startup.'),
          ),
          Expanded(
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('Revnara — sign in (Sprint 2)'),
                  // Debug-only convenience link -- not part of normal app
                  // navigation (the /dev/gallery route stays hidden in
                  // release builds and is never linked outside kDebugMode).
                  if (kDebugMode) ...[
                    const SizedBox(height: 16),
                    TextButton(
                      onPressed: () => context.go('/dev/gallery'),
                      child: const Text('View component gallery (dev)'),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DevModeBanner extends StatelessWidget {
  const _DevModeBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: Colors.amber.shade700,
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
      child: Text(
        message,
        style: const TextStyle(color: Colors.black),
        textAlign: TextAlign.center,
      ),
    );
  }
}
