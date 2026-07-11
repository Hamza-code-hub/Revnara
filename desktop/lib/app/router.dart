import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../auth/membership_provider.dart';
import '../auth/session.dart';
import '../features/command_center/command_center_screen.dart';
import '../features/company/company_profile_screen.dart';
import '../features/company/team_portfolio_screen.dart';
import '../features/onboarding/create_organization_screen.dart';
import '../features/settings/login_screen.dart';
import '../features/settings/team_management_screen.dart';
import '../shared/dev/component_gallery.dart';
import '../shared/motion/transitions.dart';

/// Notifies GoRouter to re-evaluate `redirect` whenever auth or membership
/// state changes -- without this, GoRouter only re-runs redirect on
/// navigation events, so a sign-in completing in the background (e.g. the
/// Supabase SDK finishing a token refresh) would never actually move the
/// user off /login.
class _RouterRefreshNotifier extends ChangeNotifier {
  _RouterRefreshNotifier(Ref ref) {
    ref.listen(isAuthenticatedProvider, (previous, next) => notifyListeners());
    ref.listen(meProvider, (previous, next) => notifyListeners());
  }
}

final routerProvider = Provider<GoRouter>((ref) {
  final refreshNotifier = _RouterRefreshNotifier(ref);

  return GoRouter(
    initialLocation: '/login',
    refreshListenable: refreshNotifier,
    redirect: (context, state) {
      final location = state.matchedLocation;

      // Never redirect away from the hidden dev route (Sprint 1.5).
      if (location.startsWith('/dev/gallery')) return null;

      final isAuthenticated = ref.read(isAuthenticatedProvider);
      if (!isAuthenticated) {
        return location == '/login' ? null : '/login';
      }

      // Authenticated from here on -- resolve membership state (FE2.3's
      // "authenticated users to /command-center", extended with the
      // onboarding step a zero-membership user needs first).
      final meAsync = ref.read(meProvider);
      return meAsync.when(
        data: (me) {
          final hasActiveMembership =
              me?.memberships.any((m) => m.status == 'active') ?? false;

          if (!hasActiveMembership) {
            return location == '/onboarding/create-organization'
                ? null
                : '/onboarding/create-organization';
          }

          if (location == '/login' || location == '/onboarding/create-organization') {
            return '/command-center';
          }
          return null;
        },
        // Stay on the current route while /me is loading/erroring rather
        // than bouncing the user mid-resolution.
        loading: () => null,
        error: (error, stackTrace) => null,
      );
    },
    routes: [
      GoRoute(
        path: '/login',
        pageBuilder: (context, state) => revnaraPageTransition(
          key: state.pageKey,
          state: state,
          child: const LoginScreen(),
        ),
      ),
      GoRoute(
        path: '/onboarding/create-organization',
        pageBuilder: (context, state) => revnaraPageTransition(
          key: state.pageKey,
          state: state,
          child: const CreateOrganizationScreen(),
        ),
      ),
      GoRoute(
        path: '/command-center',
        pageBuilder: (context, state) => revnaraPageTransition(
          key: state.pageKey,
          state: state,
          child: const CommandCenterScreen(),
        ),
      ),
      GoRoute(
        path: '/settings/team',
        pageBuilder: (context, state) => revnaraPageTransition(
          key: state.pageKey,
          state: state,
          child: const TeamManagementScreen(),
        ),
      ),
      GoRoute(
        path: '/company/profile',
        pageBuilder: (context, state) => revnaraPageTransition(
          key: state.pageKey,
          state: state,
          child: const CompanyProfileScreen(),
        ),
      ),
      GoRoute(
        path: '/company/brain',
        pageBuilder: (context, state) => revnaraPageTransition(
          key: state.pageKey,
          state: state,
          child: const TeamPortfolioScreen(),
        ),
      ),
      GoRoute(
        path: '/dev/gallery',
        builder: (context, state) => const ComponentGalleryScreen(),
      ),
    ],
  );
});
