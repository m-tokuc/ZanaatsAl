import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';

class ResultScreen extends StatelessWidget {
  final Map<String, dynamic> data;
  final XFile imageFile;

  const ResultScreen({super.key, required this.data, required this.imageFile});

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

  Widget _buildGlassCard({
    required BuildContext context,
    required String title,
    required IconData icon,
    required Color iconColor,
    required Widget content,
    String? copyText,
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
    final exportStrategy = data['export_strategy'] ?? {};
    final suggestedTitle = exportStrategy['suggested_title'] ?? 'Belirtilmedi';
    final suggestedPrice = exportStrategy['suggested_price'] ?? 'Belirtilmedi';
    final marketingHook = exportStrategy['marketing_hook'] ?? 'Belirtilmedi';
    final competitorAnalysis = data['rakip_analizi'] ?? 'Belirtilmedi';

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
                      ? Image.network(imageFile.path, fit: BoxFit.cover)
                      : Image.file(File(imageFile.path), fit: BoxFit.cover),
                  // Gradient Overlay for readability
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
                  // Price Card
                  _buildGlassCard(
                    context: context,
                    title: 'Önerilen Satış Fiyatı',
                    icon: Icons.sell_outlined,
                    iconColor: const Color(0xFF4CAF50),
                    content: Text(
                      suggestedPrice,
                      style: GoogleFonts.poppins(
                        fontSize: 36,
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF4CAF50),
                      ),
                    ),
                  ),

                  // Title Card
                  _buildGlassCard(
                    context: context,
                    title: 'Optimize Edilmiş Başlık',
                    icon: Icons.title,
                    iconColor: Colors.blueAccent,
                    copyText: suggestedTitle,
                    content: Text(
                      suggestedTitle,
                      style: GoogleFonts.poppins(
                        fontSize: 16,
                        color: Colors.white,
                        height: 1.5,
                      ),
                    ),
                  ),

                  // Marketing Hook Card
                  _buildGlassCard(
                    context: context,
                    title: 'Pazarlama Metni & Hikaye',
                    icon: Icons.auto_awesome,
                    iconColor: Colors.purpleAccent,
                    copyText: marketingHook,
                    content: Text(
                      marketingHook,
                      style: GoogleFonts.poppins(
                        fontSize: 15,
                        color: Colors.grey[300],
                        height: 1.6,
                      ),
                    ),
                  ),

                  // Competitor Analysis Card
                  _buildGlassCard(
                    context: context,
                    title: 'Rakip ve Pazar Analizi',
                    icon: Icons.analytics_outlined,
                    iconColor: Colors.orangeAccent,
                    content: Text(
                      competitorAnalysis,
                      style: GoogleFonts.poppins(
                        fontSize: 15,
                        color: Colors.grey[300],
                        height: 1.6,
                      ),
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Yeni Ürün Analiz Et Butonu
                  Container(
                    width: double.infinity,
                    height: 60,
                    margin: const EdgeInsets.only(bottom: 40),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF1B5E20), Color(0xFF2E7D32)],
                      ),
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF1B5E20).withOpacity(0.4),
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
                          Navigator.popUntil(context, (route) => route.isFirst);
                        },
                        child: Center(
                          child: Text(
                            'Yeni Ürün Analiz Et',
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
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
