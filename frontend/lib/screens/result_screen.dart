import 'dart:io';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'photo_enhancement_screen.dart';
import 'studio_screen.dart';

class ResultScreen extends StatefulWidget {
  final Map<String, dynamic> data;
  final XFile imageFile;

  const ResultScreen({super.key, required this.data, required this.imageFile});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  bool _showEnglishDescription = false;
  bool _isSaving = false;

  void _copyToClipboard(BuildContext context, String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Kopyalandı!', style: GoogleFonts.poppins()),
        backgroundColor: const Color(0xFF1B5E20),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  Future<void> _saveProduct() async {
    setState(() => _isSaving = true);
    try {
      final prefs = await SharedPreferences.getInstance();
      final savedList = prefs.getStringList('saved_products') ?? [];
      
      final productData = {
        'image_path': widget.imageFile.path,
        'date': DateTime.now().toIso8601String(),
        'data': widget.data,
      };
      
      savedList.add(jsonEncode(productData));
      await prefs.setStringList('saved_products', savedList);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
           SnackBar(
            content: Text('Ürün başarıyla koleksiyona kaydedildi!', style: GoogleFonts.poppins()),
            backgroundColor: const Color(0xFF1B5E20),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
           SnackBar(content: Text('Kaydetme hatası: $e')),
        );
      }
    } finally {
      setState(() => _isSaving = false);
    }
  }

  String getDeepValue(Map map, List<String> keys, [String defaultValue = 'Belirtilmedi']) {
    dynamic current = map;
    for (var key in keys) {
      if (current is Map && current.containsKey(key)) {
        current = current[key];
      } else {
        return defaultValue;
      }
    }
    if (current is List) return current.join(', ');
    return current?.toString() ?? defaultValue;
  }

  Widget _buildGlassCard({
    required String title,
    required IconData icon,
    required Color iconColor,
    required Widget content,
    String? copyText,
    Widget? trailingAction,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 24),
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF151916), // Dark premium card background
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFF2E332F), width: 1),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.4),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: iconColor.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: iconColor, size: 24),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Text(
                  title,
                  style: GoogleFonts.poppins(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                  ),
                ),
              ),
              if (trailingAction != null) trailingAction,
              if (copyText != null)
                IconButton(
                  icon: const Icon(Icons.copy, color: Colors.grey, size: 20),
                  onPressed: () => _copyToClipboard(context, copyText),
                  tooltip: 'Kopyala',
                ),
            ],
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 16.0),
            child: Divider(color: Color(0xFF2E332F), height: 1),
          ),
          content,
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final exportStrategy = widget.data['export_strategy'] ?? {};
    
    // Fiyatlar
    final trFiyat = getDeepValue(exportStrategy, ['fiyatlandirma_stratejisi', 'tr_fiyat_tl']);
    final globalFiyat = getDeepValue(exportStrategy, ['fiyatlandirma_stratejisi', 'global_fiyat_usd']);
    
    // Açıklamalar
    final aciklamaTr = getDeepValue(exportStrategy, ['pazarlama_ve_icerik', 'urun_aciklamasi_tr']);
    final aciklamaEn = getDeepValue(exportStrategy, ['pazarlama_ve_icerik', 'urun_aciklamasi_en']);
    final currentAciklama = _showEnglishDescription ? aciklamaEn : aciklamaTr;
    
    // Pazar ve SEO
    final trPlatformlar = getDeepValue(exportStrategy, ['pazar_ve_seo', 'tr_stratejisi', 'platformlar']);
    final trSeo = getDeepValue(exportStrategy, ['pazar_ve_seo', 'tr_stratejisi', 'seo_kelimeleri']);
    final globalPlatformlar = getDeepValue(exportStrategy, ['pazar_ve_seo', 'global_strateji', 'platformlar']);
    final globalSeo = getDeepValue(exportStrategy, ['pazar_ve_seo', 'global_strateji', 'seo_kelimeleri']);

    return Scaffold(
      backgroundColor: const Color(0xFF0A0E0B),
      body: CustomScrollView(
        slivers: [
          // AppBar & Image Header
          SliverAppBar(
            expandedHeight: 300.0,
            floating: false,
            pinned: true,
            backgroundColor: const Color(0xFF0A0E0B),
            elevation: 0,
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white),
              onPressed: () => Navigator.pop(context),
            ),
            flexibleSpace: FlexibleSpaceBar(
              background: Stack(
                fit: StackFit.expand,
                children: [
                  kIsWeb
                      ? Image.network(widget.imageFile.path, fit: BoxFit.cover)
                      : Image.file(File(widget.imageFile.path), fit: BoxFit.cover),
                  Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.transparent,
                          const Color(0xFF0A0E0B).withOpacity(0.8),
                          const Color(0xFF0A0E0B),
                        ],
                        stops: const [0.4, 0.8, 1.0],
                      ),
                    ),
                  ),
                  Positioned(
                    bottom: 20,
                    left: 20,
                    right: 20,
                    child: Text(
                      'Analiz Sonucu',
                      style: GoogleFonts.poppins(
                        fontSize: 32,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Content
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Dual Market Price Card
                  _buildGlassCard(
                    title: 'Önerilen Satış Fiyatları',
                    icon: Icons.sell_outlined,
                    iconColor: const Color(0xFF4CAF50),
                    content: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('🇹🇷 Türkiye Pazarı', style: GoogleFonts.poppins(color: Colors.grey[400], fontSize: 13)),
                              const SizedBox(height: 4),
                              Text(
                                trFiyat,
                                style: GoogleFonts.poppins(
                                  fontSize: 22,
                                  fontWeight: FontWeight.bold,
                                  color: const Color(0xFF4CAF50),
                                ),
                              ),
                            ],
                          ),
                        ),
                        Container(width: 1, height: 50, color: const Color(0xFF2E332F)),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('🌍 Global Pazar', style: GoogleFonts.poppins(color: Colors.grey[400], fontSize: 13)),
                              const SizedBox(height: 4),
                              Text(
                                globalFiyat,
                                style: GoogleFonts.poppins(
                                  fontSize: 22,
                                  fontWeight: FontWeight.bold,
                                  color: const Color(0xFF81C784),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),

                  // Bilingual Description Card
                  _buildGlassCard(
                    title: 'Satış Açıklaması',
                    icon: Icons.description_outlined,
                    iconColor: Colors.purpleAccent,
                    copyText: currentAciklama,
                    trailingAction: TextButton.icon(
                      icon: const Icon(Icons.g_translate, size: 18, color: Colors.white),
                      label: Text(_showEnglishDescription ? 'TR' : 'EN', style: GoogleFonts.poppins(color: Colors.white)),
                      style: TextButton.styleFrom(
                        backgroundColor: Colors.purpleAccent.withOpacity(0.2),
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: () {
                        setState(() {
                          _showEnglishDescription = !_showEnglishDescription;
                        });
                      },
                    ),
                    content: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 300),
                      child: Text(
                        currentAciklama,
                        key: ValueKey<bool>(_showEnglishDescription),
                        style: GoogleFonts.poppins(
                          fontSize: 15,
                          color: Colors.grey[300],
                          height: 1.6,
                        ),
                      ),
                    ),
                  ),

                  // TR Strategy
                  _buildGlassCard(
                    title: '🇹🇷 Türkiye Pazar Stratejisi',
                    icon: Icons.trending_up,
                    iconColor: Colors.orangeAccent,
                    content: RichText(
                      text: TextSpan(
                        style: GoogleFonts.poppins(fontSize: 14, color: Colors.grey[300], height: 1.6),
                        children: [
                          const TextSpan(text: 'Platformlar: ', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                          TextSpan(text: '$trPlatformlar\n\n'),
                          const TextSpan(text: 'SEO Kelimeleri: ', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                          TextSpan(text: trSeo),
                        ],
                      ),
                    ),
                  ),

                  // Global Strategy
                  _buildGlassCard(
                    title: '🌍 Global Pazar Stratejisi',
                    icon: Icons.public,
                    iconColor: Colors.blueAccent,
                    content: RichText(
                      text: TextSpan(
                        style: GoogleFonts.poppins(fontSize: 14, color: Colors.grey[300], height: 1.6),
                        children: [
                          const TextSpan(text: 'Platformlar: ', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                          TextSpan(text: '$globalPlatformlar\n\n'),
                          const TextSpan(text: 'SEO Kelimeleri: ', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                          TextSpan(text: globalSeo),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 10),

                  // Save Product Button
                  Container(
                    width: double.infinity,
                    height: 55,
                    margin: const EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      color: const Color(0xFF151916),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFF4CAF50).withOpacity(0.5)),
                    ),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(16),
                        onTap: _isSaving ? null : _saveProduct,
                        child: Center(
                          child: _isSaving
                              ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF4CAF50)))
                              : Text(
                                  '💾 Ürünü Koleksiyona Kaydet',
                                  style: GoogleFonts.poppins(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                    color: const Color(0xFF4CAF50),
                                  ),
                                ),
                        ),
                      ),
                    ),
                  ),

                  // AI Photo Enhancement Button
                  Container(
                    width: double.infinity,
                    height: 60,
                    margin: const EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF6A1B9A), Color(0xFF8E24AA)],
                      ),
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF6A1B9A).withOpacity(0.4),
                          blurRadius: 15,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(16),
                        onTap: () {
                           Navigator.push(
                             context,
                             MaterialPageRoute(
                               builder: (context) => PhotoEnhancementScreen(imageFile: widget.imageFile),
                             ),
                           );
                        },
                        child: Center(
                          child: Text(
                            '✨ AI Fotoğraf İyileştirme',
                            style: GoogleFonts.poppins(
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                              color: Colors.white,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),

                  // ── Stüdyo AI Butonu ──────────────────────────────────
                  Container(
                    width: double.infinity,
                    height: 65,
                    margin: const EdgeInsets.only(bottom: 40),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [Color(0xFF1A0533), Color(0xFF2D0B6B)],
                      ),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(
                        color: const Color(0xFF7B2FF7).withOpacity(0.6),
                        width: 1.5,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF7B2FF7).withOpacity(0.35),
                          blurRadius: 20,
                          spreadRadius: 0,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(18),
                        splashColor: const Color(0xFF7B2FF7).withOpacity(0.3),
                        onTap: () {
                          Navigator.push(
                            context,
                            PageRouteBuilder(
                              pageBuilder: (_, animation, __) =>
                                  StudioAIScreen(imageFile: widget.imageFile),
                              transitionsBuilder:
                                  (_, animation, __, child) {
                                return FadeTransition(
                                  opacity: animation,
                                  child: child,
                                );
                              },
                              transitionDuration:
                                  const Duration(milliseconds: 400),
                            ),
                          );
                        },
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 20),
                          child: Row(
                            children: [
                              // İkon kutusu
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  gradient: const LinearGradient(
                                    colors: [
                                      Color(0xFF7B2FF7),
                                      Color(0xFF00D4FF)
                                    ],
                                  ),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: const Icon(
                                  Icons.auto_awesome,
                                  color: Colors.white,
                                  size: 22,
                                ),
                              ),
                              const SizedBox(width: 14),
                              // Metin
                              Expanded(
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  crossAxisAlignment:
                                      CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Stüdyo AI',
                                      style: GoogleFonts.poppins(
                                        fontSize: 17,
                                        fontWeight: FontWeight.w700,
                                        color: Colors.white,
                                        letterSpacing: 0.3,
                                      ),
                                    ),
                                    Text(
                                      'Profesyonel stüdyo ortamına taşı',
                                      style: GoogleFonts.poppins(
                                        fontSize: 11,
                                        color: const Color(0xFF00D4FF),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const Icon(
                                Icons.arrow_forward_ios,
                                color: Color(0xFF7B2FF7),
                                size: 16,
                              ),
                            ],
                          ),
                        ),
                      ),
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
}
