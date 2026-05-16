import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:google_fonts/google_fonts.dart';

class PhotoEnhancementScreen extends StatefulWidget {
  final XFile imageFile;

  const PhotoEnhancementScreen({super.key, required this.imageFile});

  @override
  State<PhotoEnhancementScreen> createState() => _PhotoEnhancementScreenState();
}

class _PhotoEnhancementScreenState extends State<PhotoEnhancementScreen> {
  int _selectedStyleIndex = -1;
  bool _isProcessing = false;
  bool _isDone = false;

  final List<Map<String, dynamic>> _styles = [
    {
      'title': 'Stüdyo Beyazı',
      'icon': Icons.crop_original,
      'desc': 'E-ticaret platformları için saf beyaz arka plan',
      'color': Colors.white,
    },
    {
      'title': 'Minimalist Ahşap',
      'icon': Icons.table_restaurant,
      'desc': 'Sıcak ve doğal ahşap dokulu zemin',
      'color': Colors.brown[300],
    },
    {
      'title': 'Doğa Konsepti',
      'icon': Icons.eco,
      'desc': 'Soft yeşillik ve gün ışığı gölgeleri',
      'color': Colors.green[200],
    },
    {
      'title': 'Karanlık Premium',
      'icon': Icons.nightlight_round,
      'desc': 'Lüks hissiyatı veren koyu ve dramatik ışık',
      'color': Colors.grey[900],
    },
  ];

  Future<void> _processImage() async {
    if (_selectedStyleIndex == -1) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Lütfen bir arka plan stili seçin!')),
      );
      return;
    }

    setState(() {
      _isProcessing = true;
    });

    // Mock processing delay
    await Future.delayed(const Duration(seconds: 3));

    setState(() {
      _isProcessing = false;
      _isDone = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E0B),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'AI Fotoğraf Stüdyosu',
          style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.w600),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // İpucu Kartı
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF1B5E20).withOpacity(0.2),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF1B5E20).withOpacity(0.5)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.lightbulb, color: Colors.yellowAccent, size: 24),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'İpucu: Fotoğraflarınızı her zaman doğal gün ışığında çekin. Ürününüzün dokusunu göstermek için yakın (makro) çekimler yapmayı unutmayın.',
                      style: GoogleFonts.poppins(color: Colors.grey[300], fontSize: 13, height: 1.5),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 30),

            // Görsel
            Center(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: Stack(
                  children: [
                    Container(
                      width: 250,
                      height: 250,
                      decoration: BoxDecoration(
                        color: _isDone ? _styles[_selectedStyleIndex]['color'] : Colors.transparent,
                      ),
                      child: kIsWeb
                          ? Image.network(widget.imageFile.path, fit: BoxFit.contain)
                          : Image.file(File(widget.imageFile.path), fit: BoxFit.contain),
                    ),
                    if (_isProcessing)
                      Container(
                        width: 250,
                        height: 250,
                        color: Colors.black.withOpacity(0.6),
                        child: const Center(
                          child: CircularProgressIndicator(color: Colors.purpleAccent),
                        ),
                      ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 30),

            Text(
              'Arka Plan Stili Seçin',
              style: GoogleFonts.poppins(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 16),

            // Grid of styles
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 1.2,
              ),
              itemCount: _styles.length,
              itemBuilder: (context, index) {
                final isSelected = _selectedStyleIndex == index;
                final style = _styles[index];

                return GestureDetector(
                  onTap: () {
                    if (!_isProcessing && !_isDone) {
                      setState(() {
                        _selectedStyleIndex = index;
                      });
                    }
                  },
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isSelected ? const Color(0xFF6A1B9A).withOpacity(0.3) : const Color(0xFF151916),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: isSelected ? Colors.purpleAccent : const Color(0xFF2E332F),
                        width: isSelected ? 2 : 1,
                      ),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(style['icon'], color: isSelected ? Colors.purpleAccent : Colors.grey, size: 32),
                        const SizedBox(height: 8),
                        Text(
                          style['title'],
                          textAlign: TextAlign.center,
                          style: GoogleFonts.poppins(
                            color: isSelected ? Colors.white : Colors.grey[400],
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),

            const SizedBox(height: 30),

            // İşle Button
            if (!_isDone)
              SizedBox(
                width: double.infinity,
                height: 55,
                child: ElevatedButton(
                  onPressed: _isProcessing ? null : _processImage,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF6A1B9A),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  child: _isProcessing
                      ? Text('Yapay Zeka İşliyor...', style: GoogleFonts.poppins(color: Colors.white, fontSize: 16))
                      : Text('Uygula', style: GoogleFonts.poppins(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
                ),
              ),

            if (_isDone)
              Column(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.green.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.check_circle, color: Colors.greenAccent),
                        const SizedBox(width: 8),
                        Text('Fotoğraf Başarıyla İyileştirildi!', style: GoogleFonts.poppins(color: Colors.greenAccent)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    height: 55,
                    child: OutlinedButton(
                      onPressed: () {
                        setState(() {
                          _isDone = false;
                          _selectedStyleIndex = -1;
                        });
                      },
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Colors.purpleAccent),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                      child: Text('Farklı Bir Stil Dene', style: GoogleFonts.poppins(color: Colors.purpleAccent, fontSize: 16)),
                    ),
                  ),
                ],
              ),
              
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }
}
