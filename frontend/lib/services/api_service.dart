import 'dart:convert';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import 'package:flutter/foundation.dart';

class ApiService {
  // Eğer web uygulaması localhost'ta çalışıyorsa yerel backend'e bağlansın.
  // Değilse ngrok bağlantısına yönlensin.
  static String get _baseUrl {
    if (kIsWeb && Uri.base.host == 'localhost') {
      return 'http://localhost:8000';
    }
    return 'https://contemptibly-septemviral-apollo.ngrok-free.dev';
  }

  static String get apiUrl => '$_baseUrl/analyze';
  static String get studioAiUrl => '$_baseUrl/studio-ai';

  // Ortak header'lar
  static Map<String, String> get _commonHeaders => {
        'Accept': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      };

  // ---------------------------------------------------------------------------
  // Ürün Analizi (mevcut)
  // ---------------------------------------------------------------------------
  static Future<Map<String, dynamic>> analyzeProduct(
    XFile imageFile, {
    String? description,
    String? category,
    String? material,
    bool isMockMode = false,
  }) async {
    try {
      String finalUrl = apiUrl;
      if (isMockMode) {
        finalUrl += '?mock=true';
      }

      // POST isteği ve Multipart formatı oluşturuluyor
      var request = http.MultipartRequest('POST', Uri.parse(finalUrl));

      // Muhammet'in istediği kritik Header (Başlık) bilgileri
      request.headers.addAll(_commonHeaders);

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

  // ---------------------------------------------------------------------------
  // Studio AI – Profesyonel Stüdyo Görseli Oluştur
  // ---------------------------------------------------------------------------
  /// [imageFile] kullanıcının seçtiği ürün görseli.
  /// [backgroundType] seçilen arka plan şablon ID'si (örn: 'rustic_wood').
  ///
  /// Döndürür: `{ 'studio_image_base64': String, 'mime_type': String }`
  static Future<Map<String, dynamic>> generateStudioImage(
    XFile imageFile, {
    String backgroundType = 'studio_white',
  }) async {
    try {
      final bytes = await imageFile.readAsBytes();

      var request =
          http.MultipartRequest('POST', Uri.parse(studioAiUrl));
      request.headers.addAll(_commonHeaders);

      // Seçilen arka plan temasını form field olarak gönder
      request.fields['background_type'] = backgroundType;

      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          bytes,
          filename:
              imageFile.name.isNotEmpty ? imageFile.name : 'product.jpeg',
          contentType: MediaType('image', 'jpeg'),
        ),
      );

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final jsonResponse = json.decode(utf8.decode(response.bodyBytes));

        if (jsonResponse['success'] == true) {
          return Map<String, dynamic>.from(jsonResponse['data']);
        } else {
          throw Exception(
              jsonResponse['message'] ?? 'Studio AI işlemi başarısız oldu.');
        }
      } else {
        throw Exception('Sunucu hatası: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Studio AI bağlantı hatası: $e');
    }
  }
}
