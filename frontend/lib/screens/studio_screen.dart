import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';

import '../services/api_service.dart';

/// Stüdyo AI Ekranı
///
/// Kullanıcı bir ürün fotoğrafı seçer → backend'de rembg + Gemini pipeline
/// çalışır → profesyonel stüdyo görseli ekranda gösterilir.
class StudioAIScreen extends StatefulWidget {
  final XFile imageFile;

  const StudioAIScreen({super.key, required this.imageFile});

  @override
  State<StudioAIScreen> createState() => _StudioAIScreenState();
}

class _StudioAIScreenState extends State<StudioAIScreen>
    with TickerProviderStateMixin {
  // -----------------------------------------------------------------------
  // State
  // -----------------------------------------------------------------------
  bool _isLoading = false;
  bool _isDone = false;
  String? _errorMessage;
  String? _studioImageBase64;

  late final AnimationController _pulseController;
  late final Animation<double> _pulseAnimation;

  late final AnimationController _fadeController;
  late final Animation<double> _fadeAnimation;

  // Loading mesajları – sırayla gösterilir
  final List<String> _loadingMessages = [
    '🔬 Ürün analiz ediliyor...',
    '✂️ Arka plan kaldırılıyor...',
    '🎨 Mermer tezgah hazırlanıyor...',
    '💡 Stüdyo ışıklandırması ayarlanıyor...',
    '🪵 Ahşap doku ekleniyor...',
    '✨ Son rötuşlar yapılıyor...',
  ];
  int _loadingMsgIndex = 0;

  @override
  void initState() {
    super.initState();

    // Pulse animasyonu (yükleme spinner için)
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.85, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    // Fade animasyonu (sonuç görseli için)
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _fadeAnimation = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeIn,
    );

    // Ekran açılır açılmaz işlemi başlat
    _startStudioAI();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _fadeController.dispose();
    super.dispose();
  }

  // -----------------------------------------------------------------------
  // İş Mantığı
  // -----------------------------------------------------------------------

  Future<void> _startStudioAI() async {
    setState(() {
      _isLoading = true;
      _isDone = false;
      _errorMessage = null;
      _studioImageBase64 = null;
      _loadingMsgIndex = 0;
    });

    // Loading mesajlarını döngülü göster
    final msgTimer = Stream.periodic(const Duration(seconds: 2), (i) => i)
        .take(_loadingMessages.length);

    msgTimer.listen((i) {
      if (mounted && _isLoading) {
        setState(() => _loadingMsgIndex = i);
      }
    });

    try {
      final result = await ApiService.generateStudioImage(widget.imageFile);
      if (mounted) {
        setState(() {
          _studioImageBase64 = result['studio_image_base64'] as String?;
          _isLoading = false;
          _isDone = true;
        });
        _fadeController.forward();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = e.toString().replaceFirst('Exception: ', '');
        });
      }
    }
  }

  // -----------------------------------------------------------------------
  // UI Helpers
  // -----------------------------------------------------------------------

  Widget _buildOriginalImage() {
    return ClipRRect(
      borderRadius: BorderRadius.circular(20),
      child: kIsWeb
          ? Image.network(widget.imageFile.path, fit: BoxFit.cover)
          : Image.file(File(widget.imageFile.path), fit: BoxFit.cover),
    );
  }

  Widget _buildStudioImage() {
    if (_studioImageBase64 == null) return const SizedBox();
    final bytes = base64Decode(_studioImageBase64!);
    return ClipRRect(
      borderRadius: BorderRadius.circular(20),
      child: Image.memory(bytes, fit: BoxFit.cover),
    );
  }

  Widget _buildLoadingOverlay() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.88),
        borderRadius: BorderRadius.circular(20),
      ),
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Pulsing icon
          ScaleTransition(
            scale: _pulseAnimation,
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const SweepGradient(
                  colors: [
                    Color(0xFF7B2FF7),
                    Color(0xFF00D4FF),
                    Color(0xFF7B2FF7),
                  ],
                ),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF7B2FF7).withOpacity(0.5),
                    blurRadius: 30,
                    spreadRadius: 4,
                  ),
                ],
              ),
              child: const Icon(
                Icons.auto_awesome,
                color: Colors.white,
                size: 48,
              ),
            ),
          ),
          const SizedBox(height: 32),
          Text(
            'Ürününüz Profesyonel\nStüdyo Ortamına Taşınıyor...',
            textAlign: TextAlign.center,
            style: GoogleFonts.poppins(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w700,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 20),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 400),
            child: Text(
              _loadingMessages[_loadingMsgIndex],
              key: ValueKey<int>(_loadingMsgIndex),
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: const Color(0xFF00D4FF),
                fontSize: 13,
              ),
            ),
          ),
          const SizedBox(height: 24),
          const LinearProgressIndicator(
            backgroundColor: Color(0xFF2E332F),
            valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF7B2FF7)),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorWidget() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.red.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.red.withOpacity(0.4)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, color: Colors.redAccent, size: 48),
          const SizedBox(height: 16),
          Text(
            'Bir Hata Oluştu',
            style: GoogleFonts.poppins(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            _errorMessage ?? 'Bilinmeyen hata',
            textAlign: TextAlign.center,
            style: GoogleFonts.poppins(color: Colors.grey[400], fontSize: 13),
          ),
          const SizedBox(height: 20),
          ElevatedButton.icon(
            icon: const Icon(Icons.refresh),
            label: const Text('Tekrar Dene'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF7B2FF7),
              foregroundColor: Colors.white,
              padding:
                  const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: _startStudioAI,
          ),
        ],
      ),
    );
  }

  // -----------------------------------------------------------------------
  // Build
  // -----------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E0B),
      body: CustomScrollView(
        slivers: [
          // ---- AppBar ----
          SliverAppBar(
            expandedHeight: 0,
            floating: true,
            snap: true,
            pinned: false,
            backgroundColor: const Color(0xFF0A0E0B),
            elevation: 0,
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white),
              onPressed: () => Navigator.pop(context),
            ),
            title: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF7B2FF7), Color(0xFF00D4FF)],
                    ),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.auto_awesome,
                      color: Colors.white, size: 18),
                ),
                const SizedBox(width: 10),
                Text(
                  'Stüdyo AI',
                  style: GoogleFonts.poppins(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 20,
                  ),
                ),
              ],
            ),
          ),

          // ---- Content ----
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Başlık bölümü
                  if (!_isLoading && !_isDone) ...[
                    _buildInfoBanner(),
                    const SizedBox(height: 24),
                  ],

                  // Karşılaştırma / durum paneli
                  _buildMainPanel(),

                  const SizedBox(height: 24),

                  // Sonuç gösterimi
                  if (_isDone) _buildResultSection(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoBanner() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF7B2FF7).withOpacity(0.15),
            const Color(0xFF00D4FF).withOpacity(0.10),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
            color: const Color(0xFF7B2FF7).withOpacity(0.4), width: 1),
      ),
      child: Row(
        children: [
          const Icon(Icons.auto_awesome, color: Color(0xFF00D4FF), size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'Ürününüz profesyonel stüdyo ortamına '
              'taşınacak: mermer tezgah, ahşap arka plan '
              've stüdyo ışıklandırması.',
              style: GoogleFonts.poppins(
                color: Colors.grey[300],
                fontSize: 13,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMainPanel() {
    return AspectRatio(
      aspectRatio: 1,
      child: Stack(
        fit: StackFit.expand,
        children: [
          // Orijinal görsel (arka planda / karşılaştırma için)
          if (_isDone)
            _buildOriginalImage()
          else
            _buildOriginalImage(),

          // Yükleniyor
          if (_isLoading) _buildLoadingOverlay(),

          // Hata
          if (!_isLoading && _errorMessage != null) _buildErrorWidget(),

          // Sonuç
          if (_isDone)
            FadeTransition(
              opacity: _fadeAnimation,
              child: _buildStudioImage(),
            ),

          // "Başarılı" rozet
          if (_isDone)
            Positioned(
              top: 12,
              right: 12,
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF7B2FF7), Color(0xFF00D4FF)],
                  ),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF7B2FF7).withOpacity(0.5),
                      blurRadius: 10,
                    ),
                  ],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.check_circle,
                        color: Colors.white, size: 14),
                    const SizedBox(width: 4),
                    Text(
                      'Stüdyo Hazır',
                      style: GoogleFonts.poppins(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildResultSection() {
    return Column(
      children: [
        // Başarı mesajı
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF151916),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: const Color(0xFF7B2FF7).withOpacity(0.4),
            ),
          ),
          child: Column(
            children: [
              const Icon(Icons.auto_awesome,
                  color: Color(0xFF00D4FF), size: 36),
              const SizedBox(height: 12),
              Text(
                '✨ Profesyonel Stüdyo Görseli Hazır!',
                textAlign: TextAlign.center,
                style: GoogleFonts.poppins(
                  color: Colors.white,
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Ürününüz mermer tezgah ve ahşap arka plan ile\n'
                'profesyonel stüdyo ortamına başarıyla taşındı.',
                textAlign: TextAlign.center,
                style: GoogleFonts.poppins(
                  color: Colors.grey[400],
                  fontSize: 13,
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // Tekrar dene butonu
        SizedBox(
          width: double.infinity,
          height: 54,
          child: OutlinedButton.icon(
            icon: const Icon(Icons.refresh, color: Color(0xFF7B2FF7)),
            label: Text(
              'Yeniden Oluştur',
              style: GoogleFonts.poppins(
                color: const Color(0xFF7B2FF7),
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            style: OutlinedButton.styleFrom(
              side: BorderSide(
                  color: const Color(0xFF7B2FF7).withOpacity(0.6), width: 1.5),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14)),
            ),
            onPressed: () {
              _fadeController.reset();
              _startStudioAI();
            },
          ),
        ),
        const SizedBox(height: 40),
      ],
    );
  }
}
