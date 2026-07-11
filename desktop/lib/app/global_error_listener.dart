import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../shared/design_system/design_system.dart';

/// FE3.1: shows a consistent "not authorized" toast for any 403 response
/// from anywhere in the app, via api_client.dart's `onForbidden` hook --
/// wrapped around the router content (app.dart) so an individual screen
/// never needs its own 403 handling just to avoid crashing or silently
/// failing. Screens can still show their own inline error too, where
/// contextual detail helps -- this is the floor every screen gets for
/// free, not a replacement for that.
class GlobalErrorListener extends ConsumerWidget {
  const GlobalErrorListener({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen<String?>(unauthorizedEventProvider, (previous, message) {
      if (message == null) return;

      RevnaraToast.show(context, message, variant: RevnaraToastVariant.error);

      // Reset to null so an identical consecutive 403 message still
      // re-triggers this listener next time -- StateProvider only
      // notifies on an actual value change, and two 403s in a row could
      // easily carry the exact same message string.
      Future.microtask(
        () => ref.read(unauthorizedEventProvider.notifier).state = null,
      );
    });

    return child;
  }
}
