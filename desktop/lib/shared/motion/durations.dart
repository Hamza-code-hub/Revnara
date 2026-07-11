/// Named animation durations. See docs/design/motion-principles.md.
class RevnaraDurations {
  RevnaraDurations._();

  static const Duration micro = Duration(milliseconds: 150);
  static const Duration short = Duration(milliseconds: 200);
  static const Duration medium = Duration(milliseconds: 300);
  static const Duration long = Duration(milliseconds: 400);
  static const Duration staggerStep = Duration(milliseconds: 40);
}
