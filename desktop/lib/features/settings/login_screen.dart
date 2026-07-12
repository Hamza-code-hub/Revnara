import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../auth/auth_repository.dart';
import '../../auth/session.dart';
import '../../shared/design_system/design_system.dart';

/// Real Supabase Auth login screen (FE2.2), replacing Sprint 1's
/// placeholder. Email/password only for Sprint 2 (SSO deferred per
/// BDOS_MVP_Cut.md P1).
class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    if (!isSupabaseConfigured) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const RevnaraEmptyState(
                icon: Icons.cloud_off,
                title: 'Supabase is not configured',
                message:
                    'Create desktop/dart_define.local.json (see the .example file next to it) '
                    'or run with --dart-define=SUPABASE_URL=... --dart-define=SUPABASE_ANON_KEY=... '
                    'to enable sign-in (see docs/Revnara_Sprint_Development_Plan.md §4).',
              ),
              // Debug-only, one-click way to see the design system without
              // Supabase configured or typing a route by hand (desktop has
              // no URL bar) -- originally added in Sprint 1
              // (placeholder_login_screen.dart) and re-added here since
              // Sprint 2 replaced that placeholder with this real screen.
              if (kDebugMode) ...[
                const SizedBox(height: RevnaraSpacing.lg),
                RevnaraButton(
                  label: 'View component gallery',
                  variant: RevnaraButtonVariant.secondary,
                  onPressed: () => context.go('/dev/gallery'),
                ),
              ],
            ],
          ),
        ),
      );
    }

    // No component-gallery shortcut here -- that debug convenience only
    // matters when there's nothing else to see (the "not configured"
    // fallback above). Once real sign-in is available, a developer can
    // just log in and see the actual app.
    return const Scaffold(body: Center(child: LoginForm()));
  }
}

/// The actual sign-in form, split out from [LoginScreen] so it's testable
/// directly (test/widget/settings/login_form_test.dart) without the
/// `isSupabaseConfigured` gate above it -- that flag stays false under
/// `flutter test` since main() (the only place that ever sets it true)
/// never runs there, which would otherwise make the form's validation
/// logic unreachable in any normal test run.
class LoginForm extends ConsumerStatefulWidget {
  const LoginForm({super.key});

  @override
  ConsumerState<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends ConsumerState<LoginForm> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  String? _emailError;
  String? _passwordError;
  String? _formError;
  bool _isSubmitting = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    setState(() {
      _emailError = email.isEmpty ? 'Email is required' : null;
      _passwordError = password.isEmpty ? 'Password is required' : null;
      _formError = null;
    });
    if (_emailError != null || _passwordError != null) return;

    setState(() => _isSubmitting = true);
    try {
      await ref
          .read(authRepositoryProvider)
          .signInWithPassword(email: email, password: password);
      // No explicit navigation here -- the router's redirect guard
      // (app/router.dart) reacts to authStateProvider and moves to
      // /command-center or /onboarding automatically.
    } on AuthException catch (e) {
      setState(() => _formError = e.message);
    } catch (e) {
      // Defensive fallback for anything unexpected (e.g. Supabase not
      // configured/reachable) -- never let sign-in crash silently instead
      // of surfacing a message the user can act on.
      setState(() => _formError = 'Sign-in failed: $e');
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      // A max width, not a fixed width -- the form still shrinks to fit
      // narrower windows via the adaptive layout discipline (Sprint 1.5
      // DS1.9), it just doesn't grow unreasonably wide on a large desktop
      // window.
      constraints: const BoxConstraints(maxWidth: 360),
      child: Padding(
        padding: const EdgeInsets.all(RevnaraSpacing.lg),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Revnara',
              style: Theme.of(context).textTheme.headlineMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: RevnaraSpacing.xl),
            RevnaraTextField(
              label: 'Email',
              controller: _emailController,
              errorText: _emailError,
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: RevnaraSpacing.md),
            RevnaraTextField(
              label: 'Password',
              controller: _passwordController,
              errorText: _passwordError,
              obscureText: true,
            ),
            if (_formError != null) ...[
              const SizedBox(height: RevnaraSpacing.sm),
              Text(
                _formError!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: RevnaraSpacing.lg),
            RevnaraButton(
              label: _isSubmitting ? 'Signing in...' : 'Sign in',
              onPressed: _isSubmitting ? null : _submit,
            ),
          ],
        ),
      ),
    );
  }
}
