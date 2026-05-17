import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';

import '../services/api_service.dart';

// ---------------------------------------------------------------------------
// Şablon Modeli
// ---------------------------------------------------------------------------

class _StudioTemplate {
  final String id;
  final String title;
  final IconData icon;
  final Color primaryColor;
  final Color secondaryColor;
  final String description;

  const _StudioTemplate({
    required this.id,
    required this.title,
    required this.icon,
    required this.primaryColor,
    required this.secondaryColor,
    required this.description,
  });
}

const List<_StudioTemplate> _kTemplates = [
  _StudioTemplate(
    id: 'studio_white',
    title: 'Stüdyo Beyazı',
    icon: Icons.crop_original,
    primaryColor: Color(0xFFF5F5F5),
    secondaryColor: Color(0xFFE0E0E0),
    description: 'Saf beyaz, e-ticaret uyumlu',
  ),
  _StudioTemplate(
    id: 'rustic_wood',
    title: 'Kırsal Ahşap',
    icon: Icons.table_restaurant,
    primaryColor: Color(0xFF8D6E4C),
    secondaryColor: Color(0xFF5D4037),
    description: 'Sıcak ahşap doku & altın ışık',
  ),
  _StudioTemplate(
    id: 'minimal_marble',
    title: 'Minimalist Mermer',
    icon: Icons.dashboard_rounded,
    primaryColor: Color(0xFFECE9E4),
    secondaryColor: Color(0xFFC8C2B8),
    description: 'Lüks Carrara mermer yüzey',
  ),
  _StudioTemplate(
    id: 'modern_concrete',
    title: 'Endüstriyel Beton',
    icon: Icons.apartment,
    primaryColor: Color(0xFF616161),
    secondaryColor: Color(0xFF424242),
    description: 'Koyu beton & dramatik ışık',
  ),
  _StudioTemplate(
    id: 'nature_leaves',
    title: 'Doğa & Yapraklar',
    icon: Icons.eco,
    primaryColor: Color(0xFF66BB6A),
    secondaryColor: Color(0xFF2E7D32),
    description: 'Tropikal yeşillik & güneş ışığı',
  ),
  _StudioTemplate(
    id: 'premium_black',
    title: 'Gece Siyahı',
    icon: Icons.nightlight_round,
    primaryColor: Color(0xFF212121),
    secondaryColor: Color(0xFF000000),
    description: 'Mat siyah & yüksek kontrast',
  ),
];

// ---------------------------------------------------------------------------
// StudioAIScreen
// ---------------------------------------------------------------------------

class StudioAIScreen extends StatefulWidget {
  final XFile imageFile;

  const StudioAIScreen({super.key, required this.imageFile});

  @override
  State<StudioAIScreen> createState() => _StudioAIScreenState();
}

class _StudioAIScreenState extends State<StudioAIScreen>
    with TickerProviderStateMixin {
  // ── State ──────────────────────────────────────────────────────────────
  int _selectedIndex = -1;         // Henüz şablon seçilmedi
  bool _isLoading = false;
  bool _isDone = false;
  String? _errorMessage;
  String? _studioImageBase64;

  late final AnimationController _pulseController;
  late final Animation<double> _pulseAnimation;

  late final AnimationController _fadeController;
  late final Animation<double> _fadeAnimation;

  // Loading mesajları
  final List<String> _loadingMessages = [
    '🔬 Ürün analiz ediliyor...',
    '✂️ Arka plan kaldırılıyor...',
    '🎨 Arka plan hazırlanıyor...',
    '💡 Stüdyo ışıklandırması ayarlanıyor...',
    '🖼️ Ortam oluşturuluyor...',
    '✨ Son rötuşlar yapılıyor...',
  ];
  int _loadingMsgIndex = 0;

  @override
  void initState() {
    super.initState();

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 0.85, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _fadeAnimation = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeIn,
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _fadeController.dispose();
    super.dispose();
  }

  // ── İş Mantığı ────────────────────────────────────────────────────────

  Future<void> _startStudioAI(String backgroundType) async {
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
      final result = await ApiService.generateStudioImage(
        widget.imageFile,
        backgroundType: backgroundType,
      );
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

  // ── UI Builders ───────────────────────────────────────────────────────

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
        color: Colors.black.withValues(alpha: 0.88),
        borderRadius: BorderRadius.circular(20),
      ),
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          ScaleTransition(
            scale: _pulseAnimation,
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const SweepGradient(colors: [
                  Color(0xFF7B2FF7),
                  Color(0xFF00D4FF),
                  Color(0xFF7B2FF7),
                ]),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF7B2FF7).withValues(alpha: 0.5),
                    blurRadius: 30,
                    spreadRadius: 4,
                  ),
                ],
              ),
              child: const Icon(Icons.auto_awesome, color: Colors.white, size: 48),
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
              style: GoogleFonts.poppins(color: const Color(0xFF00D4FF), fontSize: 13),
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
        color: Colors.red.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.red.withValues(alpha: 0.4)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, color: Colors.redAccent, size: 48),
          const SizedBox(height: 16),
          Text(
            'Bir Hata Oluştu',
            style: GoogleFonts.poppins(
              color: Colors.white, fontSize: 18, fontWeight: FontWeight.w600,
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
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: _selectedIndex >= 0
                ? () => _startStudioAI(_kTemplates[_selectedIndex].id)
                : null,
          ),
        ],
      ),
    );
  }

  // ── Şablon Grid Kutucuğu ──────────────────────────────────────────────

  Widget _buildTemplateCard(int index) {
    final t = _kTemplates[index];
    final isSelected = _selectedIndex == index;
    final bool isDark = t.primaryColor.computeLuminance() < 0.35;

    return GestureDetector(
      onTap: (_isLoading || _isDone)
          ? null
          : () => setState(() => _selectedIndex = index),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              t.primaryColor,
              t.secondaryColor,
            ],
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? const Color(0xFF7B2FF7) : Colors.transparent,
            width: isSelected ? 2.5 : 0,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: const Color(0xFF7B2FF7).withValues(alpha: 0.45),
                    blurRadius: 14,
                    spreadRadius: 1,
                  ),
                ]
              : [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.25),
                    blurRadius: 6,
                    offset: const Offset(0, 3),
                  ),
                ],
        ),
        child: Stack(
          children: [
            // İçerik
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    t.icon,
                    color: isDark ? Colors.white70 : Colors.black54,
                    size: 28,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    t.title,
                    textAlign: TextAlign.center,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: GoogleFonts.poppins(
                      color: isDark ? Colors.white : Colors.black87,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    t.description,
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: GoogleFonts.poppins(
                      color: isDark
                          ? Colors.white.withValues(alpha: 0.65)
                          : Colors.black54,
                      fontSize: 9,
                      height: 1.3,
                    ),
                  ),
                ],
              ),
            ),
            // Seçim rozeti
            if (isSelected)
              Positioned(
                top: 6,
                right: 6,
                child: Container(
                  padding: const EdgeInsets.all(3),
                  decoration: const BoxDecoration(
                    color: Color(0xFF7B2FF7),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.check, color: Colors.white, size: 14),
                ),
              ),
          ],
        ),
      ),
    );
  }

  // ── Build ─────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E0B),
      body: CustomScrollView(
        slivers: [
          // ── AppBar ──
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
                  child: const Icon(Icons.auto_awesome, color: Colors.white, size: 18),
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

          // ── Content ──
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Ürün Görseli / Sonuç Paneli
                  _buildMainPanel(),

                  const SizedBox(height: 24),

                  // ── Şablon Seçim Paneli (İşlem sırasında / sonrasında gizli) ──
                  if (!_isLoading && !_isDone) ...[
                    _buildInfoBanner(),
                    const SizedBox(height: 20),

                    // Başlık
                    Text(
                      'Arka Plan Teması Seçin',
                      style: GoogleFonts.poppins(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 14),

                    // 3×2 Grid
                    GridView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 3,
                        crossAxisSpacing: 10,
                        mainAxisSpacing: 10,
                        childAspectRatio: 0.95,
                      ),
                      itemCount: _kTemplates.length,
                      itemBuilder: (_, i) => _buildTemplateCard(i),
                    ),

                    const SizedBox(height: 24),

                    // ── Uygula Butonu ──
                    SizedBox(
                      width: double.infinity,
                      height: 58,
                      child: ElevatedButton(
                        onPressed: _selectedIndex >= 0
                            ? () => _startStudioAI(_kTemplates[_selectedIndex].id)
                            : null,
                        style: ElevatedButton.styleFrom(
                          padding: EdgeInsets.zero,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                          disabledBackgroundColor: const Color(0xFF2E332F),
                          elevation: 0,
                        ).copyWith(
                          backgroundColor: WidgetStateProperty.resolveWith(
                            (states) {
                              if (states.contains(WidgetState.disabled)) {
                                return const Color(0xFF2E332F);
                              }
                              return null; // Use Ink decoration below
                            },
                          ),
                        ),
                        child: Ink(
                          decoration: BoxDecoration(
                            gradient: _selectedIndex >= 0
                                ? const LinearGradient(
                                    colors: [Color(0xFF7B2FF7), Color(0xFF00D4FF)],
                                  )
                                : null,
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Center(
                            child: Text(
                              _selectedIndex >= 0
                                  ? '✨ ${_kTemplates[_selectedIndex].title} — Uygula'
                                  : 'Bir Tema Seçin',
                              style: GoogleFonts.poppins(
                                color: _selectedIndex >= 0
                                    ? Colors.white
                                    : Colors.grey[600],
                                fontSize: 16,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),

                    const SizedBox(height: 30),
                  ],

                  // ── Sonuç bölümü ──
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
        gradient: LinearGradient(colors: [
          const Color(0xFF7B2FF7).withValues(alpha: 0.15),
          const Color(0xFF00D4FF).withValues(alpha: 0.10),
        ]),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0xFF7B2FF7).withValues(alpha: 0.4),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          const Icon(Icons.auto_awesome, color: Color(0xFF00D4FF), size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'Ürününüze profesyonel bir arka plan ekleyin. '
              'Aşağıdan bir tema seçip "Uygula" butonuna basın.',
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
          _buildOriginalImage(),

          if (_isLoading) _buildLoadingOverlay(),

          if (!_isLoading && _errorMessage != null) _buildErrorWidget(),

          if (_isDone)
            FadeTransition(opacity: _fadeAnimation, child: _buildStudioImage()),

          if (_isDone)
            Positioned(
              top: 12,
              right: 12,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF7B2FF7), Color(0xFF00D4FF)],
                  ),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF7B2FF7).withValues(alpha: 0.5),
                      blurRadius: 10,
                    ),
                  ],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.check_circle, color: Colors.white, size: 14),
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
              color: const Color(0xFF7B2FF7).withValues(alpha: 0.4),
            ),
          ),
          child: Column(
            children: [
              const Icon(Icons.auto_awesome, color: Color(0xFF00D4FF), size: 36),
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
                'Ürününüz "${_selectedIndex >= 0 ? _kTemplates[_selectedIndex].title : ''}" '
                'temasıyla\nprofesyonel stüdyo ortamına başarıyla taşındı.',
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

        // Farklı bir tema dene
        SizedBox(
          width: double.infinity,
          height: 54,
          child: OutlinedButton.icon(
            icon: const Icon(Icons.palette_outlined, color: Color(0xFF7B2FF7)),
            label: Text(
              'Farklı Tema ile Dene',
              style: GoogleFonts.poppins(
                color: const Color(0xFF7B2FF7),
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            style: OutlinedButton.styleFrom(
              side: BorderSide(
                color: const Color(0xFF7B2FF7).withValues(alpha: 0.6),
                width: 1.5,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
              ),
            ),
            onPressed: () {
              _fadeController.reset();
              setState(() {
                _isDone = false;
                _studioImageBase64 = null;
                _errorMessage = null;
                _selectedIndex = -1;
              });
            },
          ),
        ),
        const SizedBox(height: 40),
      ],
    );
  }
}
