import 'package:flutter/material.dart';

import '../theme.dart';
import '../tokens.dart';

/// Generic colored status pill -- the primitive every specific badge below
/// is built from, and reusable directly once Sprint 11 introduces the
/// canonical `PlatformCapability` status enum (map status -> label/color at
/// the UI layer there, same pattern used here).
class RevnaraStatusChip extends StatelessWidget {
  const RevnaraStatusChip({
    super.key,
    required this.label,
    required this.color,
    this.icon,
  });

  final String label;
  final Color color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: RevnaraSpacing.sm,
        vertical: 2,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(RevnaraRadius.pill),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 12, color: color),
            const SizedBox(width: 4),
          ],
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

/// R0-R6 risk tier badge, per docs/BDOS_Enforcement_Spec.md's risk tiers.
class RevnaraRiskTierBadge extends StatelessWidget {
  const RevnaraRiskTierBadge({super.key, required this.tier});

  /// 0-6, matching R0-R6.
  final int tier;

  @override
  Widget build(BuildContext context) {
    assert(tier >= 0 && tier <= 6, 'Risk tier must be 0-6 (R0-R6)');
    final color = context.governanceColors.riskScale[tier];
    return RevnaraStatusChip(label: 'R$tier', color: color);
  }
}

/// Evidence-cited vs. assumption badge for proposal claims (Sprint 9).
class RevnaraEvidenceBadge extends StatelessWidget {
  const RevnaraEvidenceBadge({super.key, required this.cited});

  final bool cited;

  @override
  Widget build(BuildContext context) {
    final colors = context.governanceColors;
    return cited
        ? RevnaraStatusChip(
            label: 'Evidence-cited',
            color: colors.evidenceCited,
            icon: Icons.fact_check_outlined,
          )
        : RevnaraStatusChip(
            label: 'Assumption',
            color: colors.assumption,
            icon: Icons.help_outline,
          );
  }
}

/// Approval bound to payload hash / policy version (Sprint 10).
class RevnaraApprovalBoundBadge extends StatelessWidget {
  const RevnaraApprovalBoundBadge({super.key});

  @override
  Widget build(BuildContext context) {
    return RevnaraStatusChip(
      label: 'Approved • Bound',
      color: context.governanceColors.approvedBound,
      icon: Icons.lock_outline,
    );
  }
}

/// Human-native-only capability indicator (Sprint 11) -- deliberately
/// muted, since this is a normal expected state, not an error.
class RevnaraHumanNativeBadge extends StatelessWidget {
  const RevnaraHumanNativeBadge({super.key});

  @override
  Widget build(BuildContext context) {
    return RevnaraStatusChip(
      label: 'Human-native only',
      color: context.governanceColors.humanNativeOnly,
      icon: Icons.person_outline,
    );
  }
}
