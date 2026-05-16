import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:google_fonts/google_fonts.dart';
import 'loading_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ImagePicker _picker = ImagePicker();
  final TextEditingController _descriptionController = TextEditingController();
  final TextEditingController _materialController = TextEditingController();
  String? _selectedCategory;
  XFile? _selectedImage;

  Future<void> _pickImage(ImageSource source) async {
    final XFile? image = await _picker.pickImage(source: source);
    if (image != null) {
      setState(() {
        _selectedImage = image;
      });
    }
  }

  void _startAnalysis() {
    if (_selectedImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Lütfen önce bir görsel seçin', style: GoogleFonts.poppins()),
          backgroundColor: Colors.redAccent,
        ),
      );
      return;
    }
    
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => LoadingScreen(
          imageFile: _selectedImage!,
          description: _descriptionController.text.trim(),
          category: _selectedCategory,
          material: _materialController.text.trim(),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    _materialController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E0B),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          'Yeni Analiz',
          style: GoogleFonts.poppins(
            fontSize: 20,
            fontWeight: FontWeight.w600,
            color: Colors.white,
          ),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Ürün Görseli',
                style: GoogleFonts.poppins(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                  color: Colors.grey[300],
                ),
              ),
              const SizedBox(height: 12),
              
              // Modern Upload Area
              GestureDetector(
                onTap: () {
                  showModalBottomSheet(
                    context: context,
                    backgroundColor: const Color(0xFF1A1A1A),
                    shape: const RoundedRectangleBorder(
                      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                    ),
                    builder: (context) => SafeArea(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          ListTile(
                            leading: const Icon(Icons.camera_alt, color: Colors.white),
                            title: Text('Kameradan Çek', style: GoogleFonts.poppins(color: Colors.white)),
                            onTap: () {
                              Navigator.pop(context);
                              _pickImage(ImageSource.camera);
                            },
                          ),
                          ListTile(
                            leading: const Icon(Icons.photo_library, color: Colors.white),
                            title: Text('Galeriden Seç', style: GoogleFonts.poppins(color: Colors.white)),
                            onTap: () {
                              Navigator.pop(context);
                              _pickImage(ImageSource.gallery);
                            },
                          ),
                        ],
                      ),
                    ),
                  );
                },
                child: Container(
                  width: double.infinity,
                  height: 220,
                  decoration: BoxDecoration(
                    color: const Color(0xFF151916),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(
                      color: _selectedImage != null ? const Color(0xFF4CAF50) : const Color(0xFF2E332F),
                      width: 2,
                    ),
                  ),
                  child: _selectedImage != null
                      ? ClipRRect(
                          borderRadius: BorderRadius.circular(22),
                          child: kIsWeb
                              ? Image.network(_selectedImage!.path, fit: BoxFit.cover)
                              : Image.file(File(_selectedImage!.path), fit: BoxFit.cover),
                        )
                      : Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: const Color(0xFF1B5E20).withOpacity(0.2),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.cloud_upload_outlined, size: 40, color: Color(0xFF4CAF50)),
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'Görsel Yüklemek İçin Dokunun',
                              style: GoogleFonts.poppins(
                                fontSize: 14,
                                color: Colors.grey[400],
                              ),
                            ),
                          ],
                        ),
                ),
              ),
              
              const SizedBox(height: 32),
              
              // Kategori Seçimi
              Text(
                'Ürün Kategorisi',
                style: GoogleFonts.poppins(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                  color: Colors.grey[300],
                ),
              ),
              const SizedBox(height: 12),
              Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF151916),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF2E332F)),
                ),
                child: DropdownButtonFormField<String>(
                  value: _selectedCategory,
                  dropdownColor: const Color(0xFF1A1A1A),
                  style: GoogleFonts.poppins(color: Colors.white, fontSize: 14),
                  decoration: const InputDecoration(
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  ),
                  hint: Text('Kategori Seçin', style: GoogleFonts.poppins(color: Colors.grey[600], fontSize: 14)),
                  items: ['Çanta & Cüzdan', 'Giyim', 'Takı & Aksesuar', 'Ev Dekorasyonu', 'Sanat & Tablo']
                      .map((String value) {
                    return DropdownMenuItem<String>(
                      value: value,
                      child: Text(value),
                    );
                  }).toList(),
                  onChanged: (newValue) {
                    setState(() {
                      _selectedCategory = newValue;
                    });
                  },
                ),
              ),

              const SizedBox(height: 24),
              
              // Ana Materyal
              Text(
                'Ana Materyal / Malzeme',
                style: GoogleFonts.poppins(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                  color: Colors.grey[300],
                ),
              ),
              const SizedBox(height: 12),
              Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF151916),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF2E332F)),
                ),
                child: TextField(
                  controller: _materialController,
                  style: GoogleFonts.poppins(color: Colors.white, fontSize: 14),
                  decoration: InputDecoration(
                    hintText: 'Örn: Hakiki Deri, Pamuk, Epoksi, Ahşap...',
                    hintStyle: GoogleFonts.poppins(color: Colors.grey[600], fontSize: 14),
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  ),
                ),
              ),

              const SizedBox(height: 24),
              
              Text(
                'Ürün Hikayesi ve Detayları (Opsiyonel)',
                style: GoogleFonts.poppins(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                  color: Colors.grey[300],
                ),
              ),
              const SizedBox(height: 12),
              
              // Description Input
              Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF151916),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF2E332F)),
                ),
                child: TextField(
                  controller: _descriptionController,
                  maxLines: 4,
                  style: GoogleFonts.poppins(color: Colors.white, fontSize: 14),
                  decoration: InputDecoration(
                    hintText: "Örn: 1980'lerden esinlenilmiş, tamamen el dikişi, sürdürülebilir malzemelerle üretilmiş minimalist cüzdan...",
                    hintStyle: GoogleFonts.poppins(color: Colors.grey[600], fontSize: 14),
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.all(16),
                  ),
                ),
              ),
              
              const SizedBox(height: 40),
              
              // CTA Button
              Container(
                width: double.infinity,
                height: 60,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: _selectedImage != null
                        ? [const Color(0xFF1B5E20), const Color(0xFF2E7D32)]
                        : [const Color(0xFF2E332F), const Color(0xFF2E332F)],
                  ),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: _selectedImage != null
                      ? [
                          BoxShadow(
                            color: const Color(0xFF1B5E20).withOpacity(0.4),
                            blurRadius: 15,
                            offset: const Offset(0, 8),
                          )
                        ]
                      : null,
                ),
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    borderRadius: BorderRadius.circular(16),
                    onTap: _startAnalysis,
                    child: Center(
                      child: Text(
                        'Analiz Et',
                        style: GoogleFonts.poppins(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                          color: _selectedImage != null ? Colors.white : Colors.grey[600],
                          letterSpacing: 1,
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
    );
  }
}
