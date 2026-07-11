import 'package:flutter/widgets.dart';

/// Named width breakpoints (DS1.9), matching Material 3's window-size
/// classes so Sprint 15.5's mobile targets fall into the same system
/// instead of needing a separate one. See docs/design/tokens.md.
enum RevnaraBreakpoint {
  /// < 600px -- phone-class.
  compact,

  /// 600-1024px -- tablet / split-view.
  medium,

  /// > 1024px -- desktop.
  expanded;

  static const double compactMax = 600;
  static const double mediumMax = 1024;

  /// Resolves the current breakpoint from the widget tree's available
  /// width via [MediaQuery]. Prefer [RevnaraAdaptive.of] inside a
  /// [LayoutBuilder] when you need the *local* available width (e.g. inside
  /// a side panel) rather than the whole window's width.
  static RevnaraBreakpoint of(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    return fromWidth(width);
  }

  static RevnaraBreakpoint fromWidth(double width) {
    if (width < compactMax) return RevnaraBreakpoint.compact;
    if (width < mediumMax) return RevnaraBreakpoint.medium;
    return RevnaraBreakpoint.expanded;
  }

  bool get isCompact => this == RevnaraBreakpoint.compact;
  bool get isMedium => this == RevnaraBreakpoint.medium;
  bool get isExpanded => this == RevnaraBreakpoint.expanded;

  /// True for medium and expanded -- the common "wider than a phone" check.
  bool get isAtLeastMedium => this != RevnaraBreakpoint.compact;
}

/// A [LayoutBuilder]-based widget that resolves the breakpoint from the
/// *local* available width (not the whole window), and rebuilds only when
/// the breakpoint actually changes -- not on every pixel of resize.
class RevnaraAdaptive extends StatelessWidget {
  const RevnaraAdaptive({
    super.key,
    required this.compact,
    this.medium,
    this.expanded,
  });

  final WidgetBuilder compact;

  /// Falls back to [compact] if not provided.
  final WidgetBuilder? medium;

  /// Falls back to [medium] (or [compact]) if not provided.
  final WidgetBuilder? expanded;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final breakpoint = RevnaraBreakpoint.fromWidth(constraints.maxWidth);
        switch (breakpoint) {
          case RevnaraBreakpoint.compact:
            return compact(context);
          case RevnaraBreakpoint.medium:
            return (medium ?? compact)(context);
          case RevnaraBreakpoint.expanded:
            return (expanded ?? medium ?? compact)(context);
        }
      },
    );
  }
}
