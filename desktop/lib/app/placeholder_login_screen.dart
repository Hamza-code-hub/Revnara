import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

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
          const Expanded(
            child: Center(
              child: Text('Revnara — sign in (Sprint 2)'),
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
