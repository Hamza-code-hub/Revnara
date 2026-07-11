# Note: actual workflow files live in `.github/workflows/`

GitHub Actions only discovers workflows in `.github/workflows/` at the repo root — that's a GitHub platform requirement, not a project convention, so the actual CI/CD YAML lives there (`backend-ci.yml`, `flutter-ci.yml`, `secret-scan.yml`) rather than in this directory. This corrects `docs/Revnara_Sprint_Development_Plan.md` §3's canonical tree, which listed this path; treat `.github/workflows/` as the real location going forward.

This directory is kept as a place for CI-adjacent scripts/configs that workflows call into (e.g. a shared deploy script used by multiple workflow files), if that need comes up later.
