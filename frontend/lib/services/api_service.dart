import 'dart:convert';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

class ApiService {
  // Muhammet'in gönderdiği gerçek Ngrok linki
  static const String apiUrl =
      'https://contemptibly-septemviral-apollo.ngrok-free.dev/analyze';

  static Future<Map<String, dynamic>> analyzeProduct(
    XFile imageFile, {
    String? description,
    String? category,
    String? material,
  }) async {
    try {
      // POST isteği ve Multipart formatı oluşturuluyor
      var request = http.MultipartRequest('POST', Uri.parse(apiUrl));

      // Muhammet'in istediği kritik Header (Başlık) bilgileri
      request.headers.addAll({
        'Accept': 'application/json',
        'ngrok-skip-browser-warning':
            'true', // Ngrok uyarı sayfasını atlamak için şart!
      });

      // Varsa ürün detaylarını ekle
      if (description != null && description.isNotEmpty) {
        request.fields['description'] = description;
      }
      if (category != null && category.isNotEmpty) {
        request.fields['category'] = category;
      }
      if (material != null && material.isNotEmpty) {
        request.fields['material'] = material;
      }

      // Fotoğrafı byte olarak oku
      final bytes = await imageFile.readAsBytes();

      // Fotoğrafı 'file' anahtarıyla (key) ekliyoruz
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          bytes,
          filename: imageFile.name.isNotEmpty ? imageFile.name : 'image.jpeg',
          contentType: MediaType('image', 'jpeg'),
        ),
      );

      // İsteği gönder ve cevabı bekle
      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        // Gelen JSON verisini çöz
        var jsonResponse = json.decode(utf8.decode(response.bodyBytes));

        // Muhammet'in verisi "data" objesinin içinde geliyor
        if (jsonResponse['success'] == true) {
          return jsonResponse['data'];
        } else {
          throw Exception(jsonResponse['message'] ?? "Bir hata oluştu");
        }
      } else {
        throw Exception('Sunucu hatası: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Bağlantı hatası: $e');
    }
  }
}
