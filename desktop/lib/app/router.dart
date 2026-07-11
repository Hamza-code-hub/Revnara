import 'package:go_router/go_router.dart';

import '../shared/dev/component_gallery.dart';
import '../shared/motion/transitions.dart';
import 'placeholder_login_screen.dart';

/// Sprint 1 scope: a single placeholder route so the app shell and
/// navigation stack exist before Sprint 2 wires up real Supabase Auth.
///
/// Sprint 1.5 adds `/dev/gallery` -- a hidden route (never linked from
/// normal app navigation) for design/QA review of the component library.
final GoRouter appRouter = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(
      path: '/login',
      pageBuilder: (context, state) => revnaraPageTransition(
        key: state.pageKey,
        state: state,
        child: const PlaceholderLoginScreen(),
      ),
    ),
    GoRoute(
      path: '/dev/gallery',
      builder: (context, state) => const ComponentGalleryScreen(),
    ),
  ],
);
