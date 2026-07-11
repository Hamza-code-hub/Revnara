import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'router.dart';

class RevnaraApp extends StatelessWidget {
  const RevnaraApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Revnara',
      debugShowCheckedModeBanner: false,
      routerConfig: appRouter,
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
