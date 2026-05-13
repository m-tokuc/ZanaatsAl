import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';
import 'result_screen.dart';

class LoadingScreen extends StatefulWidget {
  final File imageFile;

  const LoadingScreen({super.key, required this.imageFile});

  @override
  State<LoadingScreen> createState() => _LoadingScreenState();
}

class _LoadingScreenState extends State<LoadingScreen> {
  final ApiService _apiService = ApiService();
  int _currentTextIndex = 0;
  Timer? _textTimer;

  final List<String> _loadingTexts = [
    'Görsel analiz ediliyor (Gemini 1.5 Flash)...',
    'Küresel pazarlar taranıyor (Etsy & Amazon)...',
    'İhracat stratejisi sentezleniyor...',
  ];

  @override
  void initState() {
    super.initState();
    _startTextAnimation();
    _analyzeProduct();
  }

  void _startTextAnimation() {
    _textTimer = Timer.periodic(const Duration(seconds: 3), (timer) {
      setState(() {
        _currentTextIndex = (_currentTextIndex + 1) % _loadingTexts.length;
      });
    });
  }

  Future<void> _analyzeProduct() async {
    try {
      final result = await _apiService.analyzeProduct(widget.imageFile);

      // Timer'ı iptal et
      _textTimer?.cancel();

      // ResultScreen'e geçiş
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) =>
              ResultScreen(data: result, imageFile: widget.imageFile),
        ),
      );
    } catch (e) {
      _textTimer?.cancel();
      // Hata durumu
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => Scaffold(
            backgroundColor: const Color(0xFF0A0E0B),
            body: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error, color: Colors.red, size: 80),
                  const SizedBox(height: 20),
                  Text(
                    'Analiz Hatası',
                    style: GoogleFonts.poppins(
                      fontSize: 24,
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    'Hata: $e',
                    style: GoogleFonts.poppins(
                      fontSize: 14,
                      color: Colors.grey[400],
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    }
  }

  @override
  void dispose() {
    _textTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E0B),
      body: SafeArea(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Yeşil SpinKitWave Animasyonu
              SpinKitWave(
                color: const Color(0xFF1B5E20),
                size: 80.0,
                itemCount: 5,
              ),

              const SizedBox(height: 40),

              // Dinamik Değişen Metin
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 500),
                child: Text(
                  _loadingTexts[_currentTextIndex],
                  key: ValueKey(_currentTextIndex),
                  style: GoogleFonts.poppins(
                    fontSize: 18,
                    color: Colors.white,
                    fontWeight: FontWeight.w500,
                    letterSpacing: 0.5,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),

              const SizedBox(height: 20),

              // İpucu metni
              Text(
                'Lütfen bekleyin, AI ajanımız çalışıyor...',
                style: GoogleFonts.poppins(
                  fontSize: 14,
                  color: Colors.grey[400],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
