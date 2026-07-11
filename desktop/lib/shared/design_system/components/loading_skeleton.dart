import 'package:flutter/material.dart';

import '../tokens.dart';

/// Shimmering loading placeholder (DS1.6). Sizes to available width via
/// [width] defaulting to `double.infinity`, height is the only fixed
/// dimension (skeletons stand in for text/media of a known height).
class RevnaraLoadingSkeleton extends StatefulWidget {
  const RevnaraLoadingSkeleton({
    super.key,
    this.width = double.infinity,
    this.height = 16,
  });

  final double width;
  final double height;

  @override
  State<RevnaraLoadingSkeleton> createState() =>
      _RevnaraLoadingSkeletonState();
}

class _RevnaraLoadingSkeletonState extends State<RevnaraLoadingSkeleton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  bool _started = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // MediaQuery must not be read in initState() -- it may not yet be
    // established and won't react to later changes. didChangeDependencies
    // is called after initState and again whenever MediaQuery changes.
    if (!_started && !MediaQuery.of(context).disableAnimations) {
      _controller.repeat();
      _started = true;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final base = Theme.of(context).colorScheme.surfaceContainerHighest;
    final highlight = Theme.of(context).colorScheme.surfaceContainerHigh;
    final reduceMotion = MediaQuery.of(context).disableAnimations;

    if (reduceMotion) {
      return Container(
        width: widget.width,
        height: widget.height,
        decoration: BoxDecoration(
          color: base,
          borderRadius: BorderRadius.circular(RevnaraRadius.sm),
        ),
      );
    }

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          width: widget.width,
          height: widget.height,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(RevnaraRadius.sm),
            gradient: LinearGradient(
              begin: Alignment(-1 + _controller.value * 2, 0),
              end: Alignment(1 + _controller.value * 2, 0),
              colors: [base, highlight, base],
              stops: const [0.4, 0.5, 0.6],
            ),
          ),
        );
      },
    );
  }
}
