import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  // Use 10.0.2.2 for Android emulator to access localhost, or 127.0.0.1 for iOS/Web.
  // Assuming Android emulator as default for testing.
  final String baseUrl = "http://10.0.2.2:8000"; 

  Future<Map<String, dynamic>> analyzeProduct(File imageFile) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/analyze'),
      );
      
      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          imageFile.path,
        ),
      );

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        // Assume backend returns JSON like: {"fiyat": "...", "baslik": "...", "aciklama": "...", "rakip_analizi": "..."}
        return json.decode(response.body);
      } else {
        throw Exception('Failed to analyze product. Status code: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('API Error: $e');
    }
  }
}
