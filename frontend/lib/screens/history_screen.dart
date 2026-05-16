import 'dart:io';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:image_picker/image_picker.dart';
import 'result_screen.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<Map<String, dynamic>> _savedProducts = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final savedList = prefs.getStringList('saved_products') ?? [];
    
    setState(() {
      _savedProducts = savedList.map((item) => jsonDecode(item) as Map<String, dynamic>).toList();
      // En yeni eklenen en üstte
      _savedProducts.sort((a, b) => DateTime.parse(b['date']).compareTo(DateTime.parse(a['date'])));
      _isLoading = false;
    });
  }

  Future<void> _clearHistory() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('saved_products');
    setState(() {
      _savedProducts = [];
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
          'Koleksiyonum',
          style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.w600),
        ),
        actions: [
          if (_savedProducts.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
              onPressed: () {
                showDialog(
                  context: context,
                  builder: (context) => AlertDialog(
                    backgroundColor: const Color(0xFF151916),
                    title: Text('Koleksiyonu Temizle', style: GoogleFonts.poppins(color: Colors.white)),
                    content: Text('Tüm kaydedilmiş ürün analizleri silinecek. Emin misiniz?', style: GoogleFonts.poppins(color: Colors.grey[300])),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: Text('İptal', style: GoogleFonts.poppins(color: Colors.grey)),
                      ),
                      TextButton(
                        onPressed: () {
                          Navigator.pop(context);
                          _clearHistory();
                        },
                        child: Text('Sil', style: GoogleFonts.poppins(color: Colors.redAccent)),
                      ),
                    ],
                  ),
                );
              },
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF4CAF50)))
          : _savedProducts.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.inventory_2_outlined, size: 80, color: Colors.grey[800]),
                      const SizedBox(height: 16),
                      Text(
                        'Henüz hiç ürün kaydetmediniz.',
                        style: GoogleFonts.poppins(color: Colors.grey[500], fontSize: 16),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _savedProducts.length,
                  itemBuilder: (context, index) {
                    final item = _savedProducts[index];
                    final date = DateTime.parse(item['date']);
                    final formattedDate = '${date.day}/${date.month}/${date.year}';
                    
                    String title = 'Belirtilmedi';
                    if (item['data'] != null && item['data']['export_strategy'] != null && item['data']['export_strategy']['urun_pozisyonlandirma'] != null) {
                       title = item['data']['export_strategy']['urun_pozisyonlandirma']['benzersiz_deger_oneri'] ?? 'Kaydedilmiş Ürün';
                    }

                    return Card(
                      color: const Color(0xFF151916),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      margin: const EdgeInsets.only(bottom: 16),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(16),
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => ResultScreen(
                                data: item['data'],
                                imageFile: XFile(item['image_path']),
                              ),
                            ),
                          );
                        },
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Row(
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(12),
                                child: SizedBox(
                                  width: 80,
                                  height: 80,
                                  child: kIsWeb
                                      ? Image.network(item['image_path'], fit: BoxFit.cover)
                                      : Image.file(File(item['image_path']), fit: BoxFit.cover),
                                ),
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      title,
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                      style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14),
                                    ),
                                    const SizedBox(height: 8),
                                    Text(
                                      formattedDate,
                                      style: GoogleFonts.poppins(color: Colors.grey[500], fontSize: 12),
                                    ),
                                  ],
                                ),
                              ),
                              const Icon(Icons.chevron_right, color: Colors.grey),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
