import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../api/models.dart';
import 'session.dart';

/// The signed-in user's `/me` response -- memberships across every
/// organization they belong to. Also the single place
/// [activeOrganizationIdProvider] gets set once memberships are known
/// (first active membership, per Sprint 2's single-active-org scope;
/// switching organizations is a later sprint).
final meProvider = FutureProvider<MeResponse?>((ref) async {
  final isAuthenticated = ref.watch(isAuthenticatedProvider);
  if (!isAuthenticated) return null;

  final client = ref.watch(apiClientProvider);
  final me = await client.getMe();

  final activeMemberships = me.memberships.where((m) => m.status == 'active');
  if (activeMemberships.isNotEmpty) {
    final newOrganizationId = activeMemberships.first.organizationId;
    if (ref.read(activeOrganizationIdProvider) != newOrganizationId) {
      ref.read(activeOrganizationIdProvider.notifier).state = newOrganizationId;
    }
  }

  return me;
});

final hasActiveOrganizationProvider = Provider<bool>((ref) {
  final me = ref.watch(meProvider).valueOrNull;
  return me?.memberships.any((m) => m.status == 'active') ?? false;
});
