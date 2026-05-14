import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI Assistant',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        scaffoldBackgroundColor: const Color(0xFF0A0E0B),
        primaryColor: const Color(0xFF1B5E20),
        textTheme: GoogleFonts.poppinsTextTheme(),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF1B5E20),
          background: Color(0xFF0A0E0B),
        ),
      ),
      home: const HomeScreen(),
    );
  }
}
