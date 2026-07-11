import 'package:flutter/material.dart';

enum RevnaraToastVariant { info, success, error }

/// Themed snackbar/toast helper (DS1.6) -- the single call site for showing
/// a toast, so duration/styling stay consistent everywhere instead of each
/// screen building its own [SnackBar].
class RevnaraToast {
  RevnaraToast._();

  static void show(
    BuildContext context,
    String message, {
    RevnaraToastVariant variant = RevnaraToastVariant.info,
  }) {
    final colorScheme = Theme.of(context).colorScheme;
    final Color background;
    switch (variant) {
      case RevnaraToastVariant.info:
        background = colorScheme.inverseSurface;
      case RevnaraToastVariant.success:
        background = colorScheme.primary;
      case RevnaraToastVariant.error:
        background = colorScheme.error;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: background,
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 4),
      ),
    );
  }
}
