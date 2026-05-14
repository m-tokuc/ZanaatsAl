import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  // Muhammet'in gönderdiği gerçek Ngrok linki
  static const String apiUrl =
      'https://contemptibly-septemviral-apollo.ngrok-free.dev/analyze';

  static Future<Map<String, dynamic>> analyzeProduct(File imageFile) async {
    try {
      // POST isteği ve Multipart formatı oluşturuluyor
      var request = http.MultipartRequest('POST', Uri.parse(apiUrl));

      // Muhammet'in istediği kritik Header (Başlık) bilgileri
      request.headers.addAll({
        'Accept': 'application/json',
        'ngrok-skip-browser-warning':
            'true', // Ngrok uyarı sayfasını atlamak için şart!
      });

      // Fotoğrafı 'file' anahtarıyla (key) ekliyoruz
      request.files.add(
        await http.MultipartFile.fromPath('file', imageFile.path),
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
