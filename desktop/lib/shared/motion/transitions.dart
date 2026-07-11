import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'curves.dart';
import 'durations.dart';
import 'motion.dart';

/// Shared-axis/fade-through page transition, applied consistently across
/// every GoRouter route (DS1.5). Wrap a route's builder with this to get a
/// [CustomTransitionPage] instead of [MaterialPage]'s default platform
/// transition.
CustomTransitionPage<T> revnaraPageTransition<T>({
  required LocalKey key,
  required GoRouterState state,
  required Widget child,
}) {
  return CustomTransitionPage<T>(
    key: key,
    child: child,
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      // Reduced motion: skip the transition entirely rather than relying on
      // a near-zero duration, since transitionDuration is fixed at page
      // creation and can't be recomputed per-context here.
      if (MediaQuery.of(context).disableAnimations) return child;

      final curved =
          CurvedAnimation(parent: animation, curve: RevnaraCurves.enter);
      return FadeTransition(
        opacity: curved,
        child: ScaleTransition(
          scale: Tween<double>(begin: 0.98, end: 1).animate(curved),
          child: child,
        ),
      );
    },
    transitionDuration: RevnaraDurations.long,
    reverseTransitionDuration: RevnaraDurations.medium,
  );
}

/// Staggered entrance for a list of items (opportunity/proposal/approval
/// lists from Sprint 7 onward). Wrap each list item's child in this,
/// passing its index.
class RevnaraStaggeredEntrance extends StatelessWidget {
  const RevnaraStaggeredEntrance({
    super.key,
    required this.index,
    required this.child,
  });

  final int index;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final delay = RevnaraMotion.duration(
      context,
      RevnaraDurations.staggerStep * index,
    );
    final duration = RevnaraMotion.duration(context, RevnaraDurations.medium);

    return TweenAnimationBuilder<double>(
      key: ValueKey(index),
      tween: Tween(begin: 0, end: 1),
      duration: duration + delay,
      curve: Interval(
        duration.inMicroseconds == 0
            ? 0
            : (delay.inMicroseconds / (duration + delay).inMicroseconds)
                .clamp(0.0, 1.0),
        1.0,
        curve: RevnaraCurves.enter,
      ),
      builder: (context, value, child) {
        return Opacity(
          opacity: value,
          child: Transform.translate(
            offset: Offset(0, (1 - value) * 8),
            child: child,
          ),
        );
      },
      child: child,
    );
  }
}
