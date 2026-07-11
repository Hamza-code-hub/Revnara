import 'package:flutter/material.dart';

import '../tokens.dart';

/// Card container (DS1.6). Sizes to available width -- callers constrain
/// width via layout (e.g. a grid or a max-width wrapper), never a literal
/// pixel value baked into the card itself.
class RevnaraCard extends StatelessWidget {
  const RevnaraCard({
    super.key,
    required this.child,
    this.onTap,
    this.padding = const EdgeInsets.all(RevnaraSpacing.md),
  });

  final Widget child;
  final VoidCallback? onTap;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    final content = Padding(padding: padding, child: child);

    return Card(
      clipBehavior: Clip.antiAlias,
      child: onTap == null ? content : InkWell(onTap: onTap, child: content),
    );
  }
}
