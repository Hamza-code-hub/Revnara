import 'package:flutter/material.dart';

import '../tokens.dart';

/// A single row in a list (opportunity pipeline, approval inbox, etc. from
/// Sprint 7 onward). Sizes to available width and wraps trailing content
/// instead of clipping it -- this is the pattern DS1.10's list/detail
/// reference layout builds on.
class RevnaraListRow extends StatelessWidget {
  const RevnaraListRow({
    super.key,
    required this.title,
    this.subtitle,
    this.leading,
    this.trailing,
    this.onTap,
  });

  final String title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: RevnaraSpacing.md,
          vertical: RevnaraSpacing.sm,
        ),
        child: Row(
          children: [
            if (leading != null) ...[
              leading!,
              const SizedBox(width: RevnaraSpacing.md),
            ],
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(title, style: theme.textTheme.titleSmall),
                  if (subtitle != null)
                    Text(
                      subtitle!,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                ],
              ),
            ),
            if (trailing != null) ...[
              const SizedBox(width: RevnaraSpacing.md),
              Wrap(
                spacing: RevnaraSpacing.xs,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [trailing!],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
