import 'dart:convert';
import 'dart:io';

class ApiService {
  Future<Map<String, dynamic>> analyzeProduct(File imageFile) async {
    // Simulate API call with 5 second delay
    await Future.delayed(Duration(seconds: 5));
    
    // Return mock data as specified
    return {
      "fiyat": "\$45 - \$50",
      "baslik": "Handcrafted Vintage Leather Crossbody Bag",
      "aciklama": "Elevate your style with this 100% genuine handcrafted leather bag. Perfect for daily use and travel. #leatherbag",
      "rakip_analizi": "Rakiplerin fermuarları kalitesiz bulunmuş. Satış yaparken kaliteli dikişlerinizi vurgulayın."
    };
  }
}
