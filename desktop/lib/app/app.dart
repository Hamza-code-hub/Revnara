import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../shared/design_system/theme.dart';
import 'router.dart';
import 'theme_mode_provider.dart';

class RevnaraApp extends ConsumerWidget {
  const RevnaraApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);

    return MaterialApp.router(
      title: 'Revnara',
      debugShowCheckedModeBanner: false,
      routerConfig: appRouter,
      theme: RevnaraTheme.light(),
      darkTheme: RevnaraTheme.dark(),
      themeMode: themeMode,
      // i18n scaffolded from day one (FE1.5) even though only English ships
      // in Release 1 — see the sprint plan for the rationale.
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [Locale('en')],
    );
  }
}
