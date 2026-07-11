import 'package:flutter/material.dart';

enum RevnaraButtonVariant { primary, secondary, destructive }

/// Primary/secondary/destructive button (DS1.6). Wraps Material's own
/// button widgets rather than reimplementing press/hover/focus states --
/// only the variant styling is Revnara-specific.
class RevnaraButton extends StatelessWidget {
  const RevnaraButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.variant = RevnaraButtonVariant.primary,
    this.icon,
  });

  final String label;
  final VoidCallback? onPressed;
  final RevnaraButtonVariant variant;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final child = icon == null
        ? Text(label)
        : Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 18),
              const SizedBox(width: 8),
              Text(label),
            ],
          );

    switch (variant) {
      case RevnaraButtonVariant.primary:
        return FilledButton(onPressed: onPressed, child: child);
      case RevnaraButtonVariant.secondary:
        return OutlinedButton(onPressed: onPressed, child: child);
      case RevnaraButtonVariant.destructive:
        final colorScheme = Theme.of(context).colorScheme;
        return FilledButton(
          style: FilledButton.styleFrom(
            backgroundColor: colorScheme.error,
            foregroundColor: colorScheme.onError,
          ),
          onPressed: onPressed,
          child: child,
        );
    }
  }
}
