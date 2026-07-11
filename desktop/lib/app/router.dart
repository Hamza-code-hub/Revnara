import 'package:go_router/go_router.dart';

import 'placeholder_login_screen.dart';

/// Sprint 1 scope: a single placeholder route so the app shell and
/// navigation stack exist before Sprint 2 wires up real Supabase Auth.
final GoRouter appRouter = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(
      path: '/login',
      builder: (context, state) => const PlaceholderLoginScreen(),
    ),
  ],
);
